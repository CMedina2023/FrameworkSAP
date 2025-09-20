import os
import sys
import logging

# DIRECTORIO RAIZ AL PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def before_all(context):
    """Ejecutar antes de todas las pruebas"""
    logging.info("Iniciando ejecución de pruebas BDD")

def before_scenario(context, scenario):
    """Ejecutar antes de cada escenario"""
    logging.info(f"Iniciando escenario: {scenario.name}")
    context.sap_login = None

def after_scenario(context, scenario):
    """Ejecutar después de cada escenario"""
    if hasattr(context, 'sap_login') and context.sap_login:
        context.sap_login.close_connection()
    logging.info(f"Finalizado escenario: {scenario.name}")

def after_all(context):
    """Ejecutar después de todas las pruebas"""
    logging.info("Finalizada ejecución de pruebas BDD")
