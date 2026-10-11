# Project quality checklist

This file maps project goals to verifiable repository evidence. Planned work is not marked complete until the evidence exists.

| Area | Current state | Evidence | Next acceptance point |
|---|---|---|---|
| Open-source reuse and design | In progress | README, architecture, ADR, NOTICE | Finish the differentiated architecture and interface example |
| Incremental delivery | In progress | Feature branch, baseline verification, tests, roadmap | Every milestone has an Issue, PR, tests, and runnable result |
| Repository quality | Local foundation complete | LICENSE, CONTRIBUTING, templates, CI, CHANGELOG | Public CI, PR, Release, and dependency alerts |
| Communication and problem solving | In progress | Decision records, known issues, progress log | Reproducible demo and documented incident retrospectives |

## Release readiness

| Requirement | State | Evidence or blocker |
|---|---|---|
| Public repository | Complete | `lh02oo18-dotcom/RouteLens` |
| README setup path | Verified locally | README and `docs/baseline-verification.md` |
| Explicit license | Complete | MIT `LICENSE` and `NOTICE.md` |
| Issue history | Pending | Create real Issues after initial push |
| At least one Release | Pending | Publish v0.1.0 after the baseline PR passes CI |
| Traceable history | In progress | Feature branches and Conventional Commits |

## GitHub platform checklist

| Capability | Usage | Evidence |
|---|---|---|
| Repository and access | Public repository and protected main branch | Repository settings |
| Issues and Discussions | Track defects, features, experiments, and design questions | Linked Issues |
| Pull Requests | Merge milestone branches with template and review | Merged PRs |
| Actions and CI | Test Python 3.10 and 3.12 on push and PR | Green workflow runs |
| Pages | Publish architecture and demonstration results | Pages URL after v0.3 |
| Releases | Baseline, anomaly detection, and stable release | Release pages |
| Security | Dependabot, dependency graph, and security policy | Alerts resolved or documented |

## Definition of done

1. An Issue describes the problem, scope, and acceptance criteria.
2. The change is developed on an independent branch.
3. Tests are updated and dependency, Ruff, and Pytest checks pass.
4. README, configuration, interfaces, and known issues remain synchronized.
5. The Pull Request separates reused behavior from RouteLens-specific behavior.
6. The Issue closes after merge, and milestone releases receive a tag and release notes.
