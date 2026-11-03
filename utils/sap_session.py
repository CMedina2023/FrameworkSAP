"""Conexión a SAP GUI Scripting (refactor de core/sap_session.py del framework anterior).

- Abre SAP Logon si no está abierto.
- Reutiliza la conexión si ya existe, si no la abre.
- Hace login con las credenciales del .env (Config).
"""
import os
import time

from config.settings import Config
from utils.logger import get_logger

logger = get_logger("SAPSession")


class SapLoginIds:
    USER = "wnd[0]/usr/txtRSYST-BNAME"
    PASSWORD = "wnd[0]/usr/pwdRSYST-BCODE"
    CLIENT = "wnd[0]/usr/txtRSYST-MANDT"
    LANGUAGE = "wnd[0]/usr/txtRSYST-LANGU"
    MULTI_LOGON_CONTINUE = "wnd[1]/usr/radMULTI_LOGON_OPT2"
    STATUS_BAR = "wnd[0]/sbar"
    OKCODE = "wnd[0]/tbar[0]/okcd"


class SAPSession:
    def __init__(self, config=Config):
        self.config = config
        self.session = None
        self._connection = None

    # ---------------------------------------------------------
    # SAP Logon
    # ---------------------------------------------------------
    def _get_sapgui(self):
        import win32com.client
        return win32com.client.GetObject("SAPGUI")

    def _start_saplogon_if_needed(self):
        try:
            self._get_sapgui()
            return
        except Exception:
            pass

        path = self.config.SAPLOGON_PATH
        if not os.path.exists(path):
            raise FileNotFoundError(f"No se encontró saplogon.exe en: {path}")

        logger.info("[*] Iniciando SAP Logon...")
        os.startfile(path)

        deadline = time.time() + max(self.config.SAP_STARTUP_WAIT, 1) * 3
        time.sleep(self.config.SAP_STARTUP_WAIT)
        while time.time() < deadline:
            try:
                self._get_sapgui()
                return
            except Exception:
                time.sleep(1)
        raise RuntimeError("SAP Logon no respondió (objeto SAPGUI no disponible).")

    # ---------------------------------------------------------
    # Conexión + login
    # ---------------------------------------------------------
    def connect(self):
        import pythoncom
        pythoncom.CoInitialize()

        self._start_saplogon_if_needed()
        application = self._get_sapgui().GetScriptingEngine

        connection = None
        for i in range(application.Children.Count):
            con = application.Children(i)
            if getattr(con, "Description", "") == self.config.SAP_CONNECTION:
                connection = con
                break

        if connection is None:
            logger.info(f"[*] Abriendo conexión '{self.config.SAP_CONNECTION}'...")
            connection = application.OpenConnection(self.config.SAP_CONNECTION, True)
            time.sleep(3)

        if connection is None or connection.Children.Count == 0:
            raise RuntimeError(
                f"No se pudo abrir la conexión SAP '{self.config.SAP_CONNECTION}'. "
                "Verifica que SAP_CONNECTION coincida EXACTO con el nombre en SAP Logon."
            )

        self._connection = connection
        session = connection.Children(0)
        self.session = session

        if self._at_logon_screen():
            self._login()
        else:
            logger.info("[*] La sesión ya estaba autenticada; se reutiliza.")

        session.findById("wnd[0]").maximize()
        logger.info("[+] Sesión SAP conectada correctamente.")
        return session

    def _at_logon_screen(self):
        try:
            self.session.findById(SapLoginIds.USER)
            return True
        except Exception:
            return False

    def _login(self):
        if not self.config.SAP_USER or not self.config.SAP_PASS:
            raise RuntimeError("Faltan SAP_USER / SAP_PASS en el archivo .env.")

        logger.info("[*] Realizando login en SAP...")
        s = self.session
        if self.config.SAP_CLIENT:
            try:
                s.findById(SapLoginIds.CLIENT).text = self.config.SAP_CLIENT
            except Exception:
                pass
        s.findById(SapLoginIds.USER).text = self.config.SAP_USER
        s.findById(SapLoginIds.PASSWORD).text = self.config.SAP_PASS
        try:
            s.findById(SapLoginIds.LANGUAGE).text = self.config.SAP_LANGUAGE
        except Exception:
            pass
        s.findById("wnd[0]").sendVKey(0)
        time.sleep(2)

        # Popup de "logon múltiple": continuar sin cerrar otras sesiones
        try:
            s.findById(SapLoginIds.MULTI_LOGON_CONTINUE).select()
            s.findById("wnd[1]").sendVKey(0)
        except Exception:
            pass

        if self._at_logon_screen():
            status = ""
            try:
                status = s.findById(SapLoginIds.STATUS_BAR).text
            except Exception:
                pass
            raise RuntimeError(f"Login SAP fallido. {status}".strip())

    # ---------------------------------------------------------
    # Cierre
    # ---------------------------------------------------------
    def go_home(self):
        """Regresa al menú principal (equivalente a /n)."""
        if not self.session:
            return
        try:
            while self.session.Children.Count > 1:
                self.session.findById(f"wnd[{self.session.Children.Count - 1}]").close()
        except Exception:
            pass
        try:
            self.session.findById(SapLoginIds.OKCODE).text = "/n"
            self.session.findById("wnd[0]").sendVKey(0)
        except Exception as e:
            logger.warning(f"[!] No se pudo regresar al menú principal: {e}")

    def disconnect(self):
        if not self.session:
            return
        try:
            logger.info("[*] Cerrando sesión SAP...")
            self.session.findById(SapLoginIds.OKCODE).text = "/nex"
            self.session.findById("wnd[0]").sendVKey(0)
        except Exception:
            pass
        finally:
            self.session = None
            self._connection = None

    def close_sap_logon(self):
        try:
            os.system("taskkill /F /IM saplogon.exe >NUL 2>&1")
            logger.info("[*] SAP Logon cerrado.")
        except Exception as e:
            logger.warning(f"[!] No se pudo cerrar SAP Logon: {e}")
