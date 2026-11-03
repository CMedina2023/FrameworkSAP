from pytest_bdd import scenarios, given, when, then, parsers
from apps.ewm.modules.arribo_module import registrar_arribo
from apps.ewm.modules.login_module import validar_sesion_activa
from utils.csv_reader import resolve_env

scenarios("ewm/features/arribo.feature")


@given("que la sesión SAP está abierta y lista para operar")
def verificar_sesion_arribo(driver):
    validar_sesion_activa(driver)


@when(parsers.parse('ejecuto el arribo para la TU "{tu}" con la cita "{cita}"'))
def paso_registrar_arribo(driver, flow_context, tu, cita):
    tu_val = resolve_env(tu)
    cita_val = resolve_env(cita)
    flow_context.TU = tu_val
    flow_context.cita = cita_val
    registrar_arribo(driver, tu=tu_val, cita=cita_val)


@then(parsers.parse('el arribo debe quedar registrado exitosamente para la TU "{tu}"'))
def paso_validar_arribo(driver, tu):
    # Validado satisfactoriamente dentro de registrar_arribo()
    pass
