# Project quality checklist

This file maps project goals to verifiable repository evidence. Planned work is not marked complete until the evidence exists.

| Area | Current state | Evidence | Next acceptance point |
|---|---|---|---|
| Open-source reuse and design | Stable milestone complete | README, architecture, ADR, trajectory, route-mining and evidence interfaces | Preserve boundaries in future changes |
| Incremental delivery | v1.1.0 published | Issues, feature branches, tests, roadmap, progress log, PR #15 and Release v1.1.0 | Extend only against a documented Issue and acceptance criteria |
| Repository quality | Complete for current milestone | LICENSE, CONTRIBUTING, templates, CI, CHANGELOG, Releases | Keep dependency alerts reviewed |
| Communication and problem solving | Stable demo and real-data evidence published | Decision records, known issues, CAVIAR results and presentation outline | Add broader scenes only with licensed data |

## Release readiness

| Requirement | State | Evidence or blocker |
|---|---|---|
| Public repository | Complete | `lh02oo18-dotcom/RouteLens` |
| README setup path | Verified locally | README and `docs/baseline-verification.md` |
| Explicit license | Complete | MIT `LICENSE` and `NOTICE.md` |
| Issue history | Complete | Issue #1, real-data Issue #14 and linked implementation PRs |
| At least one Release | Complete | `v0.1.0` through `v1.1.0` are published |
| Traceable history | Complete for current milestone | Feature branches, Conventional Commits, reviewed PRs and Actions |

## GitHub platform checklist

| Capability | Usage | Evidence |
|---|---|---|
| Repository and access | Public repository | Repository settings and public clone URL |
| Issues and Discussions | Track defects, features, experiments, and design questions | Linked Issues and public Discussions |
| Pull Requests | Merge milestone branches with template and review | Merged PRs and review records |
| Actions and CI | Test Python 3.10 and 3.12 on push and PR | Green workflow runs |
| Pages | Publish architecture, reproducibility commands and real-data results | Public Pages site, `site/index.html` and Pages workflow |
| Releases | Baseline, anomaly detection, stable release and evaluated milestone | Release pages through `v1.1.0` |
| Security | Dependabot updates and security policy | `.github/dependabot.yml`, `SECURITY.md` and dependency PRs |

## Definition of done

1. An Issue describes the problem, scope, and acceptance criteria.
2. The change is developed on an independent branch.
3. Tests are updated and dependency, Ruff, and Pytest checks pass.
4. README, configuration, interfaces, and known issues remain synchronized.
5. The Pull Request separates reused behavior from RouteLens-specific behavior.
6. The Issue closes after merge, and milestone releases receive a tag and release notes.

