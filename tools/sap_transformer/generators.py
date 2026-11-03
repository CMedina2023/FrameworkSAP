"""Genera Locators, Módulo, Feature y Step Definition a partir de acciones SAP GUI grabadas."""
from __future__ import annotations

import re
from tools.sap_transformer.models import SapAction
from tools.sap_transformer.naming import locators_class_name, module_function_name


def _clean_const_name(element_id: str, suffix: str = "") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", element_id).strip("_").upper()
    parts = [p for p in cleaned.split("_") if p and p not in ("WND", "0", "USR", "SUBX", "SSUB", "CNTNL")]
    res = "_".join(parts[-3:]) if parts else "ELEMENT"
    if suffix:
        res = f"{res}_{suffix.upper()}"
    if res and res[0].isdigit():
        res = f"ID_{res}"
    return res


def render_locators(key: str, class_name: str, actions: list[SapAction]) -> str:
    """Genera la clase de locators con constantes para los IDs de SAP GUI."""
    seen = {}
    lines = [
        '"""Locators generados desde grabación SAP GUI."""',
        f"class {class_name}:",
    ]

    count = 1
    for a in actions:
        if not a.element_id:
            continue
        if a.element_id in seen:
            continue
        cname = _clean_const_name(a.element_id)
        if cname in seen.values():
            cname = f"{cname}_{count}"
            count += 1
        seen[a.element_id] = cname
        lines.append(f'    {cname} = "{a.element_id}"')

    if len(lines) == 2:
        lines.append("    pass")

    lines.append("")
    return "\n".join(lines)


def render_module(key: str, locators_class: str, actions: list[SapAction]) -> str:
    """Genera el módulo de negocio usando DriverWrapper."""
    func_name = module_function_name(key)
    body = [
        '    TU = kwargs.get("TU")',
        '    docs = kwargs.get("docs", [])',
        '    HUs = kwargs.get("HUs", [])',
        '',
    ]

    for a in actions:
        if a.kind == "comment":
            body.append(f"    # VBS: {a.literal}")
        elif a.kind == "assign":
            body.append(f'    wrapper.send_keys("{a.element_id}", {a.python.split("=")[-1].strip()})')
        elif a.kind == "call":
            if a.member.lower() == "sendvkey":
                arg = a.python.split("sendVKey(")[-1].rstrip(")")
                body.append(f"    wrapper.send_vkey({arg})")
            elif a.member.lower() in ("press", "pressbutton"):
                body.append(f'    wrapper.click("{a.element_id}")')
            elif a.member.lower() == "maximize":
                pass
            else:
                body.append(f"    # {a.python}")

    body_code = "\n".join(body) if body else "    pass"

    return f'''"""Módulo generado desde grabación SAP GUI: {key}."""
from utils.driver_wrapper import DriverWrapper
from utils.templete_report import add_step
from apps.ewm.locators.{key}_locators import {locators_class}


def {func_name}(driver, **kwargs):
    """Ejecuta la automatización de la grabación {key}."""
    wrapper = DriverWrapper(driver)
    add_step("Iniciando grabación {key}", "passed")

{body_code}

    add_step("Grabación {key} completada con éxito", "passed")
'''


def render_feature(key: str) -> str:
    titulo = key.replace("_", " ").title()
    return f"""# language: es
Característica: Automatización de Grabación {titulo}
  Como tester de SAP
  Quiero ejecutar la grabación convertida
  Para reproducir el flujo dentro del framework estandarizado

  @bdd @grabacion @{key}
  Escenario: Ejecución de grabación {key}
    Dado que la sesión SAP está abierta y lista para operar
    Cuando ejecuto el módulo de la grabación "{key}"
    Entonces el módulo debe finalizar con éxito
"""


def count_actions(actions: list[SapAction]) -> int:
    return sum(1 for action in actions if action.kind != "comment")
