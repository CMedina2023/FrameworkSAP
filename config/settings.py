import os
from dotenv import load_dotenv

_env_file = os.getenv("ENV_FILE")
if _env_file and os.path.exists(_env_file):
    load_dotenv(_env_file, override=True)
else:
    load_dotenv(override=True)


def _as_bool(value, default="false"):
    return str(os.getenv(value, default)).strip().lower() == "true"


class Config:
    # ── Conexión SAP GUI ──
    SAP_CONNECTION = os.getenv("SAP_CONNECTION", "SAP EWM S/4 (PRE-PRODUCTIVO)")
    SAPLOGON_PATH = os.getenv(
        "SAPLOGON_PATH", r"C:\Program Files (x86)\SAP\FrontEnd\SAPgui\saplogon.exe"
    )
    SAP_CLIENT = os.getenv("SAP_CLIENT", "")
    SAP_LANGUAGE = os.getenv("SAP_LANGUAGE", "ES")

    SAP_USER = os.getenv("SAP_USER")
    SAP_PASS = os.getenv("SAP_PASS")

    # Segundos para esperar controles / que SAP Logon arranque
    SAP_TIMEOUT = int(os.getenv("SAP_TIMEOUT", 30))
    SAP_STARTUP_WAIT = int(os.getenv("SAP_STARTUP_WAIT", 5))

    # Cerrar SAP Logon al terminar la suite
    SAP_CLOSE_ON_FINISH = _as_bool("SAP_CLOSE_ON_FINISH", "true")

    # ── Reportes ──
    REPORT_PATH = os.path.join(os.getcwd(), "reports", "report.html")
    REPORT_TITLE = os.getenv("REPORT_TITLE", "Reporte de Automatización SAP - Liverpool")
    APP_LABEL = os.getenv("APP_LABEL", "SAP EWM")
    NEXUS_PROJECT = os.getenv("NEXUS_PROJECT", "SAP-EWM")
    NOTIFICATION_SUBTITLE = os.getenv("NOTIFICATION_SUBTITLE", "SAP EWM")

    # ── Jira Config ──
    JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "").rstrip("/")
    JIRA_USER_EMAIL = os.getenv("JIRA_USER_EMAIL")
    JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
