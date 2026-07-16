# portfolio-fee-drag-simulator

Use this skill when working on the `portfolio-fee-drag-simulator` repo or when a user asks for static portfolio fee drag packets.

## Boundaries

Keep finance safety boundaries explicit: static local assumptions only; no live data, broker API, orders, predictions, portfolio optimization, tax/legal/investment advice, or buy/sell/hold recommendations.

## Common Commands

```bash
python -m unittest discover -s tests
python -m portfolio_fee_drag_simulator selfcheck
python -m portfolio_fee_drag_simulator quickstart-check --output demo
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
python -m portfolio_fee_drag_simulator static-showcase --output demo/showcase.html
python -m portfolio_fee_drag_simulator artifact-catalog --output demo
```

## Implementation Notes

- Runtime dependencies must remain empty.
- Bundled fixtures live under `portfolio_fee_drag_simulator/data/` and must remain package data.
- Demo outputs should be deterministic and generated through `quickstart-check`.
- Scenario preset fixtures should remain static JSON and gallery outputs should include Markdown, JSON, and HTML.
- Visual receipt outputs should include Markdown, JSON, and HTML with local routes, bytes, SHA-256 hashes, roles, regeneration commands, and safety boundaries.
- Cold-start walkthrough outputs should include Markdown and JSON, fit a 10-minute first-time GitHub user path, and include expected outputs plus boundaries.
- Fixture doctor outputs should include Markdown and JSON with actionable warnings for holdings, assumptions, and scenario preset fixtures.
- Package audit outputs should include Markdown and JSON covering zero runtime dependencies, package-data declarations, script wiring, import/project versions, and command coverage.
- Decision journal outputs should include deterministic Markdown and JSON prompts for assumptions changed, human verification needs, no-advice boundary, and a blank next review date field.
- Artifact catalog outputs should include deterministic Markdown and JSON inventory rows with route, bytes, SHA-256, producer command, role, and promotion usefulness.
- Docs export outputs should include deterministic Markdown and JSON covering command summaries, input schema, artifact map, verification commands, and finance boundaries.
- Static showcase output should be no-JS HTML linking dashboard, case gallery, visual receipt, cold-start walkthrough, decision journal, artifact catalog, release audit, package audit, and docs export with short user-value copy.
- Release audit summary outputs should include Markdown and JSON combining tests, selfcheck, public scan, manifest, visual receipt, fixture doctor, and package audit status. Do not mark tests as pass unless the test command actually ran.
- Do not add GitHub Actions workflows.
