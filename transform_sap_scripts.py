"""CLI para convertir grabaciones .vbs a locators y módulos del FrameworkSAP."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.sap_transformer.models import RecordingError
from tools.sap_transformer.service import TransformationService, SCRIPTS_DIRNAME


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="transform_sap_scripts",
        description="Convierte grabaciones .vbs de SAP Logon en Locators, Módulos y Features del framework.",
    )
    parser.add_argument(
        "rutas",
        nargs="*",
        help=f"Archivos .vbs o carpetas. Por defecto usa '{SCRIPTS_DIRNAME}'.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenera los archivos si ya existen.",
    )
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parent
    service = TransformationService(root)

    try:
        batch = service.transform_paths(args.rutas, force=args.force)
    except RecordingError as exc:
        print(f"Error: {exc}")
        return 1

    for item in batch.written:
        print(f"[+] Convertido: {item.source.name}")
        print(f"    Locators: {item.locators_path}")
        print(f"    Módulo:   {item.module_path}")
        print(f"    Feature:  {item.feature_path}")
        print(f"    Acciones: {item.actions}")

    for item in batch.skipped:
        print(f"[-] Omitido (ya existe): {item.key} (usa --force para sobreescribir)")

    for error in batch.errors:
        print(f"[!] Error: {error}")

    return 1 if batch.errors else 0


if __name__ == "__main__":
    sys.exit(main())
