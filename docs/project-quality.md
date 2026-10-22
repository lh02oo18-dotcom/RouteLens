# Project quality checklist

This file maps project goals to verifiable repository evidence. Planned work is not marked complete until the evidence exists.

| Area | Current state | Evidence | Next acceptance point |
|---|---|---|---|
| Open-source reuse and design | Stable milestone complete | README, architecture, ADR, trajectory, route-mining and evidence interfaces | Preserve boundaries in future changes |
| Incremental delivery | Complete through v1.0.0 | Issues, feature branches, tests, roadmap, progress log | Add only evidence-backed milestones |
| Repository quality | Complete for current milestone | LICENSE, CONTRIBUTING, templates, CI, CHANGELOG, Releases | Keep dependency alerts reviewed |
| Communication and problem solving | Stable demo prepared | Decision records, known issues, evidence demo and presentation outline | Add evaluated real-video cases |

## Release readiness

| Requirement | State | Evidence or blocker |
|---|---|---|
| Public repository | Complete | `lh02oo18-dotcom/RouteLens` |
| README setup path | Verified locally | README and `docs/baseline-verification.md` |
| Explicit license | Complete | MIT `LICENSE` and `NOTICE.md` |
| Issue history | Complete | Issue #1 and linked implementation PRs |
| At least one Release | Complete | `v0.1.0`, `v0.2.0`, and `v0.3.0`; stable update prepares `v1.0.0` |
| Traceable history | Complete for current milestone | Feature branches, Conventional Commits, PRs and Actions |

## GitHub platform checklist

| Capability | Usage | Evidence |
|---|---|---|
| Repository and access | Public repository and protected main branch | Repository settings |
| Issues and Discussions | Track defects, features, experiments, and design questions | Linked Issues |
| Pull Requests | Merge milestone branches with template and review | Merged PRs |
| Actions and CI | Test Python 3.10 and 3.12 on push and PR | Green workflow runs |
| Pages | Publish architecture and demonstration results | `site/index.html` and Pages workflow |
| Releases | Baseline, anomaly detection, and stable release | Release pages |
| Security | Dependabot, dependency graph, and security policy | Alerts resolved or documented |

## Definition of done

1. An Issue describes the problem, scope, and acceptance criteria.
2. The change is developed on an independent branch.
3. Tests are updated and dependency, Ruff, and Pytest checks pass.
4. README, configuration, interfaces, and known issues remain synchronized.
5. The Pull Request separates reused behavior from RouteLens-specific behavior.
6. The Issue closes after merge, and milestone releases receive a tag and release notes.
