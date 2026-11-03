---
name: sap-automation
description: Guía experta para construir scripts, locators, módulos y pruebas BDD en SAP GUI con Pytest-BDD y DriverWrapper.
---

# Guía de Construcción de Scripts y Flujos SAP GUI

Esta skill detalla el procedimiento paso a paso para automatizar transacciones y procesos logísticos en SAP GUI (S/4 HANA, ECC y EWM) dentro del framework estandarizado.

---

## 1. Filosofía de Arquitectura (Patrón Page Object / Module)

En este framework no escribimos scripts planos ni llamadas monolíticas `session.findById` dispersas en los tests. Se sigue la separación de 4 capas:

```
[ .feature (Gherkin) ]
        │
[ test_*_steps.py (Step Definitions) ]
        │
[ *_module.py (Lógica de Negocio con DriverWrapper) ]
        │
[ *_locators.py (Constantes de IDs de SAP GUI) ]
```

---

## 2. Los Dos Caminos de Construcción

### Camino A: Desde Grabación SAP Logon (Recomendado para procesos nuevos)

1. Abre **SAP Logon** y accede al mandante de pruebas.
2. Haz clic en el ícono de la grabadora en la barra de herramientas: **Grabar y reproducir script...**
3. Haz clic en **Grabar** y ejecuta el proceso en SAP.
4. Presiona **Detener** y guarda el archivo `.vbs` en:
   `FrameworkSAP/scripts de sap/<nombre_proceso>.vbs`
5. Ejecuta el transformador automático:
   ```bash
   python transform_sap_scripts.py "scripts de sap/<nombre_proceso>.vbs" --force
   ```
6. El transformador creará automáticamente:
   - `apps/ewm/locators/<nombre_proceso>_locators.py`
   - `apps/ewm/modules/<nombre_proceso>_module.py`
   - `apps/ewm/features/<nombre_proceso>.feature`
7. Refina el módulo generado agregando validaciones de la barra de estado y descripciones legibles.

---

### Camino B: Construcción Manual (Recomendado para mantenimiento o flujos conocidos)

#### Paso 1: Localizadores (`Locators`)
Crea un archivo en `apps/ewm/locators/<flujo>_locators.py`:
- Los IDs de SAP GUI tienen la estructura: `wnd[x]/usr/...` o `wnd[x]/tbar[x]/...`
- Define constantes con nombres en mayúsculas que describan el propósito del campo, no el ID técnico.

```python
class AsignaCortinaLocators:
    TCODE = "/N/SCWM/RFUI"
    MENU_INPUT = "wnd[0]/usr/subX:/SCWM/SAPLRF_SSCR:0001/txt/SCWM/S_RF_SCRELM-MENU"
    TU_BARCODE_INPUT = "wnd[0]/usr/txtP_BCODE"
    PB1_BUTTON = "wnd[0]/usr/btn/SCWM/S_RF_SCRELM-PB1"
    STATUS_BAR = "wnd[0]/sbar"
```

#### Paso 2: Módulo de Negocio (`Module`)
Crea la lógica en `apps/ewm/modules/<flujo>_module.py` usando `DriverWrapper`.

**Reglas indispensables del módulo:**
1. Siempre envolver `driver` con `wrapper = DriverWrapper(driver)`.
2. Proporcionar el argumento `description` en cada método (`click`, `send_keys`, `transaction`) para que el reporte HTML muestre pasos legibles de negocio.
3. Usar `is_secret=True` si se manejan contraseñas.
4. Siempre validar el resultado mediante la barra de estado (`wrapper.get_status_bar()`) o verificando la aparición de un control con `wrapper.wait.until(...)`.
5. Lanzar `AssertionError` descriptivo si ocurre un fallo para que Pytest y Jira marquen el caso como `failed`.

```python
from utils.driver_wrapper import DriverWrapper
from utils.templete_report import add_step
from apps.ewm.locators.arribo_locators import ArriboLocators

def registrar_arribo(driver, tu: str, cita: str = None):
    wrapper = DriverWrapper(driver)

    try:
        # 1. Navegar a la transacción
        wrapper.transaction(ArriboLocators.TCODE, description="Transacción de Arribo /SCWM/TU")

        # 2. Llenar campos
        if cita:
            wrapper.send_keys(ArriboLocators.CITA_INPUT, cita, description=f"Cita [{cita}]")
        wrapper.send_keys(ArriboLocators.TU_INPUT, tu, description=f"Unidad de Transporte [{tu}]")

        # 3. Acciones de teclado / botones
        wrapper.send_vkey(0, description="Enter para validar datos")
        wrapper.click(ArriboLocators.EXECUTE_BUTTON, description="Botón Ejecutar (F8)")

        # 4. Validar barra de estado de SAP
        status = wrapper.get_status_bar()
        if status["type"] == "E":  # 'E' indica Error en SAP
            raise AssertionError(f"SAP reportó error en el arribo: {status['text']}")

        add_step(f"Arribo completado exitosamente para TU={tu}", "passed")
        return tu

    except Exception as e:
        msg_error = f"Error al procesar el arribo para TU '{tu}': {e}"
        add_step(msg_error, "failed")
        raise AssertionError(msg_error) from e
```

---

## 3. Catálogo de Acciones de `DriverWrapper`

`DriverWrapper` provee métodos de alto nivel adaptados a SAP GUI:

| Método | Propósito | Ejemplo |
|---|---|---|
| `transaction(tcode, description)` | Ingresa `/n{tcode}` y presiona Enter | `wrapper.transaction("/SCWM/RFUI")` |
| `send_keys(selector, text, description, is_secret)` | Escribe en un campo de texto | `wrapper.send_keys(Loc.USER, "USR1", is_secret=False)` |
| `click(selector, description)` | Hace clic o presiona un botón | `wrapper.click(Loc.BTN_ACEPTAR)` |
| `send_vkey(vkey_id, description)` | Envía tecla virtual SAP (Enter=0, F3=3, F8=8, etc.) | `wrapper.send_vkey(0)` |
| `get_status_bar()` | Lee el texto y tipo (`S`, `W`, `E`) de la barra de estado | `status = wrapper.get_status_bar()` |
| `wait.until(selector, timeout)` | Espera activa hasta que el control aparezca | `wrapper.wait.until("wnd[0]/usr/lblEXITO")` |
| `get_columna(table_id, col_id)` | Extrae todos los valores de una columna en una tabla ALV | `filas = wrapper.get_columna(Loc.TABLA, "DOCNO")` |
| `select_tab(selector, description)` | Cambia de pestaña en un contenedor con tabs | `wrapper.select_tab(Loc.TAB_POSICIONES)` |
| `exists(selector)` | Verifica si un control existe en la pantalla actual | `if wrapper.exists(Loc.POPUP): ...` |

### Teclas Virtuales (VKeys) más comunes de SAP GUI:
- `0` = Enter
- `3` = F3 (Atrás / Volver)
- `5` = F5 (Modificar / Detalle)
- `7` = F7 (Paso anterior / Menú RFUI)
- `8` = F8 (Ejecutar)
- `11` = Ctrl + S (Guardar)
- `12` = F12 (Cancelar)
- `15` = Shift + F3 (Salir / Exit)

---

## 4. Redacción del Feature BDD (`.feature`)

Los archivos `.feature` se escriben en **Gherkin en Español** dentro de `apps/ewm/features/`.

```gherkin
# language: es
Característica: Asignación de Cortina en RFUI
  Como operador de patio
  Quiero asignar una cortina a una unidad de transporte
  Para coordinar la descarga en el muelle

  @PC-535 @bdd @smoke @cortina @ICD_103
  Escenario: Asignar cortina correctamente a TU
    Dado que la sesión SAP está abierta y lista para operar
    Cuando asigno la cortina para la unidad de transporte "TU123"
    Entonces el sistema debe confirmar la asignación sin errores
```

### Reglas de Etiquetas (Tags):
- `@PC-XXX`: Vincula automáticamente la prueba con el issue en **Jira Cloud**.
- `@ICD_XXX`: Mapea dinámicamente el resultado esperado configurado en `apps/ewm/data/expected_result.csv`.
- `@smoke` / `@regression`: Clasifican la suite para ejecuciones filtradas.
- `@arribo`, `@cortina`, `@chocolate`: Permiten ejecutar flujos puntuales con `python runner_central.py --tag <tag>`.

---

## 5. Definición de Pasos (`Step Definitions`)

En `tests/bdd/step_defs/test_<flujo>_steps.py`:

```python
from pytest_bdd import scenarios, given, when, then, parsers
from apps.ewm.modules.login_module import validar_sesion_activa
from apps.ewm.modules.cortina_module import asignar_cortina
from utils.csv_reader import resolve_env

# 1. Enlazar el feature
scenarios("ewm/features/cortina.feature")

# 2. Paso inicial común
@given("que la sesión SAP está abierta y lista para operar")
def verificar_sesion(driver):
    validar_sesion_activa(driver)

# 3. Paso de acción delegando al módulo
@when(parsers.parse('asigno la cortina para la unidad de transporte "{tu}"'))
def paso_asignar(driver, flow_context, tu):
    tu_valor = resolve_env(tu)
    flow_context.TU = tu_valor  # Compartir con pasos posteriores si es un flujo E2E
    asignar_cortina(driver, tu=tu_valor)

# 4. Paso de aserción final
@then("el sistema debe confirmar la asignación sin errores")
def paso_validar(driver):
    pass
```

---

## 6. Manejo de Estado entre Pasos (`flow_context`)

Para flujos continuos (como el flujo completo de Recibo Chocolate: Arribo -> Cortina -> Recibo):
- Pytest provee el fixture `flow_context` (inyectado automáticamente por `conftest.py`).
- Puedes guardar valores en un paso (`flow_context.TU = "TU123"`) y consumirlos en pasos siguientes sin quemar datos en duro.

---

## 7. Buenas Prácticas y Restricciones Técnicas

1. **Sin Paralelismo (Single-Thread)**: SAP GUI Scripting por COM no es thread-safe. Nunca ejecutar con `pytest -n` (xdist). El orquestador `runner_central.py` ya previene esto por diseño.
2. **Reinicio de Pantalla (`/n`)**: Al finalizar cada test, el fixture `driver` ejecuta automáticamente `sap.go_home()` para regresar al menú principal y evitar que un test deje una transacción bloqueada para el siguiente.
3. **Manejo de Popups**: Si la transacción muestra un diálogo de confirmación (típicamente `wnd[1]`), verificar primero con `wrapper.exists("wnd[1]")` antes de interactuar.
4. **No quemar credenciales**: Siempre leer usuarios y passwords desde `.env` mediante `Config.SAP_USER` y `Config.SAP_PASS`.
