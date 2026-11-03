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
                time.sleep(4)  # Pausa fija para asentar SAP Logon
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
            logger.info("[*] Esperando pausa de 6 segundos para que SAP cargue la ventana de login...")
            time.sleep(6)

        # Buscar la sesión activa en el motor de scripting
        session = None
        deadline = time.time() + max(self.config.SAP_TIMEOUT, 15)

        while time.time() < deadline:
            try:
                # Re-inspeccionar application.Children por si connection cambió de estado
                for i in range(application.Children.Count):
                    con = application.Children(i)
                    if getattr(con, "Description", "") == self.config.SAP_CONNECTION or con.Children.Count > 0:
                        connection = con
                        if con.Children.Count > 0:
                            session = con.Children(0)
                            break
                if session is not None:
                    break
            except Exception as e:
                logger.debug(f"Reintentando acceso a la sesión COM: {e}")
            time.sleep(2)

        if connection is None or session is None:
            raise RuntimeError(
                f"No se pudo abrir la conexión SAP '{self.config.SAP_CONNECTION}' dentro del tiempo límite. "
                "Verifica que SAP_CONNECTION coincida EXACTO con el nombre en SAP Logon."
            )

        self._connection = connection
        self.session = session

        logger.info("[*] Sesión detectada. Pausa de 2 segundos para estabilizar la ventana...")
        time.sleep(2)

        # Maximizar ventana para visibilidad clara
        try:
            session.findById("wnd[0]").maximize()
            time.sleep(1)
        except Exception:
            pass

        # Espera activa y validación de la pantalla de login con mensaje de bienvenida
        if self._wait_for_login_screen(timeout=15):
            self._login()
        elif self._is_authenticated():
            logger.info("[*] La sesión ya estaba autenticada; se reutiliza.")
        else:
            logger.info("[*] Sesión iniciada directamente sin pantalla de login previa.")

        logger.info("[+] Sesión SAP conectada correctamente.")
        return session

    def _get_welcome_message(self):
        """Busca y extrae el texto del mensaje de bienvenida de la pantalla de login."""
        try:
            usr = self.session.findById("wnd[0]/usr")
            messages = []
            for i in range(usr.Children.Count):
                child = usr.Children(i)
                text = (getattr(child, "Text", "") or "").strip()
                if not text:
                    continue
                # Identificar palabras clave del mensaje de bienvenida
                text_lower = text.lower()
                if any(k in text_lower for k in ["bienvenido", "welcome", "s4hana", "ewm", "preproductivo", "mandante", "mandate"]):
                    messages.append(text)
            return " | ".join(messages) if messages else None
        except Exception:
            return None

    def _wait_for_login_screen(self, timeout=15):
        """Espera de forma activa a que aparezca la pantalla de login e identifica el mensaje de bienvenida."""
        deadline = time.time() + timeout
        logger.info("[*] Esperando a que cargue la pantalla de login...")
        while time.time() < deadline:
            if self._at_logon_screen():
                welcome_text = self._get_welcome_message()
                if welcome_text:
                    logger.info(f"[+] Pantalla de login confirmada. Mensaje de bienvenida: '{welcome_text}'")
                else:
                    logger.info("[+] Pantalla de login confirmada (campos de credenciales listos).")
                return True
            time.sleep(1)
        return False

    def _is_authenticated(self):
        """Verifica si la sesión ya superó el login y se encuentra en el menú principal."""
        try:
            self.session.findById(SapLoginIds.OKCODE)
            return True
        except Exception:
            return False

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
        time.sleep(2)  # Pausa antes de comenzar a escribir

        if self.config.SAP_CLIENT:
            try:
                s.findById(SapLoginIds.CLIENT).text = self.config.SAP_CLIENT
                time.sleep(0.5)
            except Exception:
                pass

        logger.info(f"[*] Escribiendo usuario '{self.config.SAP_USER}'...")
        s.findById(SapLoginIds.USER).text = self.config.SAP_USER
        time.sleep(0.5)

        logger.info("[*] Escribiendo contraseña...")
        s.findById(SapLoginIds.PASSWORD).text = self.config.SAP_PASS
        time.sleep(0.5)

        if self.config.SAP_LANGUAGE:
            try:
                s.findById(SapLoginIds.LANGUAGE).text = self.config.SAP_LANGUAGE
                time.sleep(0.5)
            except Exception:
                pass

        logger.info("[*] Presionando Enter (F8 / sendVKey 0)...")
        s.findById("wnd[0]").sendVKey(0)
        time.sleep(3)  # Pausa tras presionar Enter

        # Popup de "logon múltiple": continuar sin cerrar otras sesiones
        try:
            s.findById(SapLoginIds.MULTI_LOGON_CONTINUE).select()
            time.sleep(1)
            s.findById("wnd[1]").sendVKey(0)
            time.sleep(2)
        except Exception:
            pass

        # Esperar confirmación de salida de la pantalla de login
        deadline = time.time() + 10
        while time.time() < deadline:
            if not self._at_logon_screen():
                break
            time.sleep(1)

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
