---
name: adr-new
description: >-
  Create an Architecture Decision Record for tox-ansible. Use when documenting
  an architecture decision, "record this choice", "we decided to use X", or
  major design choices affecting the matrix, config surfaces, or plugin
  behavior.
argument-hint: "[Decision Title] [--status accepted|proposed]"
user-invocable: true
metadata:
  author: tox-ansible
  version: 1.0.0
---

# ADR New

Create an Architecture Decision Record.

## Arguments

If `$ARGUMENTS` is provided, parse for:

- Decision title in quotes → use as ADR title
- `--status X` → set status (`proposed` / `accepted`)

## Usage

```
/adr-new                            # Interactive mode
/adr-new "Decision Title"           # Quick mode with title
/adr-new "Title" --status accepted  # With status
```

## Behavior

### 1. Check for Context

**From conversation:** If recent discussion contains a decision:

```
I see you decided [X] over [Y]. Create ADR from this? (Y/n)
```

### 2. Determine Next ADR Number

Scan `.sdlc/adrs/ADR-*.md` for highest number, increment by 1.

### 3. Gather Information (Streamlined)

```
Decision title?
```

```
Context — why is this decision needed?
```

```
Constraints and drivers? (bullet list, or included above)
```

```
Options considered (name: description, pros/cons):
```

Require at least 2 options for meaningful comparison.

```
Decision — which option and why?
```

```
Consequences? (use +/- prefix, or describe)
```

```
Status? (1=Proposed, 2=Accepted)
```

```
Implementation guidance? (or skip)
```

```
Related ADRs? (numbers, or skip)
```

### 4. Consistency and Invariant Check

**Before creating the ADR file**, verify consistency with tox-ansible conventions
in `AGENTS.md`:

| Convention | Status |
|------------|--------|
| ade installs ansible-core (plugin orchestrates tox envs) | Consistent / MODIFIES |
| Upstream matrix lives in `ENV_LIST` in `plugin.py` | Consistent / MODIFIES |
| Config via `[ansible]` INI and `[tool.tox-ansible]` TOML | Consistent / MODIFIES |
| No dual/competing matrix semantics without an ADR | Consistent / MODIFIES |

Also read `.sdlc/adrs/README.md` for conflicts, duplicates, and related ADRs.

**If this ADR contradicts an existing accepted ADR without superseding it:**

Either add `Supersedes: ADR-NNN`, make it compatible, or explain coexistence under Related Decisions.

### 5. Create ADR File

Create `.sdlc/adrs/ADR-NNN-title-slug.md` using `.sdlc/templates/adr.md`.

**Slug:** 3-5 words, lowercase, hyphens.

Fill title, status, date, context, options (with why-not), decision, consequences, implementation notes, related decisions, references, and revision history.

### 6. Update Index

Run:

```bash
python scripts/generate_adr_index.py
```

Do not hand-edit `.sdlc/adrs/README.md`.

### 7. Summary

```
Done!
- Created: ADR-NNN-title-slug.md
- Status: [Proposed/Accepted]
- Updated: adrs/README.md (via generate_adr_index.py)

Next: [If Proposed] Share for review | [If Accepted] Implement
```

## Quick Mode

| Provided | Skip |
|----------|------|
| Title in quotes | Title prompt |
| `--status X` | Status prompt |

## Edge Cases

| Situation | Handling |
|-----------|----------|
| <2 options provided | Ask for at least one more |
| No consequences listed | Note "To be determined" |
