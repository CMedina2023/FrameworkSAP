
MODULES_CONFIG = {
    "module_login": {
        "name": "Modulo Login",
        "description": "Pruebas de autenticacion SAP",
        "tags": ["@login", "@auth"],
        "dependencies": [],
        "enabled": True,
        "execution_order": 1
    },
    "module_materials": {
        "name": "Modulo Materiales",
        "description": "Pruebas de transacciones MM",
        "tags": ["@mm01", "@materiales"],
        "dependencies": ["module_login"],
        "enabled": True,
        "execution_order": 2
    }
}

def get_enabled_modules():
    return {name: config for name, config in MODULES_CONFIG.items()
            if config['enabled']}

def get_module_dependencies(module_name):
    return MODULES_CONFIG.get(module_name, {}).get('dependencies', [])
