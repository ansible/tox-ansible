---
name: update-matrix
description: >-
  Refresh tox-ansible ENV_LIST and DOWNSTREAM_EXTRA from the community
  ansible-core support matrix and the Red Hat AAP lifecycle pages. Use when
  asked to update the matrix, sync ansible-core versions, drop EOL cores, add
  a new core after GA, or align with AAP lifecycle.
argument-hint: "[--apply] [--upstream-only|--downstream-only]"
user-invocable: true
metadata:
  author: tox-ansible
  version: 1.0.0
---

# Update Matrix

Refresh the ansible-core / Python matrices in `src/tox_ansible/plugin.py` from
the official lifecycle sources. Follow ADR-001: downstream **extends** upstream.

## Arguments

- `--apply` — edit files after showing the diff (default is propose + ask)
- `--upstream-only` — only refresh `ENV_LIST`
- `--downstream-only` — only refresh `DOWNSTREAM_EXTRA`

## Canonical sources (fetch live every run)

Do **not** rely on training data or chat memory for versions.

1. Community support matrix:
   https://docs.ansible.com/projects/ansible/latest/reference_appendices/release_and_maintenance.html#ansible-core-support-matrix
2. AAP lifecycle:
   https://access.redhat.com/support/policy/updates/ansible-automation-platform

See [references/sources.md](references/sources.md) for a worked derivation example.

## Procedure

### 1. Fetch and summarize

Fetch both pages (WebFetch or equivalent). Produce a short summary:

- Community: which ansible-core majors are maintained vs EOL; control-node
  Python ranges per core.
- AAP: which cores are still the platform default or published EE streams under
  Full / Maintenance support; note control-node Python from AAP Table 1.3 when
  present.

### 2. Derive upstream `ENV_LIST`

- Include non-EOL ansible-core majors from the community matrix.
- Always include `milestone` and `devel` on Python versions that support the
  newest maintained cores (match existing project convention).
- Pair each core with control-node Python versions from the community table,
  intersected with tox-ansible’s Python floor/ceiling (today **3.11–3.14**).
- Drop community-EOL cores from `ENV_LIST` (they may still appear only in
  `DOWNSTREAM_EXTRA` if AAP still supports them).
- Keep the `galaxy` entry and the
  `{integration, sanity, unit}-pyX.Y-{...}` factor syntax.

### 3. Derive `DOWNSTREAM_EXTRA`

- Start from AAP-supported cores (platform default + published EE streams still
  in support).
- Keep only environment combos **not already present** in the proposed
  `ENV_LIST` (extras are additive; no duplicates).
- Intersect Python with the tox-ansible floor and each core’s control-node
  range (community table and/or AAP Table 1.3).
- Remember ADR-001: downstream mode is **upstream ∪ extras**, so it is fine if
  upstream contains cores not yet in AAP.

### 4. Diff and confirm

Diff proposed constants against current `ENV_LIST` / `DOWNSTREAM_EXTRA` in
`src/tox_ansible/plugin.py`. Show a short before/after summary.

Unless `--apply` (or the user already said to apply), ask for confirmation
before editing.

### 5. Apply

If approved:

1. Update the constants in `src/tox_ansible/plugin.py`.
2. Update unit/integration tests and fixtures that hardcode matrix lengths or
   version strings (e.g. `GH_MATRIX_LENGTH`, assertions naming specific cores).
3. Refresh docs examples if they hardcode obsolete versions
   (`docs/configuration.md`, `docs/user_guide.md`).

### 6. Verify

Run the project’s usual matrix tests (unit tests covering `add_ansible_matrix`
and integration list/matrix checks). Note Hub-cert or partner impact if extras
shrink.

### 7. Policy vs version churn

If the request changes **semantics** (e.g. “downstream should replace
upstream”, new config keys, different union rules), stop and use `/adr-new`
(or amend ADR-001). Do not silently change policy in a matrix refresh.

## Output checklist

- [ ] Both URLs fetched this run
- [ ] Upstream and downstream proposals summarized
- [ ] Diff shown
- [ ] Files updated (if apply)
- [ ] Tests/docs adjusted
- [ ] ADR opened only if policy changed
