from src.core.sap_login import SAPLogin
import logging

logger = logging.getLogger(__name__)

def execute_transaction(transaction_code, session=None):
    """Ejecuta una transacción SAP"""
    try:
        if session is None:
            sap_login = SAPLogin()
            if sap_login.login():
                session = sap_login.session
            else:
                return False

        logger.info(f"Ejecutando transacción: {transaction_code}")
        session.StartTransaction(transaction_code)
        return True

    except Exception as e:
        logger.error(f"Error ejecutando transacción {transaction_code}: {e}")
        return False

def get_session():
    """Obtiene una sesión activa de SAP"""
    sap_login = SAPLogin()
    if sap_login.login():
        return sap_login.session
    return None
