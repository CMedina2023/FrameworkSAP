from pytest_bdd import scenarios, given, then
from apps.ewm.modules.login_module import validar_sesion_activa

scenarios("ewm/features/login.feature")


@given("que la sesión SAP está abierta y lista para operar")
def verificar_sesion(driver):
    validar_sesion_activa(driver)


@then("el sistema debe responder mostrando la pantalla principal de SAP")
def validar_pantalla_principal(driver):
    # La aserción fue verificada en validar_sesion_activa
    pass
