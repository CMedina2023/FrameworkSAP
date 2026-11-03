from pytest_bdd import scenarios, given, when, then, parsers
from apps.ewm.modules.login_module import validar_sesion_activa
from apps.ewm.modules.arribo_module import registrar_arribo
from apps.ewm.modules.cortina_module import asignar_cortina
from apps.ewm.modules.recibo_module import recibir_asn_chocolate
from utils.csv_reader import resolve_env

scenarios("ewm/features/flujo_chocolate.feature")


@given("que la sesión SAP está abierta y lista para operar")
def verificar_sesion_flujo(driver):
    validar_sesion_activa(driver)


@when(parsers.parse('registro el arribo para la TU "{tu}" y cita "{cita}"'))
def paso_flujo_arribo(driver, flow_context, tu, cita):
    tu_val = resolve_env(tu)
    cita_val = resolve_env(cita)
    flow_context.TU = tu_val
    flow_context.cita = cita_val
    registrar_arribo(driver, tu=tu_val, cita=cita_val)


@when(parsers.parse('asigno la cortina para la unidad de transporte "{tu}"'))
def paso_flujo_cortina(driver, flow_context, tu):
    tu_val = flow_context.TU or resolve_env(tu)
    asignar_cortina(driver, tu=tu_val)


@when(parsers.parse('proceso el recibo de las HUs "{hus}"'))
def paso_flujo_recibo(driver, flow_context, hus):
    lista_hus = [h.strip() for h in hus.split(",") if h.strip()]
    flow_context.HUs = lista_hus
    recibir_asn_chocolate(driver, hus=lista_hus)


@then("el flujo completo de recibo chocolate debe finalizar sin errores")
def paso_validar_fin_flujo(driver, flow_context):
    pass
