import sys
from pathlib import Path
from run_module import run_module

def run_all_modules():
    """Ejecuta todos los módulos en secuencia"""

    modules_dir = Path("modules")
    modules = [d.name for d in modules_dir.iterdir() if d.is_dir() and d.name.startswith("module_")]

    print(f"🎯 Ejecutando {len(modules)} módulos...")
    results = {}

    for module in modules:
        print(f"\n{'='*50}")
        success = run_module(module)
        results[module] = success
        status = "✅" if success else "❌"
        print(f"{status} {module}: {'ÉXITO' if success else 'FALLO'}")

    # Generar reporte consolidado
    generate_summary_report(results)

    return all(results.values())


def generate_summary_report(results):
    """Genera reporte resumen de todos los módulos"""
    print("\n📊 RESUMEN DE EJECUCIÓN")
    print("=" * 50)
    for module, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {module}: {'ÉXITO' if success else 'FALLO'}")

    total = len(results)
    successes = sum(results.values())
    failures = total - successes

    print(f"\n🎯 Total módulos: {total}")
    print(f"✅ Éxitos: {successes}")
    print(f"❌ Fallos: {failures}")
    print(f"📈 Tasa de éxito: {successes/total*100:.1f}%")


if __name__ == "__main__":
    success = run_all_modules()
    sys.exit(0 if success else 1)
