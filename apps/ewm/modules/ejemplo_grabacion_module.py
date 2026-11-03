"""Módulo generado desde grabación SAP GUI: ejemplo_grabacion."""
from utils.driver_wrapper import DriverWrapper
from utils.templete_report import add_step
from apps.ewm.locators.ejemplo_grabacion_locators import EjemploGrabacionLocators


def ejecutar_ejemplo_grabacion(driver, **kwargs):
    """Ejecuta la automatización de la grabación ejemplo_grabacion."""
    wrapper = DriverWrapper(driver)
    add_step("Iniciando grabación ejemplo_grabacion", "passed")

    TU = kwargs.get("TU")
    docs = kwargs.get("docs", [])
    HUs = kwargs.get("HUs", [])

    wrapper.send_keys("wnd[0]/tbar[0]/okcd", "/n/scwm/tu")
    wrapper.send_vkey(0)
    wrapper.send_keys("wnd[0]/usr/ctxt/SCWM/S_TU_SR_NO-LOW", TU)
    wrapper.send_keys("wnd[0]/usr/ctxt/SCWM/S_CITA-LOW", kwargs.get("cita"))
    # session.findById("wnd[0]/usr/ctxt/SCWM/S_TU_SR_NO-LOW").setFocus()
    wrapper.send_keys("wnd[0]/usr/ctxt/SCWM/S_TU_SR_NO-LOW", 5)
    wrapper.send_keys("wnd[0]/usr/chkP_CHECK", True)
    wrapper.click("wnd[0]/tbar[1]/btn[8]")

    add_step("Grabación ejemplo_grabacion completada con éxito", "passed")
