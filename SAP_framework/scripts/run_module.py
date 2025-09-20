import argparse
import sys
import subprocess
from pathlib import Path
from src.reporting.html_reporter import HTMLReporter

def run_module(module_name, tags=None):
    """Ejecuta un módulo específico"""
    module_path = Path("modules") / module_name

    if not module_path.exists():
        print(f"❌ Módulo {module_name} no encontrado")
        print(f"📋 Módulos disponibles:")
        modules_dir = Path("modules")
        for module in modules_dir.iterdir():
            if module.is_dir():
                print(f"  - {module.name}")
        return False

    # Construir comando behave
    cmd = [
        sys.executable, "-m", "behave",
        str(module_path / "features"),
        "--no-capture",
        "--format", "json.pretty",
        "--outfile", f"reports/{module_name}_report.json",
        "--define", f"module_name={module_name}"
    ]

    # Incluir steps del módulo
    steps_dir = module_path / "steps"
    if steps_dir.exists():
        cmd.extend(["--steps", str(steps_dir)])

    if tags:
        cmd.extend(["--tags", tags])

    print(f"🚀 Ejecutando módulo: {module_name}")
    if tags:
        print(f"   Tags: {tags}")

    # Ejecutar behave
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Mostrar output
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

    # Generar reporte HTML
    try:
        reporter = HTMLReporter()
        html_report = reporter.generate_html_report(f"reports/{module_name}_report.json")
        print(f"📊 Reporte generado: {html_report}")
    except Exception as e:
        print(f"⚠️  Error generando reporte: {e}")

    return result.returncode == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ejecutar módulo específico")
    parser.add_argument("module", help="Nombre del módulo a ejecutar")
    parser.add_argument("--tags", help="Tags específicos a ejecutar")

    args = parser.parse_args()

    success = run_module(args.module, args.tags)
    sys.exit(0 if success else 1)
