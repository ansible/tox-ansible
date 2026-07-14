# Agent guidelines for tox-ansible

Operational notes for coding agents working in this repository.

## Architectural conventions

These are the project invariants. Do not work around them — if one needs to
change, write an ADR first (see below).

1. **ade installs ansible-core.** tox-ansible generates tox environments and
   delegates ansible-core installation to `ade`. Do not add a parallel install
   path without an ADR.
2. **Matrices live in `src/tox_ansible/plugin.py`.** Upstream environments are
   `ENV_LIST`. AAP/cert extras are `DOWNSTREAM_EXTRA`. Do not introduce a second
   competing matrix definition without an ADR. Upstream uses tox’s Python
   floor/ceiling (today 3.11–3.14); extras use the Hub/partner cert Python
   floor (today **3.12+**) — see `/update-matrix` and ADR-001.
3. **Config surfaces are INI and TOML.** User settings come from `[ansible]` in
   `tox-ansible.ini` or `[tool.tox-ansible]` in `pyproject.toml` (TOML wins).
   Keep both in sync when adding options.
4. **`downstream=true` means upstream ∪ extras** (ADR-001). It is not an
   AAP-only matrix. Use `skip` to tighten.

## Architecture Decision Records

Major design choices that affect matrix semantics, config surfaces, plugin
behavior, or release process need an ADR under `.sdlc/adrs/`.

- Index: [`.sdlc/adrs/README.md`](.sdlc/adrs/README.md)
- Template: [`.sdlc/templates/adr.md`](.sdlc/templates/adr.md)
- Create with `/adr-new`
- Refresh matrices from official lifecycle pages with `/update-matrix`

When in doubt, check existing ADRs before inventing a new pattern. If none
covers the decision, write one before implementing.

## Skills

| Skill | Purpose |
|-------|---------|
| `/adr-new` | Create an Architecture Decision Record |
| `/update-matrix` | Refresh `ENV_LIST` / `DOWNSTREAM_EXTRA` from community + AAP lifecycle URLs |
