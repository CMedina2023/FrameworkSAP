import os
import re
import requests
from requests.auth import HTTPBasicAuth
from config.settings import Config
from utils.logger import get_logger

logger = get_logger("JiraClient")


class JiraClient:
    """Cliente para integración con Jira Cloud REST API v3."""

    def __init__(self, base_url=None, user_email=None, api_token=None):
        self.base_url = (base_url or getattr(Config, "JIRA_BASE_URL", None) or os.getenv("JIRA_BASE_URL", "")).rstrip("/")
        self.user_email = user_email or getattr(Config, "JIRA_USER_EMAIL", None) or os.getenv("JIRA_USER_EMAIL")
        self.api_token = api_token or getattr(Config, "JIRA_API_TOKEN", None) or os.getenv("JIRA_API_TOKEN")

        self.auth = HTTPBasicAuth(self.user_email, self.api_token) if self.user_email and self.api_token else None
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def is_configured(self) -> bool:
        """Verifica si las credenciales de Jira están disponibles."""
        return bool(self.base_url and self.user_email and self.api_token)

    def get_issue(self, issue_key: str):
        """Obtiene información básica del issue."""
        if not self.is_configured():
            logger.warning("[!] JiraClient no está configurado. Omitiendo get_issue.")
            return None

        url = f"{self.base_url}/rest/api/3/issue/{issue_key}?fields=status,summary"
        try:
            resp = requests.get(url, auth=self.auth, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            logger.error(f"[-] Error al consultar issue {issue_key}: {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.error(f"[-] Excepción consultando issue {issue_key}: {e}")
        return None

    def get_transitions(self, issue_key: str):
        """Obtiene las transiciones disponibles para un issue."""
        if not self.is_configured():
            return []

        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions"
        try:
            resp = requests.get(url, auth=self.auth, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                return resp.json().get("transitions", [])
            logger.error(f"[-] Error obteniendo transiciones para {issue_key}: {resp.status_code}")
        except Exception as e:
            logger.error(f"[-] Excepción obteniendo transiciones para {issue_key}: {e}")
        return []

    def transition_to(self, issue_key: str, target_state: str) -> bool:
        """Transiciona un issue a un estado destino.
        
        Args:
            issue_key: Clave del issue (ej. 'PC-592')
            target_state: Nombre del estado o acción (ej. 'En Progreso', 'Exitoso', 'Fallado', 'Pendiente')
        """
        if not self.is_configured():
            return False

        transitions = self.get_transitions(issue_key)
        if not transitions:
            logger.warning(f"[!] No hay transiciones disponibles para {issue_key}")
            return False

        target_norm = target_state.strip().lower()

        # Mapeo de sinónimos habituales a posibles estados de destino o nombres de transición
        synonyms = {
            "in progress": ["en progreso", "ejecutar", "in progress", "progreso"],
            "en progreso": ["en progreso", "ejecutar", "in progress", "progreso"],
            "ejecutar": ["en progreso", "ejecutar", "in progress"],
            "passed": ["exitoso", "pasado", "exitoso (1)", "passed", "done", "aprobado", "listo"],
            "exitoso": ["exitoso", "pasado", "exitoso (1)", "passed", "done", "aprobado", "listo"],
            "failed": ["fallado", "no exitoso", "failed", "fallo", "rechazado"],
            "fallado": ["fallado", "no exitoso", "failed", "fallo", "rechazado"],
            "bloqueado": ["bloqueado", "bloqueado (1)", "bloquear", "blocked"],
            "pendiente": ["pendiente", "pendiente (1)", "to do", "por hacer"]
        }
        candidates = synonyms.get(target_norm, [target_norm])

        matched_transition = None
        for t in transitions:
            t_name = t.get("name", "").strip().lower()
            dest_name = t.get("to", {}).get("name", "").strip().lower()

            if dest_name in candidates or t_name in candidates:
                matched_transition = t
                break

        if not matched_transition:
            avail = [f"{t.get('name')} -> {t.get('to', {}).get('name')}" for t in transitions]
            logger.warning(f"[!] No se encontró transición para '{target_state}' en {issue_key}. Disponibles: {avail}")
            return False

        t_id = matched_transition["id"]
        t_name = matched_transition["name"]
        dest_name = matched_transition.get("to", {}).get("name")
        logger.info(f"[*] Aplicando transición '{t_name}' (ID: {t_id}) -> '{dest_name}' en Jira [{issue_key}]")

        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions"
        try:
            resp = requests.post(url, auth=self.auth, headers=self.headers, json={"transition": {"id": t_id}}, timeout=10)
            if resp.status_code in (204, 200):
                logger.info(f"[+] Estado de Jira [{issue_key}] actualizado exitosamente a: {dest_name}")
                return True
            logger.error(f"[-] Error aplicando transición en {issue_key}: {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.error(f"[-] Excepción aplicando transición en {issue_key}: {e}")
        return False

    def add_comment(self, issue_key: str, text: str) -> bool:
        """Agrega un comentario al issue usando ADF (Atlassian Document Format)."""
        if not self.is_configured():
            return False

        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/comment"
        payload = {
            "body": {
                "version": 1,
                "type": "doc",
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": text
                            }
                        ]
                    }
                ]
            }
        }
        try:
            resp = requests.post(url, auth=self.auth, headers=self.headers, json=payload, timeout=10)
            if resp.status_code in (201, 200):
                logger.info(f"[+] Comentario agregado en Jira [{issue_key}]")
                return True
            logger.error(f"[-] Error al agregar comentario en {issue_key}: {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.error(f"[-] Excepción al agregar comentario en {issue_key}: {e}")
        return False

    def add_attachment(self, issue_key: str, file_path: str) -> bool:
        """Adjunta un archivo (evidencia, captura, log) al issue."""
        if not self.is_configured() or not os.path.exists(file_path):
            return False

        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/attachments"
        headers = {
            "Accept": "application/json",
            "X-Atlassian-Token": "no-check"
        }
        try:
            filename = os.path.basename(file_path)
            with open(file_path, "rb") as f:
                files = {"file": (filename, f)}
                resp = requests.post(url, auth=self.auth, headers=headers, files=files, timeout=30)
            if resp.status_code in (200, 201):
                logger.info(f"[+] Archivo '{filename}' adjuntado con éxito en Jira [{issue_key}]")
                return True
            logger.error(f"[-] Error al adjuntar archivo en {issue_key}: {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.error(f"[-] Excepción al adjuntar archivo en {issue_key}: {e}")
        return False


# Instancia singleton para fácil reutilización
jira_client = JiraClient()


def extract_jira_key_from_item(item) -> str | None:
    """Extrae la clave del ticket de Jira desde los marcadores de pytest o tags BDD."""
    # 1. Marcador @pytest.mark.jira("KEY")
    marker = item.get_closest_marker("jira")
    if marker and marker.args:
        return str(marker.args[0]).strip()

    # 2. Marcadores dinámicos o nombres de marcadores que coincidan con patrón JIRA (ej. PC_592 o PC-592)
    jira_pattern = re.compile(r'^[A-Za-z]+[-_]\d+$')
    for m in getattr(item, "own_markers", []):
        if jira_pattern.match(m.name):
            return m.name.replace("_", "-").upper()

    # 3. Tags BDD (escenarios Gherkin)
    bdd_tags = getattr(item, "_bdd_tags", None) or getattr(getattr(item, "node", None), "_bdd_tags", [])
    for tag in bdd_tags:
        cleaned = tag.lstrip("@").strip()
        if jira_pattern.match(cleaned):
            return cleaned.replace("_", "-").upper()

    return None
