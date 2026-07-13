# ADR-001: Downstream Matrix Extends Upstream

## Status

Implemented

## Date

2026-07-13

## Context

Upstream `tox-ansible` tracks the [community ansible-core support matrix](https://docs.ansible.com/projects/ansible/latest/reference_appendices/release_and_maintenance.html#ansible-core-support-matrix).
PR [#562](https://github.com/ansible/tox-ansible/pull/562) dropped ansible-core
**2.16** (community EOL July 2025).

Red Hat Ansible Automation Platform still supports **2.16** as the platform
default for AAP 2.5–2.7, and publishes long-lived **2.18** EE streams
([AAP lifecycle](https://access.redhat.com/support/policy/updates/ansible-automation-platform)).
Automation Hub certification still expects partners to test against Python 3.12
and ansible-core 2.16 (minimum). Partners are expected to use tox-ansible.

Forces in tension:

- Community tooling should follow community EOL.
- Downstream / partner workflows need AAP-supported cores after community EOL.
- Content authors benefit from testing newer community cores before those become
  AAP EE defaults (forward-looking).
- Config must remain available on both INI (`[ansible]`) and TOML
  (`[tool.tox-ansible]`) surfaces.

## Decision

**We will add a `downstream` boolean (default `false`) that unions
`DOWNSTREAM_EXTRA` onto the upstream `ENV_LIST`, then applies the existing
`skip` filter.**

```ini
[ansible]
downstream = true
```

```toml
[tool.tox-ansible]
downstream = true
```

Semantics:

- `downstream = false` (default): upstream `ENV_LIST` only.
- `downstream = true`: **upstream ∪ DOWNSTREAM_EXTRA** (not an AAP-only matrix).
- Newer upstream cores (including those not yet in a given AAP release) remain
  when downstream mode is on — intentional forward-looking coverage.
- Use `skip` to tighten (e.g. drop `devel` / `milestone` / a specific core).

Initial `DOWNSTREAM_EXTRA` (AAP default/EE cores not already in upstream,
intersected with each core’s control-node Python range and the Hub/partner
certification Python floor **3.12+** — not tox-ansible’s upstream floor 3.11):

```
{integration, sanity, unit}-py3.12-{2.16, 2.18}
{integration, sanity, unit}-py3.13-{2.18}
```

Maintain matrices with the `/update-matrix` skill, which fetches the two
lifecycle URLs above and refreshes `ENV_LIST` / `DOWNSTREAM_EXTRA`.

## Alternatives Considered

### Alternative 1: Replace upstream when downstream=true

**Description**: Downstream mode uses only AAP-supported cores.

**Pros**:
- Smaller matrix closer to “what AAP supports today”
- Less CI time for partner pipelines

**Cons**:
- Loses forward-compat testing against newer community cores
- Diverges from upstream tox-ansible behavior partners already know
- Still need a second definition to maintain

**Why not chosen**: Partner/content developers benefit from catching breakages
on upcoming cores; extras are additive, not a replacement.

### Alternative 2: Dual packages / fork-only downstream ADT

**Description**: Keep upstream matrix community-only; ship a separate downstream
package or ADT fork with a different matrix.

**Pros**:
- Clear product boundary
- Upstream stays simple

**Cons**:
- Double maintenance and drift
- Partners must discover the “right” package
- Cert guidance still points at tox-ansible

**Why not chosen**: One plugin with a flag is simpler and keeps partners on the
same tool.

### Alternative 3: Full custom matrix via config

**Description**: Let users define the entire envlist in INI/TOML.

**Pros**:
- Maximum flexibility

**Cons**:
- Easy to invent unsupported combos
- Harder to keep aligned with official lifecycle pages
- Weak default for partners who just need “AAP extras”

**Why not chosen**: Curated extras plus `skip` covers the Hub/AAP case without
turning tox-ansible into a free-form matrix editor.

## Consequences

### Positive

- Partners can test AAP-supported cores (2.16 / 2.18) again via one flag.
- Forward-looking community cores remain available under downstream mode.
- Existing `skip` continues to work on the unioned list.
- INI and TOML stay in parity.

### Negative

- Downstream mode expands the envlist (more CI time unless `skip` is used).
- Two constants (`ENV_LIST`, `DOWNSTREAM_EXTRA`) must stay synchronized with
  external lifecycle pages.

### Neutral

- Default remains upstream-only; no behavior change for existing users.
- Matrix maintenance is agent-assisted via `/update-matrix`, not a silent CI
  auto-edit.

## Implementation Notes

- Constants and config loading live in `src/tox_ansible/plugin.py`.
- `add_ansible_matrix` parses both lists when `downstream` is true, unions env
  names, applies `skip`, then sorts with `custom_sort`.
- Document the flag in `docs/configuration.md` and `docs/user_guide.md`.
- Refresh versions with `/update-matrix` (do not invent cores from memory).
- Policy changes to “extends vs replaces” require a new or amended ADR.

## Related Decisions

- None yet.

## References

- https://docs.ansible.com/projects/ansible/latest/reference_appendices/release_and_maintenance.html#ansible-core-support-matrix
- https://access.redhat.com/support/policy/updates/ansible-automation-platform
- https://github.com/ansible/tox-ansible/pull/562
- Internal DevTools discussion on partner cert requirements vs community EOL
- Skill: `.agents/skills/update-matrix/SKILL.md`

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-07-13 | Brad Thornton | Initial decision and implementation |
| 2026-07-13 | Brad Thornton | Drop py3.11 from DOWNSTREAM_EXTRA (Hub cert floor 3.12+) |
