"""Modelos del transformador de grabaciones SAP GUI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class RecordingError(ValueError):
    """La grabación no se pudo leer o convertir."""


@dataclass
class SapAction:
    """Una línea de la grabación ya clasificada."""

    kind: str
    python: str = ""
    member: str = ""
    element_id: str = ""
    literal: str | None = None


@dataclass
class TransformResult:
    """Resultado de convertir una grabación."""

    source: Path
    key: str
    function_name: str
    module_path: Path
    locators_path: Path
    feature_path: Path
    steps_path: Path
    actions: int
    skipped: bool


@dataclass
class BatchResult:
    """Resultado de convertir un lote de grabaciones."""

    written: list[TransformResult]
    skipped: list[TransformResult]
    errors: list[str]
