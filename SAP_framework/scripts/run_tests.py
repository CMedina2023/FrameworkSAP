import sys
import os
from pathlib import Path


def run_tests():
    """Script principal de ejecución (para compatibilidad)"""

    # Agregar el directorio actual al path
    sys.path.insert(0, str(Path.cwd()))

    print("🚀 EJECUTOR DE PRUEBAS SAP")
    print("=" * 50)
    print("1. Ejecutar módulo login")
    print("2. Ejecutar todos los módulos")
    print("3. Ver módulos disponibles")
    print("4. Salir")

    try:
        option = input("\nSeleccione opción (1-4): ").strip()

        if option == "1":
            from run_module import run_module
            success = run_module("module_login")
            return success

        elif option == "2":
            from run_all_modules import run_all_modules
            success = run_all_modules()
            return success

        elif option == "3":
            print("\n📋 MÓDULOS DISPONIBLES:")
            modules_dir = Path("modules")
            for module in modules_dir.iterdir():
                if module.is_dir() and module.name.startswith("module_"):
                    # Verificar si tiene features
                    features_dir = module / "features"
                    has_features = features_dir.exists() and any(features_dir.glob("*.feature"))
                    status = "✅" if has_features else "⚠️ "
                    print(f"{status} {module.name}")

                    if has_features:
                        for feature_file in features_dir.glob("*.feature"):
                            print(f"   📄 {feature_file.name}")
            return True

        elif option == "4":
            print("👋 Saliendo...")
            return True

        else:
            print("❌ Opción inválida")
            return False

    except KeyboardInterrupt:
        print("\n👋 Ejecución cancelada por el usuario")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
