"""Find paths in note text that point outside the repository.

A note may name a file only by a path relative to the repository root that
never climbs out of it. Anything else names a place on one machine.
"""

import re

_BOUNDARY = r"(?:^|(?<=[\s\"'`(\[{<=,;|*:]))"

_URL = re.compile(r"\b[A-Za-z][A-Za-z0-9+.-]*://\S*")
_FILE_URL = re.compile(r"\bfile://\S*", re.I)
_RULES = (
    ("absolute path", re.compile(_BOUNDARY + r"/(?=[^\s/])", re.M)),
    ("home-relative path", re.compile(_BOUNDARY + r"~[\w.-]*/", re.M)),
    ("home variable", re.compile(r"\$HOME\b|\$\{HOME\}|%USERPROFILE%|%HOMEPATH%", re.I)),
    ("drive path", re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]")),
    ("network path", re.compile(_BOUNDARY + r"\\\\[^\s\\]+", re.M)),
    ("parent traversal", re.compile(
        r"(?:^|(?<=[\s\"'`(\[{<=,;|*:/\\]))\.\.(?=[/\\\s\"'`)\]}>,;|*]|$)", re.M)),
)


def _token_at(text, index):
    start = index
    while start > 0 and not text[start - 1].isspace():
        start -= 1
    end = index
    while end < len(text) and not text[end].isspace():
        end += 1
    return text[start:end]


def find_machine_paths(text):
    found = [("file URL", m.group(0)) for m in _FILE_URL.finditer(text)]
    blanked = _URL.sub(lambda m: " " * len(m.group(0)), text)
    for rule, pattern in _RULES:
        for match in pattern.finditer(blanked):
            found.append((rule, _token_at(text, match.start())))
    return found
