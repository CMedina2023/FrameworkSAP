"""Adaptador y Wrapper de SAP GUI Scripting con la misma arquitectura del DriverWrapper WEB.

Permite:
1. Reutilizar el reporte HTML (templete_report.py) llamando a get_screenshot_as_base64().
2. Acciones estándar (send_keys, click, press, send_vkey, transaction, etc.) con add_step automático.
3. Métodos utilitarios como get_columna, status_bar, y esperas dinámicas.
"""
import os
import time
import base64
import tempfile
from datetime import datetime

from config.settings import Config
from utils.logger import get_logger
from utils.templete_report import add_step

logger = get_logger("DriverWrapper")


class SapElementSimulator:
    """Emula un elemento capturado con métodos similares a los de Playwright/Selenium."""
    def __init__(self, raw_element, selector):
        self.raw = raw_element
        self.selector = selector

    @property
    def text(self):
        try:
            return getattr(self.raw, "text", "") or ""
        except Exception as e:
            logger.error(f"[-] Error al obtener texto del elemento {self.selector}: {e}")
            return ""


class SapWaitSimulator:
    """Manejo de esperas explícitas para controles de SAP GUI."""
    def __init__(self, session, timeout_seconds):
        self.session = session
        self.timeout = timeout_seconds

    def until(self, selector, timeout=None):
        limit = timeout or self.timeout
        deadline = time.time() + limit
        last_error = None

        while time.time() < deadline:
            try:
                elem = self.session.findById(selector)
                if elem is not None:
                    return SapElementSimulator(elem, selector)
            except Exception as e:
                last_error = e
            time.sleep(0.3)

        raise AssertionError(
            f"El control SAP '{selector}' no apareció tras {limit} segundos de espera. Detalle: {last_error}"
        )


class SapDriverAdapter:
    """Adaptador de la sesión SAP GUI compatible con el reporte del framework WEB."""
    def __init__(self, session):
        self.session = session

    def get_screenshot_as_base64(self):
        """Captura la ventana principal de SAP GUI y la entrega en base64 para el reporte HTML."""
        if not self.session:
            return None

        temp_dir = tempfile.gettempdir()
        bmp_path = os.path.join(temp_dir, f"sap_shot_{int(time.time()*1000)}.bmp")
        png_path = bmp_path.replace(".bmp", ".png")

        try:
            # SAP GUI hardCopy guarda el screenshot nativo del window
            self.session.findById("wnd[0]").hardCopy(bmp_path, 2)

            # Convertir a PNG usando PIL si está disponible para optimizar tamaño
            try:
                from PIL import Image
                with Image.open(bmp_path) as im:
                    im.save(png_path, "PNG")
                target_file = png_path
            except Exception:
                target_file = bmp_path

            with open(target_file, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")

            # Limpieza de temporales
            for p in (bmp_path, png_path):
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass

            return encoded

        except Exception as e:
            logger.warning(f"[-] No se pudo capturar pantalla en SAP GUI: {e}")
            return None

    def quit(self):
        """Finaliza o libera la sesión."""
        try:
            if self.session:
                self.session.findById("wnd[0]/tbar[0]/okcd").text = "/n"
                self.session.findById("wnd[0]").sendVKey(0)
        except Exception:
            pass


class DriverWrapper:
    """Wrapper para automatizar SAP GUI con logging y pasos de reporte automáticos."""
    def __init__(self, driver):
        # driver puede ser el SapDriverAdapter o directamente la GuiSession
        if hasattr(driver, "session"):
            self.driver = driver
            self.session = driver.session
        else:
            self.driver = SapDriverAdapter(driver)
            self.session = driver

        self.logger = logger
        self.wait = SapWaitSimulator(self.session, Config.SAP_TIMEOUT)

    # -------------------------------------------------------------
    # Acciones de Entrada y Botones
    # -------------------------------------------------------------
    def send_keys(self, selector, text, description=None, is_secret=False):
        """Escribe texto en un campo de texto de SAP GUI."""
        label = description if description else f"el campo '{selector}'"
        valor_log = "********" if is_secret else str(text)
        msg = f"Ingresando '{valor_log}' en {label}"
        self.logger.info(f"[*] {msg}")
        add_step(msg)

        try:
            elem = self.session.findById(selector)
            elem.text = str(text)
        except Exception as e:
            err = f"Error al escribir en {label}: {e}"
            self.logger.error(f"[-] {err}")
            add_step(err, "failed")
            raise AssertionError(err) from e

    def click(self, selector, description=None):
        """Hace clic o presiona un botón / control en SAP GUI."""
        label = description if description else f"el control '{selector}'"
        msg = f"Click en {label}"
        self.logger.info(f"[*] {msg}")
        add_step(msg)

        try:
            elem = self.session.findById(selector)
            if hasattr(elem, "press"):
                elem.press()
            elif hasattr(elem, "select"):
                elem.select()
            else:
                elem.setFocus()
        except Exception as e:
            err = f"Error al presionar {label}: {e}"
            self.logger.error(f"[-] {err}")
            add_step(err, "failed")
            raise AssertionError(err) from e

    def press(self, selector, description=None):
        """Alias para click()."""
        self.click(selector, description=description)

    def send_vkey(self, vkey_number: int, description=None):
        """Envía una tecla virtual de SAP (0=Enter, 3=Volver/F3, 8=Ejecutar/F8, 12=Cancelar, etc.)."""
        nombres_comunes = {
            0: "Enter (VKey 0)",
            3: "F3 / Volver (VKey 3)",
            7: "F7 / Anterior (VKey 7)",
            8: "F8 / Ejecutar (VKey 8)",
            11: "Guardar / Ctrl+S (VKey 11)",
            12: "F12 / Cancelar (VKey 12)",
            15: "F15 / Salir (VKey 15)"
        }
        label = description or nombres_comunes.get(vkey_number, f"VKey {vkey_number}")
        msg = f"Presionando tecla virtual {label}"
        self.logger.info(f"[*] {msg}")
        add_step(msg)

        try:
            self.session.findById("wnd[0]").sendVKey(int(vkey_number))
        except Exception as e:
            err = f"Error al enviar VKey {vkey_number}: {e}"
            self.logger.error(f"[-] {err}")
            add_step(err, "failed")
            raise AssertionError(err) from e

    def transaction(self, tcode: str, description=None):
        """Ejecuta una transacción de SAP (/n + tcode)."""
        label = description or f"transacción {tcode}"
        msg = f"Accediendo a {label}"
        self.logger.info(f"[*] {msg}")
        add_step(msg)

        try:
            formatted = tcode.strip()
            if not formatted.startswith("/"):
                formatted = f"/n{formatted}"
            self.session.findById("wnd[0]/tbar[0]/okcd").text = formatted
            self.session.findById("wnd[0]").sendVKey(0)
        except Exception as e:
            err = f"Error al navegar a la transacción {tcode}: {e}"
            self.logger.error(f"[-] {err}")
            add_step(err, "failed")
            raise AssertionError(err) from e

    def set_focus(self, selector):
        try:
            self.session.findById(selector).setFocus()
        except Exception as e:
            self.logger.warning(f"[!] No se pudo dar foco a {selector}: {e}")

    def set_caret(self, selector, position: int):
        try:
            self.session.findById(selector).caretPosition = int(position)
        except Exception:
            pass

    def select_tab(self, selector, description=None):
        label = description or f"pestaña '{selector}'"
        msg = f"Seleccionando {label}"
        self.logger.info(f"[*] {msg}")
        add_step(msg)
        try:
            self.session.findById(selector).select()
        except Exception as e:
            err = f"Error al seleccionar pestaña {label}: {e}"
            self.logger.error(f"[-] {err}")
            add_step(err, "failed")
            raise AssertionError(err) from e

    def press_toolbar_button(self, grid_shell_selector, button_id, description=None):
        label = description or f"botón de grilla '{button_id}'"
        msg = f"Presionando {label}"
        self.logger.info(f"[*] {msg}")
        add_step(msg)
        try:
            self.session.findById(grid_shell_selector).pressButton(button_id)
        except Exception as e:
            err = f"Error al presionar {label}: {e}"
            self.logger.error(f"[-] {err}")
            add_step(err, "failed")
            raise AssertionError(err) from e

    # -------------------------------------------------------------
    # Consultas y Validaciones
    # -------------------------------------------------------------
    def get_text(self, selector):
        try:
            return getattr(self.session.findById(selector), "text", "") or ""
        except Exception as e:
            self.logger.error(f"[-] Error al leer texto de {selector}: {e}")
            return ""

    def get_status_bar(self):
        """Retorna el texto y el tipo de la barra de estado de SAP (S=Éxito, W=Advertencia, E=Error, A=Abend)."""
        try:
            sbar = self.session.findById("wnd[0]/sbar")
            return {
                "text": getattr(sbar, "text", "") or "",
                "type": getattr(sbar, "messageType", "") or ""
            }
        except Exception:
            return {"text": "", "type": ""}

    def exists(self, selector):
        try:
            self.session.findById(selector)
            return True
        except Exception:
            return False

    def get_columna(self, id_tabla, id_columna):
        """Extrae todos los valores no vacíos de una columna en un Grid/Table control de SAP."""
        arreglo = []
        try:
            grid = self.session.findById(id_tabla)
            filas = getattr(grid, "RowCount", 0)
            for i in range(filas):
                val = grid.getCellValue(i, id_columna)
                if val:
                    arreglo.append(val)
        except Exception as e:
            self.logger.error(f"[-] Error al obtener columna {id_columna} de {id_tabla}: {e}")
        return arreglo
