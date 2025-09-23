import os
import sys
import logging
import time
import datetime
import traceback
from pathlib import Path

try:
    import win32com.client
except Exception:
    win32com = None

# Ajustar PYTHONPATH si es necesario
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Config logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def before_all(context):
    logging.info("Iniciando ejecución de pruebas BDD")
    context.evidence_dir = Path("reports") / "evidence"
    context.evidence_dir.mkdir(parents=True, exist_ok=True)

def after_all(context):
    logging.info("Finalizada ejecución de pruebas BDD")

def before_scenario(context, scenario):
    logging.info(f"Iniciando escenario: {scenario.name}")
    context.sap_login = None

def after_scenario(context, scenario):
    if hasattr(context, 'sap_login') and context.sap_login:
        context.sap_login.close_connection()
    logging.info(f"Finalizado escenario: {scenario.name}")

# -----------------------------
# TIMINGS + SCREENSHOTS SAP GUI
# -----------------------------
def _get_sap_session():
    if win32com is None:
        return None
    try:
        SapGuiAuto = win32com.client.GetObject("SAPGUI")
        application = SapGuiAuto.GetScriptingEngine
        connection = application.Children(0)
        session = connection.Children(0)
        return session
    except Exception as e:
        logging.warning(f"No se pudo obtener sesión SAP: {e}")
        return None

def before_step(context, step):
    step._env_start_time = time.time()

def after_step(context, step):
    step._env_end_time = time.time()
    duration_seconds = step._env_end_time - getattr(step, "_env_start_time", step._env_end_time)

    # Guardar duración en ns (para JSON de behave) y segundos
    try:
        step.result.duration = int(duration_seconds * 1e9)  # ns
        step.result.duration_seconds = duration_seconds
    except Exception:
        pass

    # Screenshot si falla
    if step.status == "failed":
        safe_name = "".join(c if (c.isalnum() or c in (' ', '_', '-')) else '_' for c in step.name)[:80].strip()
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        bmp_path = context.evidence_dir / f"{safe_name}_{ts}.bmp"

        try:
            session = _get_sap_session()
            if session:
                session.findById("wnd[0]").hardCopy(str(bmp_path))
                logging.info(f"📷 Screenshot capturado: {bmp_path}")
                step.result.screenshot_path = str(bmp_path)
            else:
                logging.warning("No hay sesión SAP activa, no se capturó screenshot")
        except Exception as e:
            logging.error(f"Error capturando screenshot SAP: {e}")
            step.result.screenshot_path = f"Error: {e}"

    # Si hay excepción, guardar trace
    if step.status == "failed":
        exc = getattr(step, 'exception', None)
        if exc is not None:
            tb = "".join(traceback.format_exception(None, exc, getattr(exc, "__traceback__", None)))
            step.result.error_message = str(exc)
            step.result.traceback = tb


