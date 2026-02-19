# Concepts

Core domain concepts used throughout docalign.

## Box-drawing characters

Unicode characters used to draw diagram borders and connectors:

| Char | Name          | Role                            |
|------|---------------|---------------------------------|
| ┌    | top-left      | opens a box top border          |
| ┐    | top-right     | closes a box top border         |
| └    | bottom-left   | opens a box bottom border       |
| ┘    | bottom-right  | closes a box bottom border      |
| ├    | left-tee      | left wall junction              |
| ┤    | right-tee     | right wall junction             |
| ┬    | top-tee       | top T-junction (pipe origin)    |
| ┴    | bottom-tee    | bottom T-junction (pipe origin) |
| │    | vertical pipe | vertical connector / wall       |
| ┼    | cross         | crossing junction               |
| ─    | horizontal    | horizontal border segment       |

These are defined in `utils.py` as `BOX_CHARS = set("│┌└├┐┘┤┬┴┼")`.

## Table column alignment

Markdown tables use `|` delimiters. A separator row (containing only dashes and pipes) defines column widths. All data rows must match these widths. Mismatched widths cause visual misalignment.

```
Before fix:                After fix:
| Name  | Age |  | Name  | Age |
|-------|-----|--|-------|-----|
| Alice | 30  |  | Alice | 30  |
```

## Box groups

A box group is a set of consecutive lines within a code block that all contain box-drawing characters. Lines without box chars act as group boundaries. Each group is processed independently.

## Box width normalization

All lines in a box group sharing the same first and last box-char column should have equal total length. The "most common length" heuristic picks the target. Lines are padded or trimmed by adjusting trailing dashes (borders) or spaces (content lines).

```
Before:                    After:
┌──────────┐               ┌──────────┐
│ content  │               │ content  │
└──────────┘               └──────────┘
```

## Rails

A rail is a vertical alignment track through a box group. Box characters that appear in consecutive lines at the same (or near-same) column form a rail. Drifted characters (off by a few columns) are detected and corrected to match the dominant column.

Two detection phases:
- By-index:  groups lines with the same number of box chars, clusters by position similarity
- By-column: clusters all box chars by column proximity (threshold: 3 columns)

Rail requirements: minimum 2 entries, maximum 1-line gap between entries.

## Arrow alignment

Standalone `v` and `^` characters (not embedded in words) act as directional arrows. They should align vertically with the nearest box character above (for `v`) or below (for `^`). A 2-column tolerance is used for searching.

```
Before:          After:
┌────┐           ┌────┐
v                v
```

## Embedded arrows

Arrows embedded directly into borders are flagged as unfixable issues:
- `v`/`^` inside horizontal borders (adjacent to `─`, e.g. `┌────v──────┐`)
- `>`/`<` inside vertical borders (with `│` above or below at the same column)

The correct pattern is to place arrows on their own line or with proper `─>`/`<─` connectors. This ensures other checks (rails, box-widths) can process the diagram correctly.

## Pipe continuity

T-junctions (`┬` and `┴`) originate vertical connector pipes (`│`). These pipes should trace straight down (or up) from the junction. If a pipe drifts (up to 5 columns tolerance), it is detected and realigned.

```
Before:          After:
   ┬               ┬
   │               │
   │               │
```

## Box padding

Content lines inside a box should have consistent left-padding (spaces between the left wall `│` and the first non-space character). When multiple content lines have different left-padding, the majority padding wins and outliers are corrected.

## Box spacing

Content lines inside a box must have at least 1 space between the content and the right box wall. When content touches the wall directly (0 right-padding), the box is expanded to add the minimum spacing.

## Horizontal arrows

Horizontal arrow patterns (`─>` / `<─`) connecting box walls should touch the wall characters without gaps. Spaces between an arrow tip and a box wall (`│`, `┐`, `┘`, `┤`) are detected and removed.

## Box walls

Nested boxes have opening corners (`┌`/`└`) at the same left column, with matching right corners (`┐`/`┘`). Interior wall pipes (`│`) must align with these corners. An 8-column drift tolerance is used when matching right walls to their expected positions.

The fix cascades: correcting an outer box wall may shift inner content, requiring re-evaluation. Hence the 3-pass iterative loop in the fix pipeline.

## Tree blocks

Structures containing tree branch characters (`├──`, `└──`) without box borders (`┌`, `┐`) are classified as tree blocks. These are excluded from all box-related checks to avoid false positives on directory listings and tree diagrams.

## Definition lists

Groups of consecutive list items matching the `- key: value` pattern form definition lists. The `:` separator is aligned across all items in the group by padding the key to match the longest key width. Single-item groups and items inside code blocks are skipped.

## Wide characters

Unicode characters with East Asian Width property W (Wide), F (Fullwidth), or A (Ambiguous) render as double-width in many monospace terminals and editors. When these appear inside code blocks, they break visual alignment of box-drawing diagrams. Common examples: ▶ ◆ ● ■ ★ and emoji. Box-drawing and arrow chars (─│┌┐└┘├┤┬┴┼→←↑↓) are excluded from detection since they are intentional diagram elements.

## Code blocks

Most checks operate within fenced code blocks (delimited by triple backticks). The list_descs check operates on regular markdown lines outside code blocks, aligning separator dashes in grouped list items.

## Constants

| Constant          | Value | Usage                                     |
|-------------------|-------|-------------------------------------------|
| RAIL_THRESHOLD    | 1     | Max column offset to join a rail cluster  |
| RAIL_MAX_GAP      | 1     | Max empty lines between rail entries      |
| CLUSTER_THRESHOLD | 3     | Max column distance for position clusters |
| BOX_WALL_DRIFT    | 8     | Max column drift for box wall matching    |
| PIPE_DRIFT_MAX    | 5     | Max column drift for pipe detection       |

---

related docs:
- docs/architecture.md                     - how these concepts flow through the fix pipeline
- docs/features/table-alignment.md         - table alignment implementation
- docs/features/box-width-normalization.md - box width normalization implementation
- docs/features/rail-alignment.md          - rail alignment implementation
- docs/features/arrow-alignment.md         - arrow alignment implementation
- docs/features/pipe-continuity.md         - pipe continuity implementation
- docs/features/box-wall-checking.md       - box wall checking implementation

related sources:
- src/docalign/utils.py  - constant definitions and shared helpers
- src/docalign/parser.py - code block and box group detection
