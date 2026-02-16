import difflib
import glob as globmod
import os
import sys
from importlib.metadata import version as pkg_version

from mdalign.checks import (
    arrows,
    box_padding,
    box_spacing,
    box_walls,
    box_widths,
    def_lists,
    horiz_arrows,
    list_descs,
    pipes,
    rails,
    tables,
    wide_chars,
)
from mdalign.hints import get_hint

CHECK_MODULES = {
    "tables": tables,
    "box-widths": box_widths,
    "box-padding": box_padding,
    "box-spacing": box_spacing,
    "horiz-arrows": horiz_arrows,
    "box-walls": box_walls,
    "rails": rails,
    "arrows": arrows,
    "pipes": pipes,
    "list-descs": list_descs,
    "def-lists": def_lists,
    "wide-chars": wide_chars,
}

ALL_CHECKS = list(CHECK_MODULES.values())


def run_checks(lines, ignored=None):
    ignored = ignored or set()
    errors = []
    for name, mod in CHECK_MODULES.items():
        if name not in ignored:
            errors.extend(mod.check(lines))
    return errors


def run_fixes(lines, ignored=None):
    ignored = ignored or set()

    def _apply(name, fn, data):
        return fn(data) if name not in ignored else data

    fixed = _apply("tables", tables.fix, lines)
    fixed = _apply("box-widths", box_widths.fix, fixed)
    fixed = _apply("box-padding", box_padding.fix, fixed)
    fixed = _apply("horiz-arrows", horiz_arrows.fix, fixed)
    for _ in range(3):
        prev = list(fixed)
        fixed = _apply("box-spacing", box_spacing.fix, fixed)
        fixed = _apply("box-widths", box_widths.fix, fixed)
        fixed = _apply("box-walls", box_walls.fix, fixed)
        fixed = _apply("rails", rails.fix, fixed)
        fixed = _apply("pipes", pipes.fix, fixed)
        if fixed == prev:
            break
    fixed = _apply("arrows", arrows.fix, fixed)
    fixed = _apply("list-descs", list_descs.fix, fixed)
    fixed = _apply("def-lists", def_lists.fix, fixed)
    fixed = _apply("wide-chars", wide_chars.fix, fixed)
    fixed = _strip_box_trailing_whitespace(fixed)
    return fixed


BOX_CHARS_SET = set("│┌└├┐┘┤┬┴┼─")


def _strip_box_trailing_whitespace(lines):
    result = []
    in_code = False
    for line in lines:
        raw = line.rstrip("\n")
        if raw.strip().startswith("```"):
            in_code = not in_code
            result.append(line)
            continue
        if in_code:
            box_count = sum(1 for c in raw if c in BOX_CHARS_SET)
            if box_count >= 2:
                stripped = raw.rstrip()
                if stripped != raw:
                    result.append(stripped + "\n" if line.endswith("\n") else stripped)
                    continue
        result.append(line)
    return result


def print_help():
    print("""mdalign - Auto-fix alignment issues in markdown documentation files.

Checks and fixes:
  1. Tables           - pads cells so every column matches the separator row width
  2. Box widths       - ensures all lines in a box group have the same total length
  3. Box padding      - normalizes left-padding of content lines inside boxes
  4. Box spacing      - ensures at least 1 space between content and box walls
  5. Horiz arrows     - closes gaps between arrow tips and box walls
  6. Rail alignment   - aligns vertically adjacent box chars to the same column
  7. Arrow alignment  - aligns standalone v/^ arrows; detects embedded arrows in borders
  8. Pipe continuity  - traces from T-junctions to detect drifted connector pipes
  9. Box walls        - verifies nested box right walls match their opening/closing borders
 10. List descs       - aligns the separator dash in list item descriptions
 11. Def lists        - aligns the colon separator in key: value list items
 12. Wide chars       - detects ambiguous/double-width Unicode chars in code blocks

Usage:
  mdalign <path>                        # check-only (default)
  mdalign --check <path>                # explicit check-only
  mdalign --fix <path>                  # auto-fix files in place
  mdalign --diff <path>                 # show unified diff of changes
  mdalign --verbose <path>              # show actionable hints with each error
  mdalign --ignore tables,pipes <path>  # skip specific checks
  mdalign --help                        # show this help
  mdalign --version                     # show version

Paths can be files, directories, or glob patterns (e.g. "docs/**/*.md").

Check names for --ignore:
  tables, box-widths, box-padding, box-spacing, horiz-arrows,
  box-walls, rails, arrows, pipes, list-descs, def-lists, wide-chars

Exit codes:
  0 - all docs aligned (or all issues auto-fixed)
  1 - errors found (check mode), unfixable issues remain (fix mode), or diff non-empty (diff mode)""")


_GLOB_CHARS = set("*?[")


def _collect_files(path):
    if any(c in path for c in _GLOB_CHARS):
        matches = globmod.glob(path, recursive=True)
        files = sorted(f for f in matches if f.endswith(".md") and os.path.isfile(f))
        if not files:
            print(f"error: no .md files matched pattern '{path}'")
            sys.exit(1)
        return files

    path = os.path.abspath(path)
    if os.path.isfile(path):
        return [path]
    if os.path.isdir(path):
        files = []
        for root, dirs, filenames in os.walk(path):
            for fn in sorted(filenames):
                if fn.endswith(".md"):
                    files.append(os.path.join(root, fn))
        return files
    print(f"error: '{path}' is not a valid file or directory")
    sys.exit(1)


def _fmt(error, verbose):
    if not verbose:
        return error
    hint = get_hint(error)
    return f"{error} \u2192 {hint}" if hint else error


def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print_help()
        sys.exit(0)

    if "--version" in sys.argv or "-v" in sys.argv:
        print(pkg_version("mdalign"))
        sys.exit(0)

    fix_mode = "--fix" in sys.argv
    diff_mode = "--diff" in sys.argv
    verbose = "--verbose" in sys.argv

    ignored = set()
    argv = sys.argv[1:]
    positional = []
    i = 0
    while i < len(argv):
        if argv[i] == "--ignore" and i + 1 < len(argv):
            names = [n.strip() for n in argv[i + 1].split(",") if n.strip()]
            invalid = [n for n in names if n not in CHECK_MODULES]
            if invalid:
                print(f"error: unknown check(s): {', '.join(invalid)}")
                print(f"valid checks: {', '.join(CHECK_MODULES)}")
                sys.exit(1)
            ignored.update(names)
            i += 2
            continue
        if not argv[i].startswith("-"):
            positional.append(argv[i])
        i += 1
    args = positional

    if len(args) == 0:
        print_help()
        sys.exit(0)

    files = []
    for a in args:
        files.extend(_collect_files(a))

    total_errors = 0
    total_fixed = 0
    has_diff = False

    for fpath in sorted(files):
        with open(fpath) as f:
            lines = f.readlines()

        rel = os.path.relpath(fpath)
        errs = run_checks(lines, ignored)

        if not errs:
            continue

        if diff_mode:
            fixed_lines = run_fixes(lines, ignored)
            diff = difflib.unified_diff(lines, fixed_lines, fromfile=rel, tofile=rel)
            diff_text = "".join(diff)
            if diff_text:
                print(diff_text, end="" if diff_text.endswith("\n") else "\n")
                has_diff = True
        elif fix_mode:
            fixed_lines = run_fixes(lines, ignored)
            with open(fpath, "w") as f:
                f.writelines(fixed_lines)

            with open(fpath) as f:
                recheck_lines = f.readlines()
            remaining = run_checks(recheck_lines, ignored)

            fixed_count = len(errs) - len(remaining)
            if fixed_count > 0:
                print(f"{rel}: fixed {fixed_count} issue(s)")
                total_fixed += fixed_count
            if remaining:
                print(f"\n{rel}: {len(remaining)} unfixable issue(s):")
                for e in remaining:
                    print(f"  {_fmt(e, verbose)}")
                total_errors += len(remaining)
        else:
            print(f"\n{rel}:")
            for e in errs:
                print(f"  {_fmt(e, verbose)}")
            total_errors += len(errs)

    if diff_mode:
        if has_diff:
            sys.exit(1)
        else:
            print("ALL DOCS ALIGNED - no diff")
    elif fix_mode:
        if total_fixed > 0:
            print(f"\n{total_fixed} issue(s) auto-fixed")
        if total_errors > 0:
            print(f"{total_errors} issue(s) could not be auto-fixed")
            sys.exit(1)
        elif total_fixed == 0:
            print("ALL DOCS ALIGNED - no errors found")
    else:
        if total_errors == 0:
            print("ALL DOCS ALIGNED - no errors found")
        else:
            print(f"\n{total_errors} error(s) found")
            sys.exit(1)
