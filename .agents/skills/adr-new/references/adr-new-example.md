# ADR New Example Session

This is a reference example for the `/adr-new` skill.

## Interactive Mode (Streamlined)

```
User: /adr-new

Claude: Let's create an Architecture Decision Record.

Decision title?

User: Downstream Matrix Extends Upstream

Claude: Context — why is this decision needed?

User: Partners need AAP-supported ansible-core versions that community EOL'd,
but tox-ansible tracks the community support matrix. Need a way to keep both.

Claude: Constraints and drivers? (bullet list)

User:
- Must support INI and TOML config
- Default remains upstream-only
- Existing skip filter must still work

Claude: Options considered (name: description, pros/cons):

User:
Extend upstream: downstream=true unions AAP extras onto ENV_LIST
+ Single maintenance path, forward-looking for content authors
- Broader CI than strict AAP-only

Replace upstream: downstream mode uses only AAP cores
+ Smaller matrix
- Loses forward-compat testing; diverges from community tooling

Claude: Decision — which option and why?

User: Extend upstream — partners need extras and still benefit from newer cores.

Claude: Consequences? (use +/- prefix)

User:
+ Cert/AAP cores available again
+ Forward-looking community cores remain
- Larger envlist when downstream=true
~ skip can tighten the set

Claude: Status? (1=Proposed, 2=Accepted)

User: 2

Claude: Done!
- Created: ADR-001-downstream-matrix-extends-upstream.md
- Status: Accepted
```

## Quick Mode

```
User: /adr-new "gRPC over REST" --status accepted

Claude: Creating ADR-002...

Context? ...
Options? ...
Decision? ...
Consequences? ...

Done! Created ADR-002-....md (Accepted)
```
