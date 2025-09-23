
MODULES_CONFIG = {
    'module_login': {
        'name': 'Módulo Login', 
        'description': 'Pruebas de autenticación SAP',
        'tags': ['@login', '@auth'],
        'dependencies': [],
        'enabled': True,
        'execution_order': 1
    }
}

def get_enabled_modules():
    return {name: config for name, config in MODULES_CONFIG.items() 
            if config['enabled']}

def get_module_dependencies(module_name):
    return MODULES_CONFIG.get(module_name, {}).get('dependencies', [])
