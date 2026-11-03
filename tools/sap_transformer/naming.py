"""Nombres de módulos y locators a partir del archivo de grabación."""

from __future__ import annotations

import re
import unicodedata

from tools.sap_transformer.models import RecordingError

RESERVED_KEYS = frozenset({"base", "common", "generated_manifest", "conftest"})


def recording_key(stem: str) -> str:
    """Convierte el nombre del archivo en un identificador snake_case."""
    normalized = unicodedata.normalize("NFKD", stem)
    without_marks = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )
    slug = re.sub(r"[^0-9a-zA-Z]+", "_", without_marks).strip("_").lower()
    if not slug:
        raise RecordingError(
            f"El nombre '{stem}' no produce un identificador válido."
        )
    if slug[0].isdigit():
        slug = f"flujo_{slug}"
    if not slug.isidentifier() or slug in RESERVED_KEYS:
        raise RecordingError(
            f"El nombre '{stem}' no puede usarse como módulo."
        )
    return slug


def locators_class_name(key: str) -> str:
    """Convierte snake_case en el nombre de la clase de locators."""
    parts = [part.capitalize() for part in key.split("_") if part]
    return "".join(parts) + "Locators"


def module_function_name(key: str) -> str:
    """Nombre de la función pública que ejecuta la grabación."""
    return f"ejecutar_{key}"
