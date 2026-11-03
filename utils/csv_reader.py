import csv
import os


def resolve_env(value):
    """Si el valor comienza con 'ENV:', resuelve la variable de entorno correspondiente."""
    if isinstance(value, str) and value.startswith("ENV:"):
        env_key = value.split("ENV:")[1].strip()
        return os.getenv(env_key, value)
    return value


def find_expected_result(test_identifier):
    """Busca dinámicamente el resultado esperado en cualquier expected_result.csv dentro de apps/."""
    if not test_identifier:
        return None
    import re
    id_match = re.search(r"ICD_\d+", test_identifier, re.IGNORECASE)
    if not id_match:
        return None
    matched_token = id_match.group(0).upper()
    test_id = f"ACC_{matched_token}"

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    apps_dir = os.path.join(base_dir, "apps")
    if os.path.exists(apps_dir):
        for app_name in os.listdir(apps_dir):
            app_path = os.path.join(apps_dir, app_name)
            if os.path.isdir(app_path):
                csv_path = os.path.join(app_path, "data", "expected_result.csv")
                if os.path.exists(csv_path):
                    try:
                        with open(csv_path, "r", encoding="utf-8") as f:
                            reader = csv.reader(f)
                            next(reader, None)
                            for fila in reader:
                                if len(fila) >= 2:
                                    f_id = fila[0].strip().upper()
                                    if f_id == test_id or f_id.endswith(matched_token) or f_id == matched_token:
                                        return fila[1].strip()
                    except Exception:
                        pass
    return None


def cargar_datos_csv(file_path):
    datos = []
    if not os.path.exists(file_path):
        print(f"[!] Error: El archivo {file_path} no existe.")
        return datos

    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return datos

        for row in reader:
            if row:
                procesada = [resolve_env(valor) for valor in row]
                datos.append(tuple(procesada))
    return datos

