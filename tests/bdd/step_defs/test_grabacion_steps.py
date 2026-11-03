"""Steps dinámicos para ejecutar cualquier grabación transformada desde SAP Logon."""
import importlib
from pytest_bdd import scenarios, given, when, then, parsers
from apps.ewm.modules.login_module import validar_sesion_activa

scenarios("ewm/features/ejemplo_grabacion.feature")


@given("que la sesión SAP está abierta y lista para operar")
def verificar_sesion_grabacion(driver):
    validar_sesion_activa(driver)


@when(parsers.parse('ejecuto el módulo de la grabación "{nombre_grabacion}"'))
def paso_ejecutar_grabacion(driver, flow_context, nombre_grabacion):
    module_name = f"apps.ewm.modules.{nombre_grabacion}_module"
    func_name = f"ejecutar_{nombre_grabacion}"

    mod = importlib.import_module(module_name)
    func = getattr(mod, func_name)

    kwargs = {
        "TU": getattr(flow_context, "TU", None),
        "cita": getattr(flow_context, "cita", None),
        "docs": getattr(flow_context, "docs", []),
        "HUs": getattr(flow_context, "HUs", []),
    }
    func(driver, **kwargs)


@then(parsers.parse('el módulo debe finalizar con éxito'))
def paso_fin_grabacion(driver):
    pass
