import os
import sys
from pathlib import Path
from src.core.sap_login import SAPLogin
from src.config.config import Credentials

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from behave import given, when, then
import logging

logger = logging.getLogger(__name__)


@given('que tengo las credenciales válidas')
def step_valid_credentials(context):
    try:
        from src.core.sap_login import SAPLogin
        from src.config.config import Credentials

        context.sap_login = SAPLogin()
        assert Credentials.USERNAME != "", "Username no configurado"
        assert Credentials.PASSWORD != "", "Password no configurado"
        logger.info("Credenciales válidas configuradas")
    except ImportError as e:
        logger.error(f"Error de importación: {e}")
        raise


@given('que tengo credenciales inválidas')
def step_invalid_credentials(context):
    from src.core.sap_login import SAPLogin
    from src.config.config import Credentials

    context.sap_login = SAPLogin()
    context.original_username = Credentials.USERNAME
    Credentials.USERNAME = "usuario_invalido"


@when('inicio sesión en SAP')
def step_login_sap(context):
    context.login_result = context.sap_login.login()


@when('intento iniciar sesión en SAP')
def step_try_login_sap(context):
    context.login_result = context.sap_login.login()


@then('debo tener acceso al sistema')
def step_verify_access(context):
    assert context.login_result == True, "Login no exitoso"


@then('debo recibir un mensaje de error')
def step_verify_error(context):
    assert context.login_result == False, "Se esperaba error de login"
    if hasattr(context, 'original_username'):
        from src.config.config import Credentials
        Credentials.USERNAME = context.original_username

