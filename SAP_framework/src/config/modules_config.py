# 🎯 CONFIGURACIÓN DE MÓDULOS
MODULES_CONFIG = {
    "module_login": {
        "name": "Módulo Login",
        "description": "Pruebas de autenticación y conexión SAP",
        "tags": ["@login", "@auth"],
        "dependencies": [],
        "enabled": True,
        "execution_order": 1
    },
    "module_materials": {
        "name": "Módulo Materiales",
        "description": "Pruebas de transacciones MM (Materiales)",
        "tags": ["@mm01", "@mm02", "@materiales"],
        "dependencies": ["module_login"],
        "enabled": True,
        "execution_order": 2
    },
    "module_compras": {
        "name": "Módulo Compras",
        "description": "Pruebas de transacciones ME (Compras)",
        "tags": ["@me21n", "@me23n", "@compras"],
        "dependencies": ["module_login"],
        "enabled": True,
        "execution_order": 3
    },
    "module_ventas": {
        "name": "Módulo Ventas",
        "description": "Pruebas de transacciones SD (Ventas)",
        "tags": ["@va01", "@va02", "@ventas"],
        "dependencies": ["module_login"],
        "enabled": True,
        "execution_order": 4
    },
    "module_finanzas": {
        "name": "Módulo Finanzas",
        "description": "Pruebas de transacciones FI (Finanzas)",
        "tags": ["@fb01", "@fb02", "@finanzas"],
        "dependencies": ["module_login"],
        "enabled": False,
        "execution_order": 5
    }
}

def get_enabled_modules():
    """Retorna módulos habilitados en orden de ejecución"""
    enabled = {name: config for name, config in MODULES_CONFIG.items() if config['enabled']}
    return dict(sorted(enabled.items(), key=lambda x: x[1]['execution_order']))

def get_module_dependencies(module_name):
    """Retorna dependencias de un módulo"""
    return MODULES_CONFIG.get(module_name, {}).get('dependencies', [])

def validate_module_dependencies(module_name, enabled_modules):
    """Valida si un módulo puede ejecutarse"""
    dependencies = get_module_dependencies(module_name)
    missing = [dep for dep in dependencies if dep not in enabled_modules]
    return missing
