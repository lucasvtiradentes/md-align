import pytest

from docalign.hints import get_hint


@pytest.mark.parametrize(
    "error, expected_hint",
    [
        (
            "L5 table col1: width=10 expected=14 (separator at L3)",
            "pad cell 4 char(s) to match separator width",
        ),
        (
            "L12 width=30, expected=34 (box group at cols 0-33)",
            "extend/shrink line by 4 char(s) to match box group",
        ),
        (
            "L8 box padding=0, expected=2",
            "adjust left-padding to 2 space(s)",
        ),
        (
            "L9 box right spacing=0, minimum=1",
            "add 1 space(s) before box wall",
        ),
        (
            "L9 box left spacing=0, minimum=1",
            "add 1 space(s) after box wall",
        ),
        (
            "L6 arrow '>' at col 15, gap=3 to box wall",
            "extend arrow dashes 3 char(s) to reach wall",
        ),
        (
            "L6 arrow '<' at col 5, gap=2 to box wall",
            "extend arrow dashes 2 char(s) to reach wall",
        ),
        (
            "L20 box \u2510 at col 30, expected col 34",
            "shift \u2510 4 column(s) right",
        ),
        (
            "L22 box \u2518 at col 36, expected col 34",
            "shift \u2518 2 column(s) left",
        ),
        (
            "L15 box wall \u2502 at col 33, expected col 34 (box \u250c at L10 col 0)",
            "shift wall 1 column(s) right",
        ),
        (
            "L7 box char at col 10, expected col 12",
            "shift box char 2 column(s) right",
        ),
        (
            "L14 arrow 'v' at col 5, expected col 7",
            "shift arrow 2 column(s) right",
        ),
        (
            "L37 arrow 'v' embedded in border at col 24",
            "extract arrow to its own line, then complete the border",
        ),
        (
            "L14 pipe '\u2502' at col 85, expected col 87",
            "shift pipe 2 column(s) right",
        ),
        (
            "L3 list desc separator: col=20 expected=35",
            "add 15 space(s) before separator dash",
        ),
        (
            "L5 def list key: col=12 expected=18",
            "add 6 space(s) before colon",
        ),
        (
            "L10 wide char '\uff0d' (U+FF0D) at col 5",
            "replace with ASCII equivalent or standard box-drawing char",
        ),
    ],
)
def test_get_hint(error, expected_hint):
    assert get_hint(error) == expected_hint


def test_unknown_pattern_returns_empty():
    assert get_hint("some unknown error message") == ""
