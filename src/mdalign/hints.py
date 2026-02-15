import re

_PATTERNS = [
    (
        re.compile(r"table col\d+: width=(\d+) expected=(\d+)"),
        lambda m: f"pad cell {abs(int(m.group(2)) - int(m.group(1)))} char(s) to match separator width",
    ),
    (
        re.compile(r"width=(\d+), expected=(\d+) \(box group"),
        lambda m: f"extend/shrink line by {abs(int(m.group(2)) - int(m.group(1)))} char(s) to match box group",
    ),
    (
        re.compile(r"box padding=(\d+), expected=(\d+)"),
        lambda m: f"adjust left-padding to {m.group(2)} space(s)",
    ),
    (
        re.compile(r"box right spacing=(\d+), minimum=(\d+)"),
        lambda m: f"add {int(m.group(2)) - int(m.group(1))} space(s) before box wall",
    ),
    (
        re.compile(r"arrow '>' at col \d+, gap=(\d+) to box wall"),
        lambda m: f"extend arrow dashes {m.group(1)} char(s) to reach wall",
    ),
    (
        re.compile(r"arrow '<' at col \d+, gap=(\d+) to box wall"),
        lambda m: f"extend arrow dashes {m.group(1)} char(s) to reach wall",
    ),
    (
        re.compile(r"box ([└┐┘]) at col (\d+), expected col (\d+)"),
        lambda m: _shift_hint(m.group(1), int(m.group(2)), int(m.group(3))),
    ),
    (
        re.compile(r"box wall │ at col (\d+), expected col (\d+)"),
        lambda m: _shift_hint("wall", int(m.group(1)), int(m.group(2))),
    ),
    (
        re.compile(r"box char at col (\d+), expected col (\d+)"),
        lambda m: _shift_hint("box char", int(m.group(1)), int(m.group(2))),
    ),
    (
        re.compile(r"arrow '([^']+)' at col (\d+), expected col (\d+)"),
        lambda m: _shift_hint("arrow", int(m.group(2)), int(m.group(3))),
    ),
    (
        re.compile(r"arrow '[^']+' embedded in border at col"),
        lambda _: "extract arrow to its own line, then complete the border",
    ),
    (
        re.compile(r"pipe '│' at col (\d+), expected col (\d+)"),
        lambda m: _shift_hint("pipe", int(m.group(1)), int(m.group(2))),
    ),
    (
        re.compile(r"list desc separator: col=(\d+) expected=(\d+)"),
        lambda m: f"add {int(m.group(2)) - int(m.group(1))} space(s) before separator dash",
    ),
    (
        re.compile(r"def list key: col=(\d+) expected=(\d+)"),
        lambda m: f"add {int(m.group(2)) - int(m.group(1))} space(s) before colon",
    ),
    (
        re.compile(r"wide char '.+' \(U\+[0-9A-F]+\) at col"),
        lambda _: "replace with ASCII equivalent or standard box-drawing char",
    ),
]


def _shift_hint(name, actual, expected):
    delta = abs(expected - actual)
    direction = "right" if expected > actual else "left"
    return f"shift {name} {delta} column(s) {direction}"


def get_hint(error):
    for pattern, hint_fn in _PATTERNS:
        m = pattern.search(error)
        if m:
            return hint_fn(m)
    return ""
