"""Lee grabaciones .vbs de SAP GUI Scripting y las pasa a acciones Python."""

from __future__ import annotations

import json
import re
from pathlib import Path

from tools.sap_transformer.models import RecordingError, SapAction

_LOCAL_VARIABLES = frozenset({"TU", "docs", "HUs"})
_BOILERPLATE_IF = re.compile(
    r"^if\s+(not\s+isobject|isobject\s*\(\s*wscript)\b",
    re.IGNORECASE,
)
_END_IF = re.compile(r"^end\s+if\b", re.IGNORECASE)
_SUB_START = re.compile(
    r"^(public\s+|private\s+)?(sub|function)\b",
    re.IGNORECASE,
)
_SUB_END = re.compile(r"^end\s+(sub|function)\b", re.IGNORECASE)
_FIND_BY_ID = re.compile(r"session\.findbyid\s*\(", re.IGNORECASE)
_MEMBER = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*(.*)$", re.DOTALL)
_PLACEHOLDER = re.compile(
    r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\s*\}\}"
)
_NUMBER = re.compile(r"^-?\d+(?:\.\d+)?$")
_VBS_CONSTANTS = {
    "true": "True",
    "false": "False",
    "nothing": "None",
    "empty": "None",
    "vbcrlf": '"\\r\\n"',
    "vbnewline": '"\\r\\n"',
    "vbcr": '"\\r"',
    "vblf": '"\\n"',
    "vbtab": '"\\t"',
    "vbnullstring": '""',
}


def read_recording(path: Path) -> str:
    """Abre un .vbs de SAP, que puede venir en UTF-16, UTF-8 o ANSI."""
    raw = path.read_bytes()
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16")
    if b"\x00" in raw[:400]:
        try:
            return raw.decode("utf-16")
        except UnicodeError:
            pass
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252")


def parse_vbs(text: str) -> list[SapAction]:
    """Convierte el texto de una grabación en acciones reproducibles."""
    actions: list[SapAction] = []
    skip_depth = 0
    inside_routine = False

    for line in _logical_lines(text):
        stripped = _strip_comment(line).strip()
        if not stripped:
            continue
        if inside_routine:
            if _SUB_END.match(stripped):
                inside_routine = False
            continue
        if _SUB_START.match(stripped):
            inside_routine = True
            continue
        if re.match(r"^on\s+error\b", stripped, re.IGNORECASE):
            continue
        if _BOILERPLATE_IF.match(stripped):
            if not _single_line_if(stripped):
                skip_depth += 1
            continue
        if skip_depth:
            if _END_IF.match(stripped):
                skip_depth -= 1
            continue
        if _END_IF.match(stripped):
            continue

        for statement in _split_statements(stripped):
            if statement.lower().startswith("session."):
                actions.append(_convert_session_line(statement))
            else:
                actions.append(_comment(statement))
    return actions


def _convert_session_line(line: str) -> SapAction:
    try:
        return _session_action(line)
    except RecordingError:
        return _comment(line)


def _session_action(line: str) -> SapAction:
    match = _FIND_BY_ID.search(line)
    if match is None:
        raise RecordingError("La línea no usa session.findById.")

    element_id, cursor = _read_vbs_string(line, match.end())
    cursor = _skip_spaces(line, cursor)
    if cursor >= len(line) or line[cursor] != ")":
        raise RecordingError("findById no está cerrado.")
    cursor = _skip_spaces(line, cursor + 1)
    if cursor >= len(line) or line[cursor] != ".":
        raise RecordingError("Falta la propiedad o el método.")

    member_match = _MEMBER.match(line[cursor + 1 :].strip())
    if member_match is None:
        raise RecordingError("No se reconoció la propiedad o el método.")

    member = member_match.group(1)
    tail = member_match.group(2).strip()
    element = json.dumps(element_id, ensure_ascii=False)
    target = f"session.findById({element}).{member}"

    if member.lower() == "hardcopy":
        return SapAction(kind="evidence", member=member, element_id=element_id, literal="captura")

    if tail.startswith("("):
        closing = _matching_paren(tail, 0)
        extra = tail[closing + 1 :].strip()
        if extra:
            raise RecordingError("No se convierte el encadenamiento de llamadas.")
        arguments = tail[1:closing].strip()
        return SapAction(
            kind="call",
            python=f"{target}({_render_arguments(arguments)})",
            member=member,
            element_id=element_id,
        )

    equals_at = _top_level_equals(tail)
    if equals_at is not None:
        rhs = tail[equals_at + 1 :].strip()
        literal = _plain_literal(rhs)
        return SapAction(
            kind="assign",
            python=f"{target} = {_convert_expression(rhs)}",
            member=member,
            element_id=element_id,
            literal=literal,
        )

    return SapAction(
        kind="call",
        python=f"{target}({_render_arguments(tail)})",
        member=member,
        element_id=element_id,
    )


def _render_arguments(arguments: str) -> str:
    parts = _split_commas(arguments)
    if not parts:
        return ""
    return ", ".join(_convert_expression(part) for part in parts)


def _convert_expression(expression: str) -> str:
    pieces = _split_concat(expression.strip())
    if not pieces:
        return '""'
    converted = [_convert_atom(piece) for piece in pieces]
    if len(converted) == 1:
        return converted[0]
    rendered = [
        piece if piece.startswith(('"', "'")) else f"str({piece})"
        for piece in converted
    ]
    return " + ".join(rendered)


def _convert_atom(atom: str) -> str:
    atom = atom.strip()
    if not atom:
        return '""'
    mapped = _VBS_CONSTANTS.get(atom.lower())
    if mapped is not None:
        return mapped
    if atom.startswith('"'):
        return _python_from_vbs_string(atom)
    if _NUMBER.match(atom):
        return atom
    return atom


def _python_from_vbs_string(literal: str) -> str:
    decoded = _decode_vbs_string(literal)
    placeholders = list(_PLACEHOLDER.finditer(decoded))
    if not placeholders:
        return json.dumps(decoded, ensure_ascii=False)
    if len(placeholders) == 1 and placeholders[0].span() == (0, len(decoded)):
        return _placeholder_expression(placeholders[0].group(1))

    chunks: list[str] = []
    cursor = 0
    for placeholder in placeholders:
        if placeholder.start() > cursor:
            chunks.append(json.dumps(decoded[cursor : placeholder.start()], ensure_ascii=False))
        chunks.append(f"str({_placeholder_expression(placeholder.group(1))})")
        cursor = placeholder.end()
    if cursor < len(decoded):
        chunks.append(json.dumps(decoded[cursor:], ensure_ascii=False))
    return " + ".join(chunks)


def _placeholder_expression(name: str) -> str:
    if "." not in name:
        if name in _LOCAL_VARIABLES:
            return name
        return f'kwargs.get("{name}")'
    head, *rest = name.split(".")
    expression = f'(kwargs.get("{head}") or {{}})'
    for part in rest:
        expression += f'.get("{part}")'
    return expression


def _plain_literal(expression: str) -> str | None:
    expression = expression.strip()
    if not expression.startswith('"'):
        return None
    if _split_concat(expression) != [expression]:
        return None
    try:
        decoded = _decode_vbs_string(expression)
    except RecordingError:
        return None
    if _PLACEHOLDER.search(decoded):
        return None
    return decoded


def _decode_vbs_string(literal: str) -> str:
    if not literal.startswith('"'):
        raise RecordingError("Se esperaba una cadena VBS.")
    chars: list[str] = []
    index = 1
    while index < len(literal):
        if literal[index] == '"':
            if index + 1 < len(literal) and literal[index + 1] == '"':
                chars.append('"')
                index += 2
                continue
            return "".join(chars)
        chars.append(literal[index])
        index += 1
    raise RecordingError("Cadena VBS sin cerrar.")


def _read_vbs_string(text: str, start: int) -> tuple[str, int]:
    start = _skip_spaces(text, start)
    if start >= len(text) or text[start] != '"':
        raise RecordingError("Se esperaba el id del control SAP.")
    chars: list[str] = []
    index = start + 1
    while index < len(text):
        if text[index] == '"':
            if index + 1 < len(text) and text[index + 1] == '"':
                chars.append('"')
                index += 2
                continue
            return "".join(chars), index + 1
        chars.append(text[index])
        index += 1
    raise RecordingError("El id del control SAP no cierra la cadena.")


def _logical_lines(text: str) -> list[str]:
    logical: list[str] = []
    buffer = ""
    for physical in text.splitlines():
        buffer = f"{buffer} {physical.strip()}".strip() if buffer else physical
        if _continues(buffer):
            buffer = buffer.rstrip()[:-1].rstrip()
            continue
        logical.append(buffer)
        buffer = ""
    if buffer:
        logical.append(buffer)
    return logical


def _continues(line: str) -> bool:
    in_string = False
    index = 0
    while index < len(line):
        if line[index] == '"':
            if in_string and index + 1 < len(line) and line[index + 1] == '"':
                index += 2
                continue
            in_string = not in_string
        index += 1
    return not in_string and line.rstrip().endswith("_")


def _strip_comment(line: str) -> str:
    if re.match(r"^\s*rem\b", line, re.IGNORECASE):
        return ""
    in_string = False
    index = 0
    while index < len(line):
        char = line[index]
        if char == '"':
            if in_string and index + 1 < len(line) and line[index + 1] == '"':
                index += 2
                continue
            in_string = not in_string
            index += 1
            continue
        if char == "'" and not in_string:
            return line[:index]
        index += 1
    return line


def _split_statements(line: str) -> list[str]:
    return [part for part in _split_outside_strings(line, ":") if part.strip()]


def _split_concat(expression: str) -> list[str]:
    return _split_outside_strings(expression, "&")


def _split_commas(arguments: str) -> list[str]:
    if not arguments.strip():
        return []
    return _split_outside_strings(arguments, ",")


def _split_outside_strings(text: str, separator: str) -> list[str]:
    parts: list[str] = []
    buffer: list[str] = []
    in_string = False
    depth = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char == '"':
            buffer.append(char)
            if in_string and index + 1 < len(text) and text[index + 1] == '"':
                buffer.append('"')
                index += 2
                continue
            in_string = not in_string
            index += 1
            continue
        if not in_string and char == "(":
            depth += 1
        elif not in_string and char == ")":
            depth -= 1
        if char == separator and not in_string and depth == 0:
            parts.append("".join(buffer).strip())
            buffer = []
            index += 1
            continue
        buffer.append(char)
        index += 1
    parts.append("".join(buffer).strip())
    return parts


def _top_level_equals(text: str) -> int | None:
    in_string = False
    index = 0
    while index < len(text):
        char = text[index]
        if char == '"':
            if in_string and index + 1 < len(text) and text[index + 1] == '"':
                index += 2
                continue
            in_string = not in_string
            index += 1
            continue
        if char == "=" and not in_string:
            return index
        index += 1
    return None


def _matching_paren(text: str, opening: int) -> int:
    depth = 0
    in_string = False
    index = opening
    while index < len(text):
        char = text[index]
        if char == '"':
            if in_string and index + 1 < len(text) and text[index + 1] == '"':
                index += 2
                continue
            in_string = not in_string
            index += 1
            continue
        if not in_string and char == "(":
            depth += 1
        elif not in_string and char == ")":
            depth -= 1
            if depth == 0:
                return index
        index += 1
    raise RecordingError("Paréntesis sin cerrar.")


def _skip_spaces(text: str, index: int) -> int:
    while index < len(text) and text[index].isspace():
        index += 1
    return index


def _single_line_if(line: str) -> bool:
    parts = re.split(r"\bthen\b", line, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) < 2:
        return False
    body = parts[1].strip()
    return bool(body) and _END_IF.match(body) is None


def _comment(line: str) -> SapAction:
    cleaned = " ".join(line.strip().split())
    return SapAction(kind="comment", literal=cleaned)
