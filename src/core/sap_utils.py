import time
import logging

logger = logging.getLogger(__name__)

# Utilidad de tiempo
def wait(seconds=5):
    logger.info(f"Esperando {seconds} segundos...")
    time.sleep(seconds)

# Utilidad para detectar modales
def close_sap_popups(session):
    """Cierra popups/modales comunes de SAP"""
    try:
        popup_windows = ["wnd[1]", "wnd[2]", "wnd[3]"]
        close_buttons = [
            "/usr/btnSPOP-OPTION1", "/tbar[0]/btn[0]",
            "/usr/btnBUTTON_1", "/usr/btnEND"
        ]

        for window in popup_windows:
            try:
                if session.findById(window).exists:
                    for button in close_buttons:
                        try:
                            session.findById(window + button).press()
                            logger.info(f"Popup cerrado: {window}{button}")
                            break
                        except:
                            continue
            except:
                continue

    except Exception as e:
        logger.error(f"Error cerrando popups: {e}")

