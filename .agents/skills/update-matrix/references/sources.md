# Matrix sources

## URLs

1. Community ansible-core support matrix:
   https://docs.ansible.com/projects/ansible/latest/reference_appendices/release_and_maintenance.html#ansible-core-support-matrix
2. Red Hat Ansible Automation Platform life cycle:
   https://access.redhat.com/support/policy/updates/ansible-automation-platform

## Worked example (illustrative)

Suppose the community matrix shows (simplified):

| Core | Status | Control-node Python |
|------|--------|---------------------|
| 2.21 | Maintained | 3.12–3.14 |
| 2.20 | Maintained | 3.12–3.14 |
| 2.19 | Maintained | 3.11–3.13 |
| 2.18 | EOL | 3.11–3.13 |
| 2.16 | EOL | 3.10–3.12 |

And AAP still lists **2.16** as platform default and **2.18** as a supported EE
stream for supported AAP minors.

tox-ansible Python floor/ceiling: **3.11–3.14**.

**Upstream `ENV_LIST` fragment** (non-EOL only + milestone/devel):

```
galaxy
{integration, sanity, unit}-py3.11-{2.19}
{integration, sanity, unit}-py3.12-{2.19, 2.20, 2.21}
{integration, sanity, unit}-py3.13-{2.19, 2.20, 2.21, milestone, devel}
{integration, sanity, unit}-py3.14-{2.20, 2.21, milestone, devel}
```

**`DOWNSTREAM_EXTRA`** (AAP cores not already in upstream):

```
{integration, sanity, unit}-py3.11-{2.16, 2.18}
{integration, sanity, unit}-py3.12-{2.16, 2.18}
{integration, sanity, unit}-py3.13-{2.18}
```

Notes:

- No `py3.14` × `2.16` / `2.18` (outside those cores’ control-node Python).
- No `2.19+` in extras (already in upstream).
- With `downstream = true`, partners get 2.16/2.18 **and** still run 2.19+ /
  milestone / devel unless they `skip` them.
