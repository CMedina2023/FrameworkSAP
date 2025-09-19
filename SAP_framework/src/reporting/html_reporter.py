import os
import html
import datetime
import json
import logging


logger = logging.getLogger(__name__)


class HTMLReporter:
    def __init__(self, report_dir="reports/html-reports"):
        self.report_dir = report_dir
        os.makedirs(report_dir, exist_ok=True)

    def parse_behave_json(self, json_path):
        """Parsea el reporte JSON de behave para extraer resultados reales"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                behave_data = json.load(f)

            test_cases = []
            total = passed = failed = skipped = 0

            for feature in behave_data:
                if 'elements' not in feature:
                    continue

                for element in feature['elements']:
                    if element['type'] == 'scenario':
                        total += 1
                        scenario_status = self._get_scenario_status(element)

                        if scenario_status == 'passed':
                            passed += 1
                        elif scenario_status == 'failed':
                            failed += 1
                        else:
                            skipped += 1

                        test_cases.append({
                            'name': element.get('name', 'Sin nombre'),
                            'status': scenario_status.upper(),
                            'duration': self._calculate_duration(element),
                            'description': feature.get('name', 'Sin descripción'),
                            'error': self._get_error_message(element)
                        })

            return {
                'total': total,
                'passed': passed,
                'failed': failed,
                'skipped': skipped,
                'test_cases': test_cases
            }

        except Exception as e:
            logger.error(f"Error parsing JSON report: {e}")
            return {
                'total': 1,
                'passed': 0,
                'failed': 1,
                'skipped': 0,
                'test_cases': [{
                    'name': 'Error parsing JSON',
                    'status': 'FAILED',
                    'duration': 0,
                    'description': 'Error al procesar reporte JSON',
                    'error': str(e)
                }]
            }

    def _get_scenario_status(self, scenario):
        if 'steps' not in scenario:
            return 'skipped'

        for step in scenario['steps']:
            if 'result' in step and step['result']['status'] == 'failed':
                return 'failed'
            if 'result' in step and step['result']['status'] == 'skipped':
                return 'skipped'
        return 'passed'

    def _calculate_duration(self, scenario):
        total_duration = 0
        if 'steps' not in scenario:
            return total_duration

        for step in scenario['steps']:
            if 'result' in step and 'duration' in step['result']:
                duration_ns = step['result']['duration']
                total_duration += duration_ns / 1000000000
        return round(total_duration, 2)

    def _get_error_message(self, scenario):
        if 'steps' not in scenario:
            return ""

        for step in scenario['steps']:
            if 'result' in step and step['result']['status'] == 'failed':
                error_message = step['result'].get('error_message', 'Error desconocido')
                if len(error_message) > 500:
                    return error_message[:500] + "..."
                return error_message
        return ""

    def generate_html_report(self, json_report_path):
        """Genera reporte HTML a partir del JSON de behave"""
        if not os.path.exists(json_report_path):
            logger.error(f"Archivo JSON no encontrado: {json_report_path}")
            return None

        results = self.parse_behave_json(json_report_path)

        report_path = os.path.join(self.report_dir,
                                   f"sap_test_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html")

        html_content = self._generate_html_content(results)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"Reporte HTML generado: {report_path}")
        return report_path

    def _generate_html_content(self, results):
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Reporte de Pruebas SAP - Ejecución Real</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
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
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat-box {{ flex: 1; text-align: center; padding: 15px; border-radius: 10px; color: white; }}
        .stat-total {{ background: #0078D7; }}
        .stat-passed {{ background: #28a745; }}
        .stat-failed {{ background: #dc3545; }}
        .stat-skipped {{ background: #ffc107; }}
        .error {{ background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Reporte de Pruebas SAP Automation</h1>
        <p>📅 Generado: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="summary">
        <h2>📊 Resumen de Ejecución</h2>
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
        </div>
    </div>

    <div class="test-cases">
        <h2>📋 Detalle de Casos de Prueba</h2>
        {self._generate_test_cases_html(results['test_cases'])}
    </div>
</body>
</html>"""

    def _generate_test_cases_html(self, test_cases):
        if not test_cases:
            return "<p>No hay casos de prueba para mostrar</p>"

        cases_html = ""
        for case in test_cases:
            status_class = case['status'].lower()
            cases_html += f"""
            <div class="test-case {status_class}">
                <h3>{html.escape(case['name'])}</h3>
                <span class="status status-{case['status']}">{case['status']}</span>
                <p><strong>⏱️ Duración:</strong> {case['duration']} segundos</p>
                <p><strong>📝 Descripción:</strong> {html.escape(case['description'])}</p>
                {f'<div class="error"><strong>🚨 Error:</strong><br><code>{html.escape(case["error"])}</code></div>' if case['error'] else ''}
            </div>
            """
        return cases_html



