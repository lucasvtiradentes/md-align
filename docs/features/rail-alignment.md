# Rail Alignment

Module: `align_md_docs/rails.py`

## What it does

Detects and corrects drift in vertically-adjacent box characters. When box chars that should be in the same column are off by a few positions, they are realigned to the dominant column.

## Two-phase detection

### Phase 1: by-index alignment

Groups lines by the number of box characters they contain, then clusters lines with similar position patterns (within CLUSTER_THRESHOLD = 3 columns). For each position index in a cluster, the most-common column wins.

```
┌───────────────────────────────────────┐
│  Group lines by box-char count        │
│         │                             │
│         v                             │
│  Cluster by position similarity       │
│  (threshold: 3 columns)               │
│         │                             │
│         v                             │
│  For each position index:             │
│  most-common column = target          │
│  flag deviations                      │
└───────────────────────────────────────┘
```

### Phase 2: by-column alignment

Identifies rails by clustering all box chars by column proximity (RAIL_THRESHOLD = 1). Consecutive entries (max 1-line gap) form a rail. For each rail, the dominant column is selected with priority:

1. Pipe origins (┬/┴) - highest priority
2. Structural chars (non-pipe, non-cross) - medium priority
3. Count of entries - lowest priority tiebreaker

```
┌───────────────────────────────────────┐
│  Sort all box chars by column         │
│         │                             │
│         v                             │
│  Cluster adjacent columns             │
│  (threshold: 1)                       │
│         │                             │
│         v                             │
│  Segment by line continuity           │
│  (max gap: 1 line)                    │
│         │                             │
│         v                             │
│  Each segment = a rail                │
│  Compute target column per rail       │
└───────────────────────────────────────┘
```

## Check output

Format: `L{line} box char at col {actual}, expected col {target}`

## Fix algorithm

1. Build corrections map: `(line_idx, current_col) -> expected_col`
2. For each line with corrections, call `_realign_box_chars()` which:
   - Splits the line into segments between box chars
   - Adjusts segment widths (spaces or dashes) to shift chars to target columns
   - Preserves box-char characters, only modifying inter-char spacing

## Safety checks

- Rails need at least 2 entries to be valid
- If no structural or pipe-origin chars exist and minority exceeds 1/3 of rail entries, no correction is applied (ambiguous rail)
- Already-flagged positions from phase 1 are skipped in phase 2

## Scope

- Operates only within fenced code blocks
- Skips tree blocks
- Runs inside the convergence loop (up to 3 iterations)

---

related docs:
- docs/concepts.md     - rail alignment concept and constants
- docs/architecture.md - position in convergence loop

related sources:
- align_md_docs/rails.py - check and fix implementation
- align_md_docs/utils.py - RAIL_THRESHOLD, RAIL_MAX_GAP, CLUSTER_THRESHOLD, _realign_box_chars
