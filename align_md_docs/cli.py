import sys
import os
from importlib.metadata import version as pkg_version

from align_md_docs import tables, box_widths, box_walls, rails, arrows, pipes

ALL_CHECKS = [tables, box_widths, box_walls, rails, arrows, pipes]


def run_checks(lines):
  errors = []
  for mod in ALL_CHECKS:
    errors.extend(mod.check(lines))
  return errors


def run_fixes(lines):
  fixed = tables.fix(lines)
  fixed = box_widths.fix(fixed)
  for _ in range(3):
    prev = list(fixed)
    fixed = box_walls.fix(fixed)
    fixed = rails.fix(fixed)
    fixed = pipes.fix(fixed)
    if fixed == prev:
      break
  fixed = arrows.fix(fixed)
  return fixed


def print_help():
  print("""align-md-docs - Auto-fix alignment issues in markdown documentation files.

Checks and fixes:
  1. Tables          - pads cells so every column matches the separator row width
  2. Box widths      - ensures all lines in a box group have the same total length
  3. Rail alignment  - aligns vertically adjacent box chars to the same column
  4. Arrow alignment - aligns standalone v/^ arrows with the nearest box char above/below
  5. Pipe continuity - traces from T-junctions to detect drifted connector pipes
  6. Box walls       - verifies nested box right walls match their opening/closing borders

Usage:
  align-md-docs <path>               # auto-fix file or all .md in folder
  align-md-docs --check <path>       # detect-only, no writes
  align-md-docs --help               # show this help
  align-md-docs --version            # show version

Exit codes:
  0 - all docs aligned (or all issues auto-fixed)
  1 - unfixable issues remain (fix mode) or errors found (check mode)""")


def _collect_files(path):
  path = os.path.abspath(path)
  if os.path.isfile(path):
    return [path]
  if os.path.isdir(path):
    files = []
    for root, dirs, filenames in os.walk(path):
      for fn in sorted(filenames):
        if fn.endswith('.md'):
          files.append(os.path.join(root, fn))
    return files
  print(f"error: '{path}' is not a valid file or directory")
  sys.exit(1)


def main():
  if '--help' in sys.argv or '-h' in sys.argv:
    print_help()
    sys.exit(0)

  if '--version' in sys.argv or '-v' in sys.argv:
    print(pkg_version('align-md-docs'))
    sys.exit(0)

  check_only = '--check' in sys.argv
  args = [a for a in sys.argv[1:] if a.startswith('-') is False]

  if len(args) == 0:
    print_help()
    sys.exit(0)

  files = []
  for a in args:
    files.extend(_collect_files(a))

  total_errors = 0
  total_fixed = 0

  for fpath in sorted(files):
    with open(fpath) as f:
      lines = f.readlines()

    rel = os.path.relpath(fpath)
    errs = run_checks(lines)

    if errs:
      if check_only:
        print(f"\n{rel}:")
        for e in errs:
          print(f"  {e}")
        total_errors += len(errs)
      else:
        fixed_lines = run_fixes(lines)
        with open(fpath, 'w') as f:
          f.writelines(fixed_lines)

        with open(fpath) as f:
          recheck_lines = f.readlines()
        remaining = run_checks(recheck_lines)

        fixed_count = len(errs) - len(remaining)
        if fixed_count > 0:
          print(f"{rel}: fixed {fixed_count} issue(s)")
          total_fixed += fixed_count
        if remaining:
          print(f"\n{rel}: {len(remaining)} unfixable issue(s):")
          for e in remaining:
            print(f"  {e}")
          total_errors += len(remaining)

  if check_only:
    if total_errors == 0:
      print("ALL DOCS ALIGNED - no errors found")
    else:
      print(f"\n{total_errors} error(s) found")
      sys.exit(1)
  else:
    if total_fixed > 0:
      print(f"\n{total_fixed} issue(s) auto-fixed")
    if total_errors > 0:
      print(f"{total_errors} issue(s) could not be auto-fixed")
      sys.exit(1)
    elif total_fixed == 0:
      print("ALL DOCS ALIGNED - no errors found")
