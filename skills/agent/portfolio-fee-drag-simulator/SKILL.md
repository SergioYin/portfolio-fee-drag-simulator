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
- Release audit summary outputs should include Markdown and JSON combining tests, selfcheck, public scan, manifest, visual receipt, fixture doctor, and package audit status. Do not mark tests as pass unless the test command actually ran.
- Do not add GitHub Actions workflows.
