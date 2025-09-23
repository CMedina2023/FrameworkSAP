import sys
import json
from pathlib import Path
from datetime import datetime
import subprocess  # Agregado: Import necesario para subprocess en run_module

def run_all_modules():
    """Ejecuta todos los módulos en secuencia con reportes modulares"""

    modules_dir = Path("modules")
    modules = [d.name for d in modules_dir.iterdir() if d.is_dir() and d.name.startswith("module_")]

    enabled_modules = get_enabled_modules(modules)

    print(f"🎯 Ejecutando {len(enabled_modules)} módulos habilitados...")
    results = {}
    all_test_cases = []

    for module in enabled_modules:
        print(f"\n{'=' * 60}")
        print(f"🚀 EJECUTANDO: {module}")
        print('=' * 60)

        success = run_module(module)
        results[module] = success

        module_data = collect_module_data(module)
        if module_data:
            all_test_cases.extend(module_data)

        status = "✅" if success else "❌"
        print(f"{status} {module}: {'ÉXITO' if success else 'FALLO'}")

    generate_consolidated_report(results, all_test_cases)

    return all(results.values())


def get_enabled_modules(available_modules):
    """Retorna módulos habilitados para ejecución"""
    try:
        from src.config.modules_config import get_enabled_modules
        enabled_config = get_enabled_modules()
        enabled = [mod for mod in available_modules if mod in enabled_config]
        return enabled
    except ImportError:
        print("⚠️  No se pudo cargar configuración de módulos, ejecutando todos")
        return available_modules


def run_module(module_name):
    """Función run_module importada o definida aquí"""
    try:
        # Intentar importar del script existente
        from run_module import run_module as run_module_func
        return run_module_func(module_name)
    except ImportError:
        # Definición alternativa si no se puede importar
        module_path = Path("modules") / module_name

        if not module_path.exists():
            print(f"❌ Módulo {module_name} no encontrado")
            return False

        # Configuración de reportes modulares
        module_report_dir = module_path / "reports"
        module_report_dir.mkdir(exist_ok=True)
        json_report_path = module_report_dir / f"{module_name}_report.json"

        cmd = [
            sys.executable, "-m", "behave",
            str(module_path / "features"),
            "--no-capture",
            "--format", "json.pretty",
            "--outfile", str(json_report_path)
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return result.returncode == 0
        except:
            return False


def collect_module_data(module_name):
    """Colecta datos de reporte del módulo"""
    module_report_path = Path("modules") / module_name / "reports" / f"{module_name}_report.json"

    if module_report_path.exists():
        try:
            with open(module_report_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Agregar información del módulo a cada test case
                for feature in data:
                    for element in feature.get('elements', []):
                        if 'module' not in element:
                            element['module'] = module_name
                return data
        except Exception as e:
            print(f"⚠️  Error leyendo reporte de {module_name}: {e}")

    return []


def generate_consolidated_report(results, all_test_cases):
    """Genera reporte consolidado de todos los módulos"""
    print("\n📊 RESUMEN DE EJECUCIÓN")
    print("=" * 60)

    total_modules = len(results)
    successful_modules = sum(results.values())
    failed_modules = total_modules - successful_modules

    for module, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {module}: {'ÉXITO' if success else 'FALLO'}")

    print(f"\n🎯 TOTAL MÓDULOS: {total_modules}")
    print(f"✅ ÉXITOS: {successful_modules}")
    print(f"❌ FALLOS: {failed_modules}")

    if total_modules > 0:
        success_rate = (successful_modules / total_modules) * 100
        print(f"📈 TASA DE ÉXITO: {success_rate:.1f}%")

    # ✅ NUEVO: Generar reporte HTML consolidado
    try:
        from src.reporting.html_reporter import HTMLReporter

        # Parsear los test_cases crudos de Behave
        all_parsed_test_cases = []
        total_duration = 0
        reporter = HTMLReporter()  # Instancia temporal para usar métodos de parsing
        for feature in all_test_cases:  # all_test_cases es lista de features de JSON Behave
            if 'elements' in feature:
                for element in feature['elements']:
                    if element['type'] == 'scenario':
                        scenario_analysis = reporter._analyze_scenario_detailed(element)
                        all_parsed_test_cases.append(scenario_analysis)
                        total_duration += scenario_analysis['duration']

        # Crear datos consolidados
        consolidated_data = {
            'total_modules': total_modules,
            'successful_modules': successful_modules,
            'failed_modules': failed_modules,
            'success_rate': success_rate if total_modules > 0 else 0,
            'test_cases': all_parsed_test_cases,  # Ahora parseados
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'execution_summary': results,
            'total_duration': round(total_duration, 2)  # Agregado para consistencia
        }

        # Generar reporte
        reporter = HTMLReporter("reports/consolidated")
        report_path = reporter.generate_consolidated_report(consolidated_data)

        if report_path:
            print(f"📋 Reporte consolidado generado: {report_path}")
        else:
            print("⚠️  No se pudo generar reporte consolidado")

    except Exception as e:
        print(f"⚠️  Error generando reporte consolidado: {e}")


if __name__ == "__main__":
    success = run_all_modules()
    sys.exit(0 if success else 1)