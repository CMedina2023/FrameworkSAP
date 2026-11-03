import os
import atexit
import base64
import time
from datetime import datetime
import pytest

from config.settings import Config
from utils.logger import get_logger
from utils.templete_report import (
    add_test_result,
    generate_html_summary,
    clear_results,
    add_step,
    _CURRENT_STEPS,
    set_business_mode,
)
from utils.csv_reader import find_expected_result
from utils.jira_client import jira_client, extract_jira_key_from_item
from utils.driver_wrapper import SapDriverAdapter
from utils.sap_session import SAPSession

logger = get_logger("Conftest")


# ── Fixtures de Sesión y Ejecución SAP ──

@pytest.fixture(scope="session")
def _shared_sap_session(request):
    """Fixture de sesión: abre SAP Logon y mantiene la conexión durante toda la suite."""
    logger.info("[*] Inicializando sesión compartida de SAP GUI...")
    sap = SAPSession(Config)
    session = sap.connect()

    yield {
        "sap": sap,
        "session": session,
    }

    # Teardown de sesión
    logger.info("[*] Finalizando suite: cerrando sesión SAP...")
    try:
        sap.disconnect()
        if Config.SAP_CLOSE_ON_FINISH:
            sap.close_sap_logon()
    except Exception as e:
        logger.warning(f"[!] Error cerrando SAP: {e}")


@pytest.fixture(scope="function")
def driver(request, _shared_sap_session):
    """Fixture por test: provee el SapDriverAdapter y regresa a la pantalla principal (/n) al terminar."""
    session = _shared_sap_session["session"]
    sap = _shared_sap_session["sap"]

    # Limpiar pasos del reporte antes de cada test
    _CURRENT_STEPS.clear()

    adapter = SapDriverAdapter(session)
    request.node._driver = adapter

    yield adapter

    # Teardown del test: volver al menú principal para no dejar transacciones abiertas
    try:
        sap.go_home()
    except Exception as e:
        logger.warning(f"[!] Error al regresar a menú principal de SAP: {e}")

    try:
        set_business_mode(False)
    except Exception:
        pass


@pytest.fixture(scope="function")
def flow_context():
    """Almacena variables dinámicas que se transfieren entre steps de un flujo BDD (TU, docs, HUs, etc.)."""
    class FlowContext:
        def __init__(self):
            self.TU = None
            self.cita = None
            self.puerta = None
            self.docs = []
            self.HUs = []
            self.HUMaster = []
            self.extra = {}

    return FlowContext()


# ── Hooks de Integración para Pytest-BDD (Gherkin) ──

@pytest.hookimpl(optionalhook=True)
def pytest_bdd_before_scenario(request, feature, scenario):
    request.node._bdd_scenario_title = scenario.name
    request.node._bdd_feature_title = feature.name
    request.node._bdd_tags = list(scenario.tags)
    set_business_mode(True)
    logger.info(f"[*] [BDD ESCENARIO INICIADO]: {scenario.name}")


@pytest.hookimpl(optionalhook=True)
def pytest_bdd_after_scenario(request, feature, scenario):
    set_business_mode(False)
    logger.info(f"[*] [BDD ESCENARIO FINALIZADO]: {scenario.name}")


@pytest.hookimpl(optionalhook=True)
def pytest_bdd_before_step(request, feature, scenario, step, step_func):
    step_label = f"{step.keyword.strip()} {step.name}".strip()
    add_step(step_label, "passed", level="business")


@pytest.hookimpl(optionalhook=True)
def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    step_label = f"{step.keyword.strip()} {step.name}".strip()
    logger.error(f"[-] [BDD STEP FAILED]: {step_label} - {exception}")
    if _CURRENT_STEPS and _CURRENT_STEPS[-1]["message"] == step_label:
        _CURRENT_STEPS[-1]["status"] = "failed"
    else:
        add_step(f"Fallo en paso: {step_label}", "failed", level="business")


# ── Integración con Jira Cloud y Reporte Elite ──

def pytest_runtest_setup(item):
    jira_key = extract_jira_key_from_item(item)
    if jira_key and jira_client.is_configured():
        item._jira_key = jira_key
        logger.info(f"[*] Vinculando prueba SAP '{item.name}' con Jira [{jira_key}]...")
        jira_client.transition_to(jira_key, "En Progreso")
        jira_client.add_comment(jira_key, f"🤖 [Automatización SAP] Iniciando ejecución de la prueba: {item.name}")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    driver_adapter = item.funcargs.get("driver") or getattr(item, "_driver", None)
    add_test_result(item, report, driver_adapter)

    # Actualización en Jira Cloud
    jira_key = getattr(item, "_jira_key", None) or extract_jira_key_from_item(item)
    if jira_key and jira_client.is_configured():
        if (call.when == "call") or (call.when == "setup" and report.failed):
            screenshot_path = None
            if driver_adapter and hasattr(driver_adapter, "get_screenshot_as_base64"):
                try:
                    reports_dir = os.path.dirname(Config.REPORT_PATH) or os.path.join(os.getcwd(), "reports")
                    os.makedirs(reports_dir, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_name = f"evidence_{jira_key}_{timestamp}.png"
                    screenshot_path = os.path.join(reports_dir, screenshot_name)

                    b64_data = driver_adapter.get_screenshot_as_base64()
                    if b64_data:
                        with open(screenshot_path, "wb") as fh:
                            fh.write(base64.b64decode(b64_data))
                        logger.info(f"[*] Captura de evidencia guardada para Jira: {screenshot_path}")
                except Exception as e_shot:
                    logger.warning(f"[-] No se pudo capturar pantalla para Jira: {e_shot}")
                    screenshot_path = None

            if call.when == "call":
                if report.passed:
                    logger.info(f"[*] Actualizando Jira [{jira_key}] a Exitoso...")
                    jira_client.transition_to(jira_key, "Exitoso")
                    jira_client.add_comment(jira_key, f"✅ [Automatización SAP] Prueba '{item.name}' finalizada con éxito.")
                    if screenshot_path and os.path.exists(screenshot_path):
                        jira_client.add_attachment(jira_key, screenshot_path)
                elif report.failed:
                    logger.info(f"[*] Actualizando Jira [{jira_key}] a Fallado...")
                    jira_client.transition_to(jira_key, "Fallado")
                    err_detail = str(call.excinfo.value) if call.excinfo else "Error durante la ejecución"
                    jira_client.add_comment(jira_key, f"❌ [Automatización SAP] Prueba '{item.name}' falló.\nDetalle: {err_detail[:400]}")
                    if screenshot_path and os.path.exists(screenshot_path):
                        jira_client.add_attachment(jira_key, screenshot_path)


# ── Hooks de Pytest HTML ──

def pytest_configure(config):
    htmlpath = config.getoption("htmlpath")
    if htmlpath:
        dir_name = os.path.dirname(htmlpath) or "reports"
        os.makedirs(dir_name, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        _, ext = os.path.splitext(os.path.basename(htmlpath))
        config.option.htmlpath = os.path.join(dir_name, f"report_{timestamp}{ext}")


def pytest_html_report_title(report):
    report.title = Config.REPORT_TITLE


def pytest_html_results_summary(prefix, summary, postfix):
    generate_html_summary(prefix, None)


def pytest_sessionstart(session):
    clear_results()


# ── Notificaciones de Resumen (Nexus + Google Chat) ──

_notification_config = {}

def pytest_unconfigure(config):
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    _notification_config["html_path"] = getattr(config.option, "htmlpath", None)


@atexit.register
def _send_notifications_on_exit():
    import requests
    from utils.templete_report import _ELITE_CASES

    html_path = _notification_config.get("html_path")
    if not html_path:
        return

    webhook_url = os.getenv("AUTO_ACC")
    if not webhook_url:
        return

    passed = sum(1 for c in _ELITE_CASES if c["outcome"] == "passed")
    failed = sum(1 for c in _ELITE_CASES if c["outcome"] in ["failed", "error"])
    total = passed + failed

    if total == 0:
        return

    report_url = "https://nexushub.up.railway.app/"
    api_key = os.getenv("NEXUS_API_KEY")
    headers = {"X-API-Key": api_key} if api_key else {}

    if html_path and os.path.exists(html_path):
        try:
            nombre_reporte = os.path.basename(html_path)
            with open(html_path, "rb") as f:
                r_upload = requests.post(
                    "https://nexushub.up.railway.app/api/reports/upload",
                    files={"file": (nombre_reporte, f)},
                    headers=headers,
                    verify=False,
                )
            if r_upload.status_code == 201:
                filename = r_upload.json().get("filename", nombre_reporte)
                report_url = f"https://nexushub.up.railway.app/reports/{filename}"
                logger.info(f"[*] Reporte subido con éxito: {report_url}")
        except Exception as e:
            logger.error(f"[-] Excepción al subir reporte HTML a Nexus: {e}")

    header_icon = (
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Flat_cross_icon.svg/120px-Flat_cross_icon.svg.png"
        if failed > 0 else
        "https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Flat_tick_icon.svg/120px-Flat_tick_icon.svg.png"
    )
    fecha_str = datetime.now().strftime("El %Y-%m-%d a las %H:%M hrs")

    payload = {
        "cardsV2": [
            {
                "cardId": "sap_execution_report",
                "card": {
                    "header": {
                        "title": "AUTOMATIZACIÓN SAP",
                        "subtitle": Config.NOTIFICATION_SUBTITLE,
                        "imageUrl": header_icon,
                        "imageType": "CIRCLE"
                    },
                    "sections": [
                        {
                            "header": "Resumen de ejecución",
                            "widgets": [
                                {
                                    "decoratedText": {
                                        "startIcon": {"iconUrl": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Flat_tick_icon.svg/120px-Flat_tick_icon.svg.png"},
                                        "text": f"Exitosos: {passed}"
                                    }
                                },
                                {
                                    "decoratedText": {
                                        "startIcon": {"iconUrl": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Flat_cross_icon.svg/120px-Flat_cross_icon.svg.png"},
                                        "text": f"Fallidos: {failed}"
                                    }
                                },
                                {
                                    "decoratedText": {
                                        "startIcon": {"knownIcon": "CLOCK"},
                                        "text": f"Fecha: {fecha_str}"
                                    }
                                },
                                {
                                    "buttonList": {
                                        "buttons": [
                                            {
                                                "text": "Ver reportes",
                                                "onClick": {"openLink": {"url": report_url}}
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
        ]
    }

    try:
        requests.post(webhook_url, json=payload, headers={"Content-Type": "application/json; charset=UTF-8"}, timeout=10)
        logger.info("[*] Notificación enviada a Google Chat.")
    except Exception as e:
        logger.error(f"[-] Error al enviar notificación a Google Chat: {e}")
