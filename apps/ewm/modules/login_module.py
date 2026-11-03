from utils.driver_wrapper import DriverWrapper
from apps.ewm.locators.login_locators import LoginLocators
from utils.templete_report import add_step
from utils.logger import get_logger

logger = get_logger("LoginModule")


def validar_sesion_activa(driver):
    """Verifica que SAP GUI responda y la ventana principal esté disponible."""
    wrapper = DriverWrapper(driver)
    try:
        wrapper.wait.until("wnd[0]")
        msg = "Sesión SAP GUI validada y activa."
        logger.info(f"[*] {msg}")
        add_step(msg, "passed")
    except Exception as e:
        msg_error = f"No hay una sesión SAP GUI activa: {e}"
        add_step(msg_error, "failed")
        raise AssertionError(msg_error) from e


def ejecutar_transaccion(driver, tcode: str):
    """Accede a una transacción mediante el campo OKCODE (/n...)."""
    wrapper = DriverWrapper(driver)
    try:
        wrapper.transaction(tcode, description=f"transacción {tcode}")
        add_step(f"Transacción {tcode} ejecutada exitosamente", "passed")
    except Exception as e:
        msg_error = f"Error al ejecutar la transacción {tcode}: {e}"
        add_step(msg_error, "failed")
        raise AssertionError(msg_error) from e
