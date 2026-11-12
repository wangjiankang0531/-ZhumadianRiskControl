"""Bounded configuration/data reads; errors never include source values or credentials."""

import json, math, re
from pathlib import Path


class ApiError(Exception):
    def __init__(self, status, code):
        self.status, self.code = status, code
        super().__init__(code)


def pairs(items):
    output = {}
    for key, value in items:
        if key in output:
            raise ValueError("duplicate JSON member")
        output[key] = value
    return output


def loads(raw):
    return json.loads(
        raw.decode("utf-8-sig"),
        object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")),
    )


def read_json(path, limit):
    with Path(path).open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("JSON exceeds limit")
    return loads(raw)


def fields(value, allowed, required=()):
    if (
        not isinstance(value, dict)
        or set(value) - set(allowed)
        or set(required) - set(value)
    ):
        raise ValueError("invalid fields")


def text(value, maximum=256, identifier=False):
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value.encode("utf-8")) > maximum
        or re.search(r"[\x00-\x1f\x7f]", value)
        or identifier
        and re.search(r"[\x00-\x20\x7f]", value)
    ):
        raise ValueError("invalid text")
    return value


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError("invalid integer")
    return value


def boolean(value):
    if type(value) is not bool:
        raise ValueError("invalid boolean")
    return value


def strings(value, maximum, limit=256):
    if not isinstance(value, list) or len(value) > maximum:
        raise ValueError("invalid list")
    checked = [text(item, limit, True) for item in value]
    if len(set(checked)) != len(checked):
        raise ValueError("duplicate list item")
    return frozenset(checked)


def relative(base, value):
    return (base / text(value, 4096)).resolve()
