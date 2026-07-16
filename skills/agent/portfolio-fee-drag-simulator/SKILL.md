# portfolio-fee-drag-simulator

Use this skill when working on the `portfolio-fee-drag-simulator` repo or when a user asks for static portfolio fee drag packets.

## Boundaries

Keep finance safety boundaries explicit: static local assumptions only; no live data, broker API, orders, predictions, portfolio optimization, tax/legal/investment advice, or buy/sell/hold recommendations.

## Common Commands

```bash
python -m unittest discover -s tests
python -m portfolio_fee_drag_simulator selfcheck
python -m portfolio_fee_drag_simulator quickstart-check --output demo
python -m portfolio_fee_drag_simulator input-template --output demo/input_templates
python -m portfolio_fee_drag_simulator assumption-diff --output demo
python -m portfolio_fee_drag_simulator risk-flags --output demo
python -m portfolio_fee_drag_simulator batch-compare --output demo
python -m portfolio_fee_drag_simulator scenario-narrative --output demo
python -m portfolio_fee_drag_simulator public-scan --root . --output demo/public_scan.json
python -m portfolio_fee_drag_simulator fixture-doctor --output demo
python -m portfolio_fee_drag_simulator package-audit --root . --output demo
python -m portfolio_fee_drag_simulator release-manifest --root . --output demo/release_manifest.json
python -m portfolio_fee_drag_simulator release-audit-summary --output demo --tests-status pass
python -m portfolio_fee_drag_simulator scenario-presets --output demo/scenario_presets.json
python -m portfolio_fee_drag_simulator case-gallery --output demo
python -m portfolio_fee_drag_simulator visual-receipt --output demo
python -m portfolio_fee_drag_simulator cold-start-walkthrough --output demo
python -m portfolio_fee_drag_simulator decision-journal --output demo
python -m portfolio_fee_drag_simulator docs-export --output demo
python -m portfolio_fee_drag_simulator reproducibility-pack --output demo
python -m portfolio_fee_drag_simulator security-boundary-report --root . --output demo
python -m portfolio_fee_drag_simulator static-showcase --output demo/showcase.html
python -m portfolio_fee_drag_simulator promotion-checklist --output demo
python -m portfolio_fee_drag_simulator artifact-catalog --output demo
```

## Implementation Notes

- Runtime dependencies must remain empty.
- Bundled fixtures live under `portfolio_fee_drag_simulator/data/` and must remain package data.
- Demo outputs should be deterministic and generated through `quickstart-check`.
- Input template outputs should include holdings CSV, assumptions JSON, and a README fragment for adapting local CSV/JSON without live data.
- Assumption diff outputs should include Markdown and JSON field deltas, observed direction, and review impact, without advice.
- Risk flags outputs should include Markdown and JSON prompts for high cash allocation, high expense ratio, high turnover/tax drag, allocation mismatch, long horizon, and frequent rebalancing. Flags must be review prompts, not recommendations.
- Scenario preset fixtures should remain static JSON and gallery outputs should include Markdown, JSON, and HTML.
- Batch compare outputs should include Markdown and JSON rankings by total annual drag, total dollar drag, cash drag, turnover tax drag, and fee drag, plus next-action review questions instead of recommendations.
- Scenario narrative outputs should read case gallery and batch compare JSON and include Markdown and JSON plain-language scenario explanations, key drag drivers, human review questions, and no-advice boundaries.
- Visual receipt outputs should include Markdown, JSON, and HTML with local routes, bytes, SHA-256 hashes, roles, regeneration commands, and safety boundaries.
- Cold-start walkthrough outputs should include Markdown and JSON, fit a 10-minute first-time GitHub user path, and include expected outputs plus boundaries.
- Fixture doctor outputs should include Markdown and JSON with actionable warnings for holdings, assumptions, and scenario preset fixtures.
- Package audit outputs should include Markdown and JSON covering zero runtime dependencies, package-data declarations, script wiring, import/project versions, and command coverage.
- Decision journal outputs should include deterministic Markdown and JSON prompts for assumptions changed, human verification needs, no-advice boundary, and a blank next review date field.
- Artifact catalog outputs should include deterministic Markdown and JSON inventory rows with route, bytes, SHA-256, producer command, role, and promotion usefulness.
- Docs export outputs should include deterministic Markdown and JSON covering command summaries, input schema, artifact map, verification commands, and finance boundaries.
- Reproducibility pack outputs should include deterministic Markdown and JSON with exact local clone, install, test, build, wheel smoke, and demo regeneration commands plus expected artifacts.
- Security boundary report outputs should include deterministic Markdown and JSON covering no secrets, no workflows, no network/live data, no broker/API/order execution, zero runtime dependencies, package data, and finance/no-advice boundaries.
- Static showcase output should be no-JS HTML linking input templates, assumption diff, risk flags, dashboard, case gallery, batch compare, scenario narrative, visual receipt, cold-start walkthrough, decision journal, artifact catalog, release audit, package audit, docs export, and promotion checklist with short user-value copy.
- Static showcase output should include the reproducibility pack and security boundary report links.
- Release audit summary outputs should include Markdown and JSON combining tests, selfcheck, public scan, manifest, visual receipt, fixture doctor, package audit, reproducibility pack, and security boundary report status. Do not mark tests as pass unless the test command actually ran.
- Promotion checklist outputs should include Markdown and JSON release/promotion readiness prompts referencing README, quickstart, demo/showcase.html, docs_export, release_audit_summary, package_audit, public_scan, reproducibility_pack, security_boundary_report, wheel install, and finance boundaries.
- Do not add GitHub Actions workflows.
