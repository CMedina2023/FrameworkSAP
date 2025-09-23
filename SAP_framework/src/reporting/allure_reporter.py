import os
import allure
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def attach_screenshot(session, name="screenshot"):
    """Toma screenshot de SAP y lo adjunta al reporte Allure"""
    try:
        screenshot_path = f"reports/screenshots/{name}.png"
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)

        # En una implementación real, aquí iría el código para tomar screenshot de SAP
        # session.findById("wnd[0]").hardCopy(screenshot_path)

        allure.attach.file(screenshot_path, name=name, attachment_type=allure.attachment_type.PNG)
        logger.info(f"Screenshot adjuntado: {name}")

    except Exception as e:
        logger.error(f"Error tomando screenshot: {e}")

def attach_text(text, name="log"):
    """Adjunta texto al reporte Allure"""
    allure.attach(text, name=name, attachment_type=allure.attachment_type.TEXT)
