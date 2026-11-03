from utils.driver_wrapper import DriverWrapper
from apps.ewm.locators.arribo_locators import ArriboLocators
from utils.templete_report import add_step
from utils.logger import get_logger

logger = get_logger("ArriboModule")


def registrar_arribo(driver, tu: str, cita: str = None):
    """Ejecuta el proceso de arribo en la transacción /SCWM/TU."""
    wrapper = DriverWrapper(driver)

    try:
        logger.info(f"[*] Iniciando arribo para TU={tu}, Cita={cita}...")
        wrapper.transaction(ArriboLocators.TCODE, description="transacción de Arribo /SCWM/TU")

        if cita and wrapper.exists(ArriboLocators.CITA_INPUT):
            wrapper.send_keys(ArriboLocators.CITA_INPUT, cita, description=f"el campo de cita ({cita})")

        if tu and wrapper.exists(ArriboLocators.TU_INPUT):
            wrapper.send_keys(ArriboLocators.TU_INPUT, tu, description=f"el número de TU ({tu})")

        wrapper.send_vkey(0, description="Enter para validar datos de Arribo")

        # Marcar casilla o ejecutar si aplica
        if wrapper.exists(ArriboLocators.CHECK_BOX):
            try:
                wrapper.click(ArriboLocators.CHECK_BOX, description="casilla de confirmación")
            except Exception:
                pass

        if wrapper.exists(ArriboLocators.EXECUTE_BUTTON):
            wrapper.click(ArriboLocators.EXECUTE_BUTTON, description="botón Ejecutar (F8)")

        status = wrapper.get_status_bar()
        if status["type"] == "E":
            raise AssertionError(f"Error SAP en arribo: {status['text']}")

        add_step(f"Arribo completado exitosamente para TU={tu}", "passed")
        return tu

    except Exception as e:
        msg_error = f"Falló el proceso de Arribo para TU '{tu}': {e}"
        logger.error(f"[-] {msg_error}")
        add_step(msg_error, "failed")
        raise AssertionError(msg_error) from e
