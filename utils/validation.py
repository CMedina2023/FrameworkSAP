from typing import Any, Iterable


class ValidationError(AssertionError):
    """
    Error de validación funcional.
    Hereda de AssertionError para que el framework
    marque el caso como FALLIDO automáticamente.
    """
    pass


# -------------------------------------------------
# Validaciones básicas
# -------------------------------------------------

def assert_not_none(value: Any, message: str):
    """
    Valida que el valor no sea None.
    """
    if value is None:
        raise ValidationError(message)


def assert_not_empty(value: Any, message: str):
    """
    Valida que el valor no sea vacío.
    Aplica para strings, listas, diccionarios, etc.
    """
    if value is None:
        raise ValidationError(message)

    if isinstance(value, (str, list, dict, tuple, set)) and len(value) == 0:
        raise ValidationError(message)


def assert_true(condition: bool, message: str):
    """
    Valida que la condición sea True.
    """
    if not condition:
        raise ValidationError(message)


def assert_false(condition: bool, message: str):
    """
    Valida que la condición sea False.
    """
    if condition:
        raise ValidationError(message)


# -------------------------------------------------
# Validaciones de igualdad
# -------------------------------------------------

def assert_equals(actual: Any, expected: Any, message: str):
    """
    Valida igualdad exacta.
    """
    if actual != expected:
        raise ValidationError(
            f"{message} | Esperado: {expected} | Actual: {actual}"
        )


def assert_not_equals(actual: Any, expected: Any, message: str):
    """
    Valida que los valores no sean iguales.
    """
    if actual == expected:
        raise ValidationError(
            f"{message} | Valor no esperado: {actual}"
        )


# -------------------------------------------------
# Validaciones de texto
# -------------------------------------------------

def assert_contains(text: str, expected: str, message: str):
    """
    Valida que el texto contenga una cadena esperada.
    """
    if text is None:
        raise ValidationError(message)

    if expected not in text:
        raise ValidationError(
            f"{message} | No contiene: '{expected}' | Texto: '{text}'"
        )


def assert_not_contains(text: str, unexpected: str, message: str):
    """
    Valida que el texto NO contenga una cadena.
    """
    if text is None:
        return  # texto vacío no contiene nada

    if unexpected in text:
        raise ValidationError(
            f"{message} | Contiene valor no esperado: '{unexpected}'"
        )


# -------------------------------------------------
# Validaciones de colecciones
# -------------------------------------------------

def assert_list_not_empty(values: Iterable, message: str):
    """
    Valida que una lista/iterable tenga elementos.
    """
    if values is None:
        raise ValidationError(message)

    if not list(values):
        raise ValidationError(message)


def assert_in(value: Any, collection: Iterable, message: str):
    """
    Valida que un valor exista dentro de una colección.
    """
    if collection is None or value not in collection:
        raise ValidationError(
            f"{message} | Valor '{value}' no encontrado"
        )


def assert_all_not_empty(values: Iterable, message: str):
    """
    Valida que todos los elementos de una colección
    sean no vacíos.
    """
    if values is None:
        raise ValidationError(message)

    for idx, v in enumerate(values):
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValidationError(
                f"{message} | Elemento inválido en posición {idx}: {v}"
            )


# -------------------------------------------------
# Helpers SAP-friendly (opcional)
# -------------------------------------------------

def assert_sap_status_ok(status_text: str):
    """
    Validación genérica para status bar de SAP.
    Marca error si contiene palabras típicas.
    """
    if not status_text:
        return

    lowered = status_text.lower()
    error_keywords = ["error", "incorrecto", "no permitido", "falló", "fallo"]

    for word in error_keywords:
        if word in lowered:
            raise ValidationError(f"Error SAP detectado: {status_text}")
