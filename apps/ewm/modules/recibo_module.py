from utils.driver_wrapper import DriverWrapper
from apps.ewm.locators.recibo_locators import ReciboLocators
from utils.templete_report import add_step
from utils.logger import get_logger

logger = get_logger("ReciboModule")


def recibir_asn_chocolate(driver, hus: list, hu_masters: list = None):
    """Procesa el recibo de ASN Chocolate mediante RFUI."""
    wrapper = DriverWrapper(driver)
    hu_masters = hu_masters or [""] * len(hus)

    try:
        logger.info(f"[*] Iniciando Recibo ASN Chocolate para {len(hus)} HUs...")
        wrapper.transaction(ReciboLocators.TCODE, description="transacción RFUI")
        wrapper.send_vkey(0, description="confirmar ingreso a RFUI")

        # Secuencia RFUI: 6 -> 1 -> 3 -> 2
        for opt, desc in [("6", "menú 6"), ("1", "menú 1"), ("3", "menú 3"), ("2", "menú 2")]:
            wrapper.send_keys(ReciboLocators.MENU_INPUT, opt, description=desc)
            wrapper.send_vkey(0, description=f"confirmar opción {opt}")

        for i, hu in enumerate(hus):
            wrapper.send_keys(ReciboLocators.HU_INPUT, str(hu), description=f"HU [{hu}]")
            wrapper.send_vkey(0, description="Enter en HU")

            hu_master_val = wrapper.get_text(ReciboLocators.HU_MASTER_INPUT).strip()
            if not hu_master_val and i < len(hu_masters) and hu_masters[i]:
                wrapper.send_keys(ReciboLocators.HU_MASTER_INPUT, hu_masters[i], description=f"HU Master [{hu_masters[i]}]")
                wrapper.send_vkey(5, description="F5 en HU Master")
                wrapper.send_vkey(0, description="Enter")

            wrapper.send_vkey(1, description="F1 para confirmar")
            wrapper.send_vkey(0, description="Enter")

        for _ in range(5):
            wrapper.send_vkey(7, description="F7 (Volver)")

        add_step(f"Recibo ASN Chocolate completado para {len(hus)} HUs", "passed")

    except Exception as e:
        msg_error = f"Error en Recibo ASN Chocolate: {e}"
        logger.error(f"[-] {msg_error}")
        add_step(msg_error, "failed")
        raise AssertionError(msg_error) from e
