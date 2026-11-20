# ADR-002: Time-based Scenario Job Bucketing

## Status

Implemented

## Date

2026-11-19

## Context

Collections with large integration suites need to spread the scenarios selected by an ImpactReport across several CI jobs. amazon.aws already does this with `ansible_test_splitter`: up to 24 jobs, at most 8 running at once, packed by the `time=` and `slow` aliases on each target. `tox-ansible --impact-file` selects those scenarios and then runs them in one tox invocation.

AAP-99999 asks for a GitHub Actions matrix that assigns every selected scenario to exactly one job, plus configuration for the job count and the maximum number of parallel jobs. Each job must be able to run only its own scenarios.

Config for this plugin is exposed on both INI (`[ansible]`) and TOML (`[tool.tox-ansible]`), with TOML winning over INI and CLI winning over both.

## Decision

**We will pack impact-selected integration targets and molecule scenarios inside tox-ansible, emit that packing as a GitHub Actions matrix, and rerun a single job with `--matrix-job`.**

- `matrix_jobs` and `matrix_max_parallel` are config and CLI settings.
- `--gh-matrix-jobs` prints `{jobs, scenarios, max_parallel}` and exits. It does not replace `--gh-matrix`.
- Integration targets and molecule scenarios are packed separately into `integration-N` and `molecule-N` jobs.
- Durations come from ansible-test `aliases` (`time=` and `slow`), matching `ansible_test_splitter`. Missing data uses 180 seconds. Molecule scenarios use 180 seconds.
- Equal durations are ordered by name so the matrix and `--matrix-job` stay stable.
- Empty jobs are omitted.
- `--matrix-job <id>` rebuilds the buckets from the impact report and integration `aliases`, then passes only those names to the existing integration or molecule command.
- Integration ids are target directory names. Molecule ids are impact-report paths, so scenarios that share a directory name stay distinct. Ids are space-separated and cannot contain whitespace.
- Collection molecule scenarios run with `molecule test -s` and the name relative to `extensions/molecule/`. Other molecule scenarios run from the directory that contains `molecule/`.
- `molecule_commands` is incompatible with `--matrix-job`; the combination exits instead of running the unscoped replacement commands.
- `max_parallel` is data for the workflow. Tox does not schedule runners.

## Alternatives Considered

### Alternative 1: Keep bucketing in ansible_test_splitter

**Description**: Leave job packing in the external splitter and pass its batches into tox as positional arguments.

**Pros**:
- amazon.aws already runs this splitter.
- No new tox-ansible command surface.

**Cons**:
- The ImpactReport workflow still cannot describe or run a subset.
- Positional arguments are appended to the full target list, so they do not replace it.
- Every collection would keep a copy of the splitter wiring.

**Why not chosen**: AAP-99999 is the tox-ansible gap. The matrix and the filtered run both belong next to `--impact-file`.

### Alternative 2: Split the list into equal counts

**Description**: Give each job the same number of scenarios and ignore aliases.

**Pros**:
- No aliases files to read.
- The assignment is obvious.

**Cons**:
- A job of long tests can exceed the runner limit while another job finishes immediately.
- It misses the runtime behavior amazon.aws already depends on.

**Why not chosen**: The story asks for time-based distribution.

## Consequences

### Positive

- A collection can replace the splitter's packing step with `--impact-file` and `--gh-matrix-jobs`.
- Generating the matrix and running a job use one implementation.
- Existing `--gh-matrix` and unscoped `--impact-file` runs stay unchanged when the new flags are absent.

### Negative

- Each runner must use the same `matrix_jobs` value, impact report contents, and integration `aliases` files as the generate step. `--matrix-job` recomputes assignments from those inputs, so a different report or aliases file can move a target to another job.
- Molecule scenarios have no aliases file, so they share one default duration.
- `max_parallel` only takes effect when the workflow copies it into `strategy.max-parallel`.

### Neutral

- The packer keeps the splitter's overflow rule: a scenario that fits in no remaining job is placed in the first job.

## Implementation Notes

- Packing lives in `src/tox_ansible/bucketing.py`.
- Plugin hooks in `src/tox_ansible/plugin.py` add the config keys, CLI flags, matrix output, and `--matrix-job` filtering.
- `--matrix-job` on the other test kind logs a skip and runs `echo`, so a molecule environment does not execute integration targets.

## Related Decisions

- ADR-001: Downstream Matrix Extends Upstream (same INI and TOML config rule)

## References

- AAP-99999
- ansible_test_splitter `split_into_equally_sized_chunks`: https://github.com/ansible/cloud-content-ci-automation/blob/main/.github/actions/ansible_test_splitter/list_changed_targets.py

---

## Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-11-19 | Sudhir Verma | Accepted and implemented with AAP-99999 |
| 2026-11-20 | Sudhir Verma | Molecule jobs keep full scenario paths; reject molecule_commands with --matrix-job |
| 2026-11-20 | Sudhir Verma | Molecule commands use -s or bash -c; reject whitespace in matrix ids |
| 2026-11-20 | Sudhir Verma | Runners must reuse the generate-step impact report and aliases |

---
