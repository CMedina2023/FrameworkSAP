import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.sap_login import SAPLogin
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def main():
    """Script principal de automatización SAP"""
    logger.info("Iniciando automatización SAP...")

    sap_login = SAPLogin()

    try:
        if sap_login.login():
            logger.info("Login exitoso! Sesión lista para operaciones.")

            # Aquí se pueden agregar operaciones específicas
            # Ejemplo:
            # from src.functions.sap_transactions import execute_transaction
            # execute_transaction("ME23N", sap_login.session)

        else:
            logger.error("Falló el login")

    except Exception as e:
        logger.error(f"Error durante la ejecución: {e}")

    finally:
        sap_login.close_connection()
        logger.info("🏁 Automatización SAP finalizada.")

if __name__ == "__main__":
    main()
