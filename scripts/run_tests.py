import sys
import os
import subprocess
from pathlib import Path
import argparse


def run_test():
    """Script principal de ejecución de pruebas (para compatibilidad)"""

    # Configurar path
    sys.path.insert(0, str(Path.cwd()))

    parser = argparse.ArgumentParser(description="Ejecutor de pruebas SAP")
    parser.add_argument("--module", help="Módulo específico a ejecutar")
    parser.add_argument("--tags", help="Tags específicos a ejecutar")
    parser.add_argument("--all", action="store_true", help="Ejecutar todos los módulos")
    parser.add_argument("--list", action="store_true", help="Listar módulos disponibles")

    args = parser.parse_args()

    print("🚀 EJECUTOR DE PRUEBAS SAP FRAMEWORK")
    print("=" * 50)

    try:
        if args.list:
            return list_modules()
        elif args.all:
            return run_all_modules()
        elif args.module:
            return run_single_module(args.module, args.tags)
        else:
            return interactive_mode()

    except KeyboardInterrupt:
        print("\n👋 Ejecución cancelada por el usuario")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def list_modules():
    """Lista todos los módulos disponibles"""
    print("\n📋 MÓDULOS DISPONIBLES:")
    print("-" * 40)

    modules_dir = Path("modules")
    if not modules_dir.exists():
        print("❌ No se encontró la carpeta 'modules'")
        return False

    modules_found = False
    for module in modules_dir.iterdir():
        if module.is_dir() and module.name.startswith("module_"):
            modules_found = True
            features_dir = module / "features"
            has_features = features_dir.exists() and any(features_dir.glob("*.feature"))

            status = "✅" if has_features else "⚠️ "
            print(f"{status} {module.name}")

            if has_features:
                for feature_file in features_dir.glob("*.feature"):
                    print(f"   📄 {feature_file.name}")

    if not modules_found:
        print("❌ No se encontraron módulos (module_*)")
        return False

    return True


def run_single_module(module_name, tags=None):
    """Ejecuta un módulo específico"""
    print(f"\n🎯 EJECUTANDO MÓDULO: {module_name}")
    if tags:
        print(f"   Tags: {tags}")
    print("-" * 40)

    module_path = Path("modules") / module_name
    if not module_path.exists():
        print(f"❌ Módulo '{module_name}' no encontrado")
        return False

    # Configuración de reportes modulares
    module_report_dir = module_path / "reports"
    module_report_dir.mkdir(exist_ok=True)
    json_report_path = module_report_dir / f"{module_name}_report.json"
    html_report_dir = module_report_dir / "html-reports"

    # Construir comando behave
    cmd = [
        sys.executable, "-m", "behave",
        str(module_path / "features"),
        "--no-capture",
        "--format", "json.pretty",
        "--outfile", str(json_report_path)
    ]

    if tags:
        cmd.extend(["--tags", tags])

    try:
        print("📋 Ejecutando pruebas...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        # Mostrar output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)

        # Generar reporte HTML
        if result.returncode == 0:
            try:
                from src.reporting.html_reporter import HTMLReporter
                reporter = HTMLReporter(str(html_report_dir))
                html_report = reporter.generate_html_report(str(json_report_path))
                if html_report:
                    print(f"📊 Reporte HTML generado: {html_report}")
            except Exception as e:
                print(f"⚠️ Error generando reporte HTML: {e}")

        success = result.returncode == 0
        status = "✅ ÉXITO" if success else "❌ FALLO"
        print(f"\n{status} - Módulo: {module_name}")

        return success

    except subprocess.TimeoutExpired:
        print("❌ Timeout: Las pruebas tomaron demasiado tiempo")
        return False
    except Exception as e:
        print(f"❌ Error ejecutando pruebas: {e}")
        return False


def run_all_modules():
    """Ejecuta todos los módulos disponibles"""
    print("\n🎯 EJECUTANDO TODOS LOS MÓDULOS")
    print("-" * 40)

    modules_dir = Path("modules")
    if not modules_dir.exists():
        print("❌ No se encontró la carpeta 'modules'")
        return False

    modules = [d.name for d in modules_dir.iterdir() if d.is_dir() and d.name.startswith("module_")]

    if not modules:
        print("❌ No se encontraron módulos para ejecutar")
        return False

    print(f"📋 Módulos a ejecutar: {', '.join(modules)}")

    results = {}
    for module in modules:
        print(f"\n{'=' * 50}")
        print(f"🚀 EJECUTANDO: {module}")
        success = run_single_module(module)
        results[module] = success
        status = "✅" if success else "❌"
        print(f"{status} {module}: {'ÉXITO' if success else 'FALLO'}")

    # Resumen final
    print("\n📊 RESUMEN FINAL")
    print("=" * 50)
    total = len(results)
    successes = sum(results.values())
    failures = total - successes

    for module, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {module}")

    print(f"\n🎯 TOTAL: {total} módulos")
    print(f"✅ ÉXITOS: {successes}")
    print(f"❌ FALLOS: {failures}")

    if total > 0:
        success_rate = (successes / total) * 100
        print(f"📈 TASA DE ÉXITO: {success_rate:.1f}%")

    return successes == total  # True solo si todos pasaron


def interactive_mode():
    """Modo interactivo para selección manual"""
    print("🔧 MODO INTERACTIVO")
    print("1. Ejecutar módulo login")
    print("2. Ejecutar todos los módulos")
    print("3. Listar módulos disponibles")
    print("4. Salir")

    try:
        option = input("\nSeleccione opción (1-4): ").strip()

        if option == "1":
            return run_single_module("module_login")
        elif option == "2":
            return run_all_modules()
        elif option == "3":
            return list_modules()
        elif option == "4":
            print("👋 Saliendo...")
            return True
        else:
            print("❌ Opción inválida")
            return False

    except KeyboardInterrupt:
        print("\n👋 Ejecución cancelada")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)



