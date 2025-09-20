import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import subprocess
import json
import logging

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_tests_single_execution():

    os.makedirs('reports', exist_ok=True)
    os.makedirs('reports/html-reports', exist_ok=True)

    json_report_path = 'reports/behave-report.json'

    logger.info("🚀 Ejecutando pruebas y generando reporte")

    # Paso 1: Ejecutar behave y generar JSON
    try:
        logger.info("📋 Ejecutando pruebas behave...")
        result = subprocess.run([
            sys.executable, '-m', 'behave',
            'features/sap_login.feature',
            '--format', 'json.pretty',
            '--outfile', json_report_path,
            '--no-capture'
        ], capture_output=True, text=True, timeout=300)

        logger.info(f"✅ Behave finalizado. Código: {result.returncode}")

    except Exception as e:
        logger.error(f"❌ Error ejecutando behave: {e}")
        return 1

    # Paso 2: Generar reporte HTML
    logger.info("📊 Generando reporte HTML...")
    try:
        from src.reporting.html_reporter import HTMLReporter
        reporter = HTMLReporter()
        html_report_path = reporter.generate_html_report(json_report_path)

        if html_report_path:
            logger.info(f"✅ Reporte HTML generado: {html_report_path}")
        else:
            logger.error("❌ Error generando reporte HTML")
            return 1

    except Exception as e:
        logger.error(f"❌ Error generando reporte: {e}")
        return 1

    return result.returncode


if __name__ == "__main__":
    exit_code = run_tests_single_execution()
    sys.exit(exit_code)
