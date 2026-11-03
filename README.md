# Framework de Automatización SAP GUI (100% BDD Gherkin)

Framework de automatización E2E para **SAP GUI** (S/4 HANA & ECC / EWM) basado exclusivamente en **BDD (Gherkin con `pytest-bdd`)**, replicando la arquitectura, reportería e integración continua del framework WEB.

---

## 📑 Guía de Operación Rápida

### 1. Requisitos Previos

- **Windows 10 / 11** con SAP GUI instalado.
- **Scripting habilitado en SAP Logon**:
  * En SAP GUI: *Ajustes / Opciones > Accesibilidad y scripting > Scripting > Habilitar scripting*.
  * Desmarcar: *"Notificar cuando un script se adjunte a SAP GUI"*.
- **Python 3.10+**.

### 2. Instalación

Abre una terminal en la carpeta `FrameworkSAP`:

```bash
cd FrameworkSAP
pip install -r requirements.txt
```

### 3. Configuración del Entorno (`.env`)

Copia la plantilla `.env.example` como `.env`:

```bash
cp .env.example .env
```

Edita el `.env` con los datos de tu ambiente:

```ini
# Nombre de la conexión EXACTO como aparece en SAP Logon:
SAP_CONNECTION=SAP EWM S/4 (PRE-PRODUCTIVO)

# Ruta del ejecutable de SAP Logon:
SAPLOGON_PATH=C:\Program Files (x86)\SAP\FrontEnd\SAPgui\saplogon.exe

# Credenciales de acceso a SAP:
SAP_USER=TU_USUARIO
SAP_PASS=TU_PASSWORD
SAP_CLIENT=100
SAP_LANGUAGE=ES

# Integración con Jira Cloud (Opcional):
JIRA_BASE_URL=https://tuempresa.atlassian.net
JIRA_USER_EMAIL=tu_correo@tuempresa.com
JIRA_API_TOKEN=tu_token_de_jira
```

---

## 🚀 Cómo Ejecutar las Pruebas

Toda la ejecución se realiza mediante el orquestador maestro `runner_central.py` o directamente con `pytest`.

### Opción A: A través de `runner_central.py` (Recomendado)

Genera automáticamente el reporte HTML Elite con capturas de pantalla integradas en `reports/`:

```bash
# 1. Ejecutar TODOS los escenarios BDD:
python runner_central.py

# 2. Ejecutar por etiqueta (tag de proceso):
python runner_central.py --tag arribo
python runner_central.py --tag cortina
python runner_central.py --tag chocolate

# 3. Ejecutar pruebas de humo (smoke):
python runner_central.py --tag smoke

# 4. Ejecutar por ticket de Jira vinculado:
python runner_central.py --tag PC-534
```

### Opción B: Ejecución Granular con `pytest`

Ideal para desarrollo y depuración paso a paso en consola:

```bash
# Ejecutar un archivo de steps específico:
pytest tests/bdd/step_defs/test_arribo_steps.py -v

# Ejecutar con reporte HTML:
pytest tests/bdd -v --html=reports/report.html --self-contained-html

# Ejecutar filtrando por marcador:
pytest tests/bdd -m arribo -v
```

---

## 🛠️ Cómo Crear un Nuevo Flujo BDD (Paso a Paso)

Todo nuevo flujo sigue un estándar de 4 pasos ordenados:

### Paso 1: Redactar el archivo `.feature` (Gherkin en Español)
Crea tu archivo en `apps/ewm/features/mi_proceso.feature`:

```gherkin
# language: es
Característica: Registro de Entrada al Almacén
  Como operador de patio
  Quiero registrar la entrada en SAP
  Para habilitar la descarga de mercancía

  @PC-700 @bdd @smoke @arribo @ICD_102
  Escenario: Registro de entrada exitoso
    Dado que la sesión SAP está abierta y lista para operar
    Cuando ejecuto el arribo para la TU "TU999" con la cita "MES000123"
    Entonces el arribo debe quedar registrado exitosamente para la TU "TU999"
```

### Paso 2: Identificar los IDs de Controles (`Locators`)
Crea las constantes en `apps/ewm/locators/mi_proceso_locators.py`:

```python
class MiProcesoLocators:
    TCODE = "/N/SCWM/TU"
    CAMPO_TU = "wnd[0]/usr/ctxt/SCWM/S_TU_SR_NO-LOW"
    CAMPO_CITA = "wnd[0]/usr/ctxt/SCWM/S_CITA-LOW"
    BTN_EJECUTAR = "wnd[0]/tbar[1]/btn[8]"
```

> **Tip**: Si no conoces los IDs de los campos, usa la grabadora de SAP Logon (ver siguiente sección).

### Paso 3: Crear la Acción Modular con `DriverWrapper`
Crea la función en `apps/ewm/modules/mi_proceso_module.py`:

```python
from utils.driver_wrapper import DriverWrapper
from apps.ewm.locators.mi_proceso_locators import MiProcesoLocators

def procesar_entrada(driver, tu: str, cita: str):
    wrapper = DriverWrapper(driver)
    
    # Cada acción genera automáticamente un paso (add_step) en el reporte
    wrapper.transaction(MiProcesoLocators.TCODE, description="Ingreso a /SCWM/TU")
    wrapper.send_keys(MiProcesoLocators.CAMPO_CITA, cita, description=f"Cita [{cita}]")
    wrapper.send_keys(MiProcesoLocators.CAMPO_TU, tu, description=f"TU [{tu}]")
    wrapper.click(MiProcesoLocators.BTN_EJECUTAR, description="Botón Ejecutar (F8)")
    
    # Validar que no haya error en la barra de estado de SAP
    status = wrapper.get_status_bar()
    if status["type"] == "E":
        raise AssertionError(f"Error en SAP: {status['text']}")
```

### Paso 4: Enlazar los Step Definitions
Crea el archivo `tests/bdd/step_defs/test_mi_proceso_steps.py`:

```python
from pytest_bdd import scenarios, given, when, then, parsers
from apps.ewm.modules.mi_proceso_module import procesar_entrada
from apps.ewm.modules.login_module import validar_sesion_activa

# Enlace al archivo .feature
scenarios("ewm/features/mi_proceso.feature")

@given("que la sesión SAP está abierta y lista para operar")
def verificar_sesion(driver):
    validar_sesion_activa(driver)

@when(parsers.parse('ejecuto el arribo para la TU "{tu}" con la cita "{cita}"'))
def paso_ejecutar(driver, tu, cita):
    procesar_entrada(driver, tu=tu, cita=cita)

@then(parsers.parse('el arribo debe quedar registrado exitosamente para la TU "{tu}"'))
def paso_validar(driver, tu):
    pass
```

---

## 🔄 Transformador de Scripts SAP (.vbs) a Python BDD

El framework incluye una herramienta (`transform_sap_scripts.py` y `tools/sap_transformer/`) que **convierte scripts grabados en SAP Logon (.vbs) directamente a código Python modular con DriverWrapper y escenarios Gherkin BDD**.

### ¿Cómo opera el transformador?

1. **Grabar en SAP Logon**:
   * Abre SAP Logon.
   * Haz clic en el ícono de la grabadora: **Grabar y reproducir script...**
   * Presiona **Grabar**, realiza el proceso en SAP y presiona **Detener**.
   * Guarda el archivo `.vbs` en la carpeta `FrameworkSAP/scripts de sap/` (por ejemplo: `scripts de sap/mi_proceso.vbs`).

2. **Ejecutar la conversión a Python**:
   ```bash
   # Convertir todas las grabaciones nuevas en 'scripts de sap/':
   python transform_sap_scripts.py

   # Convertir un script específico:
   python transform_sap_scripts.py "scripts de sap/mi_proceso.vbs"

   # Forzar regeneración si el archivo ya fue convertido previamente:
   python transform_sap_scripts.py "scripts de sap/mi_proceso.vbs" --force
   ```

3. **Artefactos generados automáticamente**:
   Por cada `.vbs`, el transformador genera 3 componentes:
   - **Locators** (`apps/ewm/locators/mi_proceso_locators.py`): Extrae todos los IDs de controles (`wnd[0]`, campos de texto, botones, tablas) y los organiza como constantes de clase en Python sin duplicados.
   - **Módulo Python** (`apps/ewm/modules/mi_proceso_module.py`): Convierte las acciones crudas de VBS a métodos limpios de `DriverWrapper` (`send_keys`, `click`, `send_vkey`) con llamadas a `add_step` para el reporte HTML.
   - **Feature BDD** (`apps/ewm/features/mi_proceso.feature`): Redacta un archivo Gherkin en español con las etiquetas `@bdd @grabacion @mi_proceso`.

4. **Ejecución inmediata de la grabación convertida**:
   ```bash
   python runner_central.py --tag mi_proceso
   ```

---

## 📈 Integración con Jira Cloud y Reporte Elite

### Jira Cloud
Cuando incluyes una etiqueta de Jira en tu escenario (ej. `@PC-534`), el framework:
1. Pone el issue de Jira en estado **En Progreso** al iniciar la prueba.
2. Si la prueba pasa, cambia el estado a **Exitoso** y agrega un comentario.
3. Si la prueba falla, cambia el estado a **Fallado**, reporta el error y **adjunta automáticamente la captura de pantalla de SAP** en el ticket.

### Reporte HTML Elite Liverpool
Al terminar la ejecución con `runner_central.py`, se genera un reporte HTML interactivo en `reports/`:
- **Gráfica Donut** con porcentaje de éxito y tiempos de ejecución.
- **Línea de tiempo detallada** con cada paso de negocio y técnico ejecutado.
- **Captura de pantalla en Base64** de la ventana de SAP GUI tomada directamente por COM (`hardCopy`).
- Envío automático a **Nexus Hub** y notificación por **Google Chat** si las variables de entorno correspondientes están configuradas.
