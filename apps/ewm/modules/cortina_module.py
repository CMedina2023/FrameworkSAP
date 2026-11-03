from utils.driver_wrapper import DriverWrapper
from apps.ewm.locators.cortina_locators import CortinaLocators
from utils.templete_report import add_step
from utils.logger import get_logger

logger = get_logger("CortinaModule")


def asignar_cortina(driver, tu: str):
    """Asigna cortina a una TU mediante el menú RFUI (/SCWM/RFUI)."""
    wrapper = DriverWrapper(driver)

    try:
        logger.info(f"[*] Iniciando asignación de cortina para TU={tu}...")
        wrapper.transaction(CortinaLocators.TCODE, description="transacción RFUI")
        wrapper.send_vkey(0, description="confirmar pantalla inicial RFUI")

        # Secuencia de navegación en menús RFUI (6 -> 1 -> 1)
        pasos_menu = [
            ("6", "opción 6 del menú RFUI"),
            ("1", "subopción 1 (Asignación)"),
            ("1", "subopción 1 (Cortina)")
        ]
        for opt, desc in pasos_menu:
            wrapper.send_keys(CortinaLocators.MENU_INPUT, opt, description=desc)
            wrapper.send_vkey(0, description=f"confirmar opción {opt}")

        # Ingresar código de barra de TU
        wrapper.send_keys(CortinaLocators.TU_BARCODE_INPUT, tu, description=f"código de barra TU ({tu})")
        wrapper.send_vkey(0, description="Enter para buscar TU")
        wrapper.send_vkey(8, description="F8 para confirmar cortina")

        # Retornar por menús usando F7
        for _ in range(4):
            wrapper.send_vkey(7, description="F7 (Volver en menú RFUI)")

        # Presionar PB1 si está presente
        if wrapper.exists(CortinaLocators.PB1_BUTTON):
            wrapper.press(CortinaLocators.PB1_BUTTON, description="botón PB1")

        add_step(f"Cortina asignada correctamente a la TU={tu}", "passed")

    except Exception as e:
        msg_error = f"Error durante la asignación de cortina para TU '{tu}': {e}"
        logger.error(f"[-] {msg_error}")
        add_step(msg_error, "failed")
        raise AssertionError(msg_error) from e
