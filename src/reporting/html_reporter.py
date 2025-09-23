import os
import html
import datetime
import json
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class HTMLReporter:
    def __init__(self, report_dir=None):
        if report_dir is None:
            self.report_dir = "reports/html-reports"
        else:
            self.report_dir = report_dir

        os.makedirs(self.report_dir, exist_ok=True)

        self.evidence_dir = Path(self.report_dir) / "evidence"
        self.evidence_dir.mkdir(exist_ok=True)

    def parse_behave_json(self, json_path):
        """Parsea el reporte JSON de behave con tiempos REALES y detalles"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                behave_data = json.load(f)

            test_cases = []
            total_duration = 0

            for feature in behave_data:
                if 'elements' not in feature:
                    continue

                for element in feature['elements']:
                    if element['type'] == 'scenario':
                        # ✅ NUEVO: Análisis detallado con tiempos reales
                        scenario_analysis = self._analyze_scenario_detailed(element)
                        test_cases.append(scenario_analysis)
                        total_duration += scenario_analysis['duration']

            passed = sum(1 for case in test_cases if case['status'] == 'passed')
            failed = sum(1 for case in test_cases if case['status'] == 'failed')
            skipped = sum(1 for case in test_cases if case['status'] == 'skipped')
            total = len(test_cases)

            return {
                'total': total,
                'passed': passed,
                'failed': failed,
                'skipped': skipped,
                'test_cases': test_cases,
                'total_duration': round(total_duration, 2),
                'average_duration': round(total_duration / total, 2) if total > 0 else 0,
                'generation_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'execution_environment': self._get_environment_info()
            }

        except Exception as e:
            logger.error(f"Error parsing JSON report: {e}")
            return self._create_error_report(e)

    def _analyze_scenario_detailed(self, scenario):
        """Analiza escenario con detalles completos y tiempos reales"""
        status = 'passed'
        total_duration = 0
        steps_details = []
        start_time = None
        end_time = None

        if 'steps' not in scenario:
            return self._create_scenario_structure(scenario, status, total_duration, steps_details, start_time,
                                                   end_time)

        for step in scenario['steps']:
            step_result = step.get('result', {})
            step_status = step_result.get('status', 'skipped')
            step_duration = step_result.get('duration', 0) / 1000000000  # ns to seconds

            if start_time is None and 'start_time' in step_result:
                start_time = step_result['start_time']
            if 'end_time' in step_result:
                end_time = step_result['end_time']

            # Determinar status del escenario
            if step_status == 'failed':
                status = 'failed'
            elif status == 'passed' and step_status == 'skipped':
                status = 'skipped'

            total_duration += step_duration

            step_detail = {
                'name': step.get('name', ''),
                'keyword': step.get('keyword', ''),
                'status': step_status,
                'duration': round(step_duration, 3),
                'error': step_result.get('error_message', ''),
                'traceback': step_result.get('traceback', ''),
                'start_time': step_result.get('start_time', ''),
                'end_time': step_result.get('end_time', ''),
                'evidence': self._generate_step_evidence(step, step_status)
            }
            steps_details.append(step_detail)

        return self._create_scenario_structure(scenario, status, round(total_duration, 3), steps_details, start_time,
                                               end_time)

    def _create_scenario_structure(self, scenario, status, duration, steps_details, start_time, end_time):
        """Crea estructura completa del escenario"""
        return {
            'name': scenario.get('name', 'Sin nombre'),
            'description': scenario.get('description', ''),
            'tags': [tag['name'] for tag in scenario.get('tags', [])],
            'status': status,
            'duration': duration,
            'steps': steps_details,
            'start_time': start_time,
            'end_time': end_time,
            'error': self._get_detailed_error(scenario),
            'evidence_paths': self._collect_evidence_paths(steps_details)
        }

    def _generate_step_evidence(self, step, step_status):
        """Genera evidencias para cada paso (screenshots, logs, etc.)"""
        evidence = {}

        if step_status == 'failed':
            evidence['screenshot'] = self._capture_screenshot(step.get('name', 'unknown'))

        evidence['logs'] = self._capture_step_logs(step)

        evidence['data'] = self._capture_step_data(step)

        return evidence

    def _capture_screenshot(self, step_name):
        """Captura screenshot (placeholder para implementación futura)"""
        try:
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_info = {
                'planned_path': f"{self.evidence_dir}/screenshot_{step_name}_{timestamp}.png",
                'status': 'not_implemented',
                'message': 'Screenshot functionality ready for SAP GUI integration'
            }
            return screenshot_info
        except Exception as e:
            return {'error': f'Screenshot capture failed: {str(e)}'}

    def _capture_step_logs(self, step):
        """Captura logs relacionados con el paso"""
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        return {
            'timestamp': timestamp,
            'step_name': step.get('name', ''),
            'log_entries': [
                f"{timestamp} - Executing step: {step.get('name', '')}",
                f"{timestamp} - Step status: {step.get('result', {}).get('status', 'unknown')}"
            ]
        }

    def _capture_step_data(self, step):
        """Captura datos de ejecución del paso"""
        return {
            'execution_time': datetime.datetime.now().isoformat(),
            'step_duration': step.get('result', {}).get('duration', 0) / 1000000000,
            'parameters': self._extract_step_parameters(step)
        }

    def _extract_step_parameters(self, step):
        """Extrae parámetros del paso Gherkin"""
        step_name = step.get('name', '')
        parameters = {}

        # Extraer valores entre comillas del paso
        import re
        quoted_values = re.findall(r'"([^"]*)"', step_name)
        if quoted_values:
            parameters['quoted_parameters'] = quoted_values

        return parameters

    def _collect_evidence_paths(self, steps_details):
        """Colecta todas las rutas de evidencias del escenario"""
        evidence_paths = []
        for step in steps_details:
            if 'evidence' in step and 'screenshot' in step['evidence']:
                evidence_paths.append(step['evidence']['screenshot'].get('planned_path', ''))
        return [path for path in evidence_paths if path]

    def _get_detailed_error(self, scenario):
        """Obtiene mensaje de error detallado con traceback"""
        if 'steps' not in scenario:
            return ""

        for step in scenario['steps']:
            if 'result' in step and step['result']['status'] == 'failed':
                error_info = {
                    'message': step['result'].get('error_message', 'Error desconocido'),
                    'traceback': step['result'].get('traceback', ''),
                    'step_name': step.get('name', ''),
                    'step_keyword': step.get('keyword', '')
                }
                return error_info
        return ""

    def _get_environment_info(self):
        """Obtiene información del entorno de ejecución"""
        import platform
        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'timestamp': datetime.datetime.now().isoformat(),
            'working_directory': os.getcwd()
        }

    def generate_html_report(self, json_report_path):
        """Genera reporte HTML MEJORADO con todos los detalles"""
        if not os.path.exists(json_report_path):
            logger.error(f"Archivo JSON no encontrado: {json_report_path}")
            return None

        results = self.parse_behave_json(json_report_path)

        report_path = os.path.join(self.report_dir,
                                   f"sap_test_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html")

        html_content = self._generate_enhanced_html_content(results)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"📊 Reporte HTML MEJORADO generado: {report_path}")

        self._generate_analysis_json(results, report_path.replace('.html', '_analysis.json'))

        return report_path

    def _generate_enhanced_html_content(self, results):
        """Genera contenido HTML con todos los detalles y evidencias"""
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Reporte Detallado SAP Automation</title>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f8f9fa; }}
        .header {{ background: linear-gradient(135deg, #0078D7, #005A9E); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .summary {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .test-case {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 15px; }}
        .passed {{ border-left: 5px solid #28a745; }}
        .failed {{ border-left: 5px solid #dc3545; }}
        .skipped {{ border-left: 5px solid #ffc107; }}
        .status {{ font-weight: bold; float: right; padding: 5px 15px; border-radius: 20px; color: white; }}
        .status-PASSED {{ background: #28a745; }}
        .status-FAILED {{ background: #dc3545; }}
        .status-SKIPPED {{ background: #ffc107; }}
        .stats {{ display: flex; gap: 15px; margin: 20px 0; flex-wrap: wrap; }}
        .stat-box {{ flex: 1; min-width: 120px; text-align: center; padding: 15px; border-radius: 10px; color: white; }}
        .stat-total {{ background: #0078D7; }}
        .stat-passed {{ background: #28a745; }}
        .stat-failed {{ background: #dc3545; }}
        .stat-skipped {{ background: #ffc107; }}
        .stat-duration {{ background: #6f42c1; }}
        .error {{ background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace; white-space: pre-wrap; }}
        .steps {{ margin-top: 15px; }}
        .step {{ padding: 12px; margin: 8px 0; border-left: 4px solid #ddd; border-radius: 5px; }}
        .step-passed {{ border-left-color: #28a745; background: #f8fff9; }}
        .step-failed {{ border-left-color: #dc3545; background: #fff5f5; }}
        .step-skipped {{ border-left-color: #ffc107; background: #fffef0; }}
        .step-name {{ font-weight: bold; font-size: 1.1em; }}
        .step-duration {{ float: right; color: #666; font-weight: bold; }}
        .step-keyword {{ color: #888; font-style: italic; }}
        .step-details {{ margin-top: 8px; font-size: 0.9em; }}
        .evidence {{ background: #e9ecef; padding: 10px; margin: 5px 0; border-radius: 5px; }}
        .collapsible {{ cursor: pointer; padding: 10px; background: #e9ecef; border: none; border-radius: 5px; width: 100%; text-align: left; font-weight: bold; }}
        .content {{ max-height: 0; overflow: hidden; transition: max-height 0.3s ease-out; }}
        .timestamp {{ color: #666; font-size: 0.9em; margin-top: 5px; }}
        .tag {{ display: inline-block; background: #e9ecef; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin-right: 5px; }}
        .environment {{ background: #e7f1ff; padding: 15px; border-radius: 5px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Reporte Detallado SAP Automation</h1>
        <p>📅 Generado: {results['generation_time']}</p>
        <p>⏱️ Duración total: <strong>{results['total_duration']} segundos</strong></p>
    </div>

    <div class="summary">
        <h2>📊 Métricas de Ejecución</h2>
        <div class="stats">
            <div class="stat-box stat-total">
                <h3>Total</h3>
                <p style="font-size: 24px; margin: 5px 0;">{results['total']}</p>
            </div>
            <div class="stat-box stat-passed">
                <h3>✅ Aprobadas</h3>
                <p style="font-size: 24px; margin: 5px 0;">{results['passed']}</p>
            </div>
            <div class="stat-box stat-failed">
                <h3>❌ Falladas</h3>
                <p style="font-size: 24px; margin: 5px 0;">{results['failed']}</p>
            </div>
            <div class="stat-box stat-skipped">
                <h3>⏸️ Saltadas</h3>
                <p style="font-size: 24px; margin: 5px 0;">{results['skipped']}</p>
            </div>
            <div class="stat-box stat-duration">
                <h3>⏱️ Promedio</h3>
                <p style="font-size: 24px; margin: 5px 0;">{results['average_duration']}s</p>
            </div>
        </div>
    </div>

    <div class="environment">
        <h3>🖥️ Información del Entorno</h3>
        <p><strong>Plataforma:</strong> {results['execution_environment']['platform']}</p>
        <p><strong>Python:</strong> {results['execution_environment']['python_version']}</p>
        <p><strong>Directorio:</strong> {results['execution_environment']['working_directory']}</p>
    </div>

    <div class="test-cases">
        <h2>📋 Detalle de Ejecución - Paso a Paso</h2>
        {self._generate_detailed_test_cases_html(results['test_cases'])}
    </div>

    <script>
        function toggleSteps(button) {{
            var content = button.nextElementSibling;
            if (content.style.maxHeight) {{
                content.style.maxHeight = null;
                button.textContent = "📂 Mostrar Detalles Completos";
            }} else {{
                content.style.maxHeight = content.scrollHeight + "px";
                button.textContent = "📂 Ocultar Detalles";
            }}
        }}

        function toggleEvidence(button) {{
            var content = button.nextElementSibling;
            if (content.style.display === 'none' || content.style.display === '') {{
                content.style.display = 'block';
                button.textContent = '🔼 Ocultar Evidencias';
            }} else {{
                content.style.display = 'none';
                button.textContent = '🔽 Mostrar Evidencias';
            }}
        }}
    </script>
</body>
</html>"""

    def _generate_detailed_test_cases_html(self, test_cases):
        """Genera HTML con detalles completos de cada caso de prueba"""
        if not test_cases:
            return "<p>No hay casos de prueba para mostrar</p>"

        cases_html = ""
        for i, case in enumerate(test_cases):
            status_class = case['status']

            cases_html += f"""
            <div class="test-case {status_class}">
                <h3>🎯 {html.escape(case['name'])}</h3>
                <span class="status status-{case['status'].upper()}">{case['status'].upper()}</span>

                <div class="timestamp">
                    <strong>🕒 Duración REAL:</strong> {case['duration']} segundos
                    {f"| Inicio: {case['start_time']}" if case['start_time'] else ""}
                    {f"| Fin: {case['end_time']}" if case['end_time'] else ""}
                </div>

                {''.join(f'<span class="tag">#{tag}</span>' for tag in case['tags'])}

                <button class="collapsible" onclick="toggleSteps(this)">📂 Mostrar Detalles de Ejecución</button>
                <div class="content">
                    <div class="steps">
                        <h4>🔍 Pasos Ejecutados ({len(case['steps'])} pasos):</h4>
                        {self._generate_steps_detailed_html(case['steps'])}
                    </div>

                    {self._generate_evidence_html(case)}
                </div>

                {self._generate_error_html(case)}
            </div>
            """
        return cases_html

    def _generate_steps_detailed_html(self, steps):
        """Genera HTML detallado para cada paso"""
        if not steps:
            return "<p>No hay información de pasos disponibles</p>"

        steps_html = ""
        for j, step in enumerate(steps):
            step_class = f"step step-{step['status']}"
            status_icon = "✅" if step['status'] == 'passed' else "❌" if step['status'] == 'failed' else "⏸️"

            steps_html += f"""
            <div class="{step_class}">
                <div class="step-name">{status_icon} {html.escape(step['name'])}</div>
                <div class="step-duration">{step['duration']}s</div>
                <div class="step-keyword">{step['keyword']}</div>

                <div class="step-details">
                    <strong>Estado:</strong> {step['status'].upper()} | 
                    <strong>Duración:</strong> {step['duration']} segundos
                    {f" | <strong>Inicio:</strong> {step['start_time']}" if step['start_time'] else ""}
                </div>

                {f'<div class="error"><strong>Error:</strong><br><code>{html.escape(step["error"])}</code></div>' if step['error'] else ''}
            </div>
            """
        return steps_html

    def _generate_evidence_html(self, case):
        """Genera HTML para las evidencias del caso"""
        evidence_html = ""
        has_evidence = any(step.get('evidence') for step in case['steps'])

        if has_evidence:
            evidence_html += '<button class="collapsible" onclick="toggleEvidence(this)">🔽 Mostrar Evidencias</button>'
            evidence_html += '<div class="content" style="display: none;">'
            evidence_html += '<h4>📎 Evidencias Recopiladas:</h4>'

            for j, step in enumerate(case['steps']):
                if step.get('evidence'):
                    evidence_html += f'<div class="evidence">'
                    evidence_html += f'<strong>Paso {j + 1}:</strong> {html.escape(step["name"])}<br>'

                    if step['evidence'].get('screenshot'):
                        screenshot_info = step['evidence']['screenshot']
                        if screenshot_info.get('status') == 'not_implemented':
                            evidence_html += f'📷 <em>{screenshot_info["message"]}</em><br>'

                    if step['evidence'].get('logs'):
                        evidence_html += f'📝 Logs: {len(step["evidence"]["logs"]["log_entries"])} entradas<br>'

                    evidence_html += '</div>'

            evidence_html += '</div>'

        return evidence_html

    def _generate_error_html(self, case):
        """Genera HTML para errores"""
        if case['status'] != 'failed' or not case['error']:
            return ""

        error = case['error']
        error_html = f"""
        <div class="error">
            <strong>🚨 Error en ejecución:</strong><br>
            <strong>Mensaje:</strong> {html.escape(error.get('message', 'Sin mensaje'))}<br>
            {f"<strong>Paso:</strong> {html.escape(error.get('step_name', ''))} ({html.escape(error.get('step_keyword', ''))})<br>" if error.get('step_name') else ""}
            {f"<strong>Traceback:</strong><br><code>{html.escape(error.get('traceback', ''))}</code>" if error.get('traceback') else ""}
        </div>
        """
        return error_html

    def _generate_analysis_json(self, results, json_path):
        """Genera archivo JSON adicional para análisis"""
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"📈 Archivo de análisis generado: {json_path}")
        except Exception as e:
            logger.error(f"Error generando archivo de análisis: {e}")

    def _create_error_report(self, error):
        """Crea reporte de error cuando falla el parsing"""
        return {
            'total': 1,
            'passed': 0,
            'failed': 1,
            'skipped': 0,
            'test_cases': [{
                'name': 'Error generando reporte',
                'status': 'failed',
                'duration': 0,
                'steps': [],
                'error': {'message': str(error)},
                'start_time': 'N/A',
                'end_time': 'N/A',
                'tags': ['error']
            }],
            'total_duration': 0,
            'average_duration': 0,
            'generation_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'execution_environment': self._get_environment_info()
        }

    # NEW METHOD ADDED HERE
    def generate_consolidated_report(self, consolidated_data):
        """Genera reporte HTML consolidado para múltiples módulos"""
        try:
            # Calcular métricas consolidadas basadas en los test_cases
            test_cases = consolidated_data.get('test_cases', [])
            total = len(test_cases)
            passed = sum(1 for case in test_cases if case['status'] == 'passed')
            failed = sum(1 for case in test_cases if case['status'] == 'failed')
            skipped = sum(1 for case in test_cases if case['status'] == 'skipped')
            total_duration = sum(case['duration'] for case in test_cases)
            average_duration = round(total_duration / total, 2) if total > 0 else 0

            results = {
                'total': total,
                'passed': passed,
                'failed': failed,
                'skipped': skipped,
                'total_duration': round(total_duration, 2),
                'average_duration': average_duration,
                'generation_time': consolidated_data.get('generation_time', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                'execution_environment': self._get_environment_info(),
                'test_cases': test_cases,  # Usar los test_cases consolidados
                'total_modules': consolidated_data.get('total_modules', 0),
                'successful_modules': consolidated_data.get('successful_modules', 0),
                'failed_modules': consolidated_data.get('failed_modules', 0),
                'success_rate': consolidated_data.get('success_rate', 0)
            }

            # Generar HTML usando la misma lógica, pero con datos consolidados
            report_path = os.path.join(self.report_dir,
                                       f"sap_consolidated_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
            html_content = self._generate_consolidated_html_content(results)

            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            logger.info(f"📊 Reporte HTML CONSOLIDADO generado: {report_path}")

            # Generar JSON de análisis opcional
            self._generate_analysis_json(results, report_path.replace('.html', '_analysis.json'))

            return report_path
        except Exception as e:
            logger.error(f"Error generando reporte consolidado: {e}")
            return None

    def _generate_consolidated_html_content(self, results):
        """Genera contenido HTML consolidado con resumen de módulos"""
        # Similar a _generate_enhanced_html_content, pero con adiciones para módulos
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Reporte Consolidado SAP Automation</title>
    <meta charset="UTF-8">
    <style>
        /* (Mantener el mismo estilo que en _generate_enhanced_html_content) */
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f8f9fa; }}
        .header {{ background: linear-gradient(135deg, #0078D7, #005A9E); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .summary {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .test-case {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 15px; }}
        .passed {{ border-left: 5px solid #28a745; }}
        .failed {{ border-left: 5px solid #dc3545; }}
        .skipped {{ border-left: 5px solid #ffc107; }}
        .status {{ font-weight: bold; float: right; padding: 5px 15px; border-radius: 20px; color: white; }}
        .status-PASSED {{ background: #28a745; }}
        .status-FAILED {{ background: #dc3545; }}
        .status-SKIPPED {{ background: #ffc107; }}
        .stats {{ display: flex; gap: 15px; margin: 20px 0; flex-wrap: wrap; }}
        .stat-box {{ flex: 1; min-width: 120px; text-align: center; padding: 15px; border-radius: 10px; color: white; }}
        .stat-total {{ background: #0078D7; }}
        .stat-passed {{ background: #28a745; }}
        .stat-failed {{ background: #dc3545; }}
        .stat-skipped {{ background: #ffc107; }}
        .stat-duration {{ background: #6f42c1; }}
        .error {{ background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace; white-space: pre-wrap; }}
        .steps {{ margin-top: 15px; }}
        .step {{ padding: 12px; margin: 8px 0; border-left: 4px solid #ddd; border-radius: 5px; }}
        .step-passed {{ border-left-color: #28a745; background: #f8fff9; }}
        .step-failed {{ border-left-color: #dc3545; background: #fff5f5; }}
        .step-skipped {{ border-left-color: #ffc107; background: #fffef0; }}
        .step-name {{ font-weight: bold; font-size: 1.1em; }}
        .step-duration {{ float: right; color: #666; font-weight: bold; }}
        .step-keyword {{ color: #888; font-style: italic; }}
        .step-details {{ margin-top: 8px; font-size: 0.9em; }}
        .evidence {{ background: #e9ecef; padding: 10px; margin: 5px 0; border-radius: 5px; }}
        .collapsible {{ cursor: pointer; padding: 10px; background: #e9ecef; border: none; border-radius: 5px; width: 100%; text-align: left; font-weight: bold; }}
        .content {{ max-height: 0; overflow: hidden; transition: max-height 0.3s ease-out; }}
        .timestamp {{ color: #666; font-size: 0.9em; margin-top: 5px; }}
        .tag {{ display: inline-block; background: #e9ecef; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin-right: 5px; }}
        .environment {{ background: #e7f1ff; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        .module-summary {{ background: #f0f4f8; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Reporte Consolidado SAP Automation</h1>
        <p>📅 Generado: {results['generation_time']}</p>
        <p>⏱️ Duración total: <strong>{results['total_duration']} segundos</strong></p>
    </div>

    <div class="summary">
        <h2>📊 Métricas Consolidadas</h2>
        <div class="stats">
            <div class="stat-box stat-total">
                <h3>Total Escenarios</h3>
                <p style="font-size: 24px; margin: 5px 0;">{results['total']}</p>
            </div>
            <div class="stat-box stat-passed">
                <h3>✅ Aprobadas</h3>
                <p style="font-size: 24px; margin: 5px 0;">{results['passed']}</p>
            </div>
            <div class="stat-box stat-failed">
                <h3>❌ Falladas</h3>
                <p style="font-size: 24px; margin: 5px 0;">{results['failed']}</p>
            </div>
            <div class="stat-box stat-skipped">
                <h3>⏸️ Saltadas</h3>
                <p style="font-size: 24px; margin: 5px 0;">{results['skipped']}</p>
            </div>
            <div class="stat-box stat-duration">
                <h3>⏱️ Promedio</h3>
                <p style="font-size: 24px; margin: 5px 0;">{results['average_duration']}s</p>
            </div>
        </div>
        <div class="module-summary">
            <h3>📦 Resumen de Módulos</h3>
            <p><strong>Total Módulos:</strong> {results['total_modules']}</p>
            <p><strong>Éxitos:</strong> {results['successful_modules']}</p>
            <p><strong>Fallos:</strong> {results['failed_modules']}</p>
            <p><strong>Tasa de Éxito:</strong> {results['success_rate']:.1f}%</p>
        </div>
    </div>

    <div class="environment">
        <h3>🖥️ Información del Entorno</h3>
        <p><strong>Plataforma:</strong> {results['execution_environment']['platform']}</p>
        <p><strong>Python:</strong> {results['execution_environment']['python_version']}</p>
        <p><strong>Directorio:</strong> {results['execution_environment']['working_directory']}</p>
    </div>

    <div class="test-cases">
        <h2>📋 Detalle de Ejecución - Paso a Paso (Todos los Módulos)</h2>
        {self._generate_detailed_test_cases_html(results['test_cases'])}
    </div>

    <script>
        function toggleSteps(button) {{
            var content = button.nextElementSibling;
            if (content.style.maxHeight) {{
                content.style.maxHeight = null;
                button.textContent = "📂 Mostrar Detalles Completos";
            }} else {{
                content.style.maxHeight = content.scrollHeight + "px";
                button.textContent = "📂 Ocultar Detalles";
            }}
        }}

        function toggleEvidence(button) {{
            var content = button.nextElementSibling;
            if (content.style.display === 'none' || content.style.display === '') {{
                content.style.display = 'block';
                button.textContent = '🔼 Ocultar Evidencias';
            }} else {{
                content.style.display = 'none';
                button.textContent = '🔽 Mostrar Evidencias';
            }}
        }}
    </script>
</body>
</html>"""

