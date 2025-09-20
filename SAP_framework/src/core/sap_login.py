import time
import win32com.client
import subprocess
import sys
from time import sleep
from src.config.config import SAPConfig, Credentials
import logging

logger = logging.getLogger(__name__)

def open_sap_logon():
    path = SAPConfig.SAP_LOGON_PATH
    subprocess.Popen(path)
    sleep(10)

class SAPLogin:
    def __init__(self):
        self.SapGuiAuto = None
        self.application = None
        self.connection = None
        self.session = None

    def establish_connection(self):
        try:
            self.SapGuiAuto = win32com.client.GetObject("SAPGUI")
            logger.info("SAP GUI ya está abierto.")
        except:
            logger.info("SAP Logon no está abierto. Abriéndolo...")
            open_sap_logon()
            self.SapGuiAuto = win32com.client.GetObject("SAPGUI")
            sleep(5)

        self.application = self.SapGuiAuto.GetScriptingEngine
        self.connection = self.application.OpenConnection(SAPConfig.CONNECTION_NAME, True)
        self.session = self.connection.Children(0)
        logger.info("Conexión establecida correctamente.")
        return self.session

    def login(self):
        if not self.session:
            self.establish_connection()

        try:
            logger.info("Realizando login...")
            self.session.findById("wnd[0]/usr/txtRSYST-MANDT").text = SAPConfig.DEFAULT_CLIENT
            self.session.findById("wnd[0]/usr/txtRSYST-BNAME").text = Credentials.USERNAME
            self.session.findById("wnd[0]/usr/pwdRSYST-BCODE").text = Credentials.PASSWORD
            self.session.findById("wnd[0]/usr/txtRSYST-LANGU").text = SAPConfig.DEFAULT_LANGUAGE
            self.session.findById("wnd[0]").sendVKey(0)

            sleep(3)  # Aumentar tiempo de espera

            # Cierre de modal de inicio de sesion
            from src.core.sap_utils import close_sap_popups
            close_sap_popups(self.session)
            try:
                # Intentar diferentes IDs comunes de modales SAP
                modal_ids = ["wnd[1]", "wnd[2]"]
                button_ids = [
                    "wnd[1]/usr/btnSPOP-OPTION1",  # Botón OK/Continuar estándar
                    "wnd[1]/tbar[0]/btn[0]",  # Botón de toolbar
                    "wnd[1]/usr/btnBUTTON_1",  # Otro formato común
                    "wnd[2]/usr/btnSPOP-OPTION1"  # Modal en segunda ventana
                ]

                for modal_id in modal_ids:
                    try:
                        if self.session.findById(modal_id).exists:
                            logger.info(f"Modal detectado en {modal_id}")

                            # Intentar todos los botones posibles
                            for button_id in button_ids:
                                try:
                                    self.session.findById(button_id).press()
                                    logger.info(f"Modal cerrado con botón: {button_id}")
                                    break
                                except:
                                    continue

                            break
                    except:
                        continue

            except Exception as modal_error:
                logger.info(f"No se pudo cerrar modal o no existía: {modal_error}")

            logger.info("Login completado exitosamente.")
            return True

        except Exception as e:
            logger.error(f"Error durante el login: {e}")
            return False

    def close_connection(self):
        logger.info("Cerrando conexión...")
        self.session = None
        self.connection = None
        self.application = None
        self.SapGuiAuto = None
