# portfolio-fee-drag-simulator

`portfolio-fee-drag-simulator` is a zero-dependency Python CLI for building static, reviewable portfolio drag packets from local assumptions. It is designed for analysts, fiduciary operations teams, educators, and product teams who need deterministic examples of how expense ratios, cash allocation, turnover/tax assumptions, contributions, and rebalancing costs can compound over time.

It does not fetch market data, connect to brokerages, place orders, predict returns, optimize portfolios, or provide tax, legal, investment, or buy/sell/hold advice. Every result is a local arithmetic scenario based on user-supplied or bundled assumptions.

## Quickstart

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
portfolio-fee-drag quickstart-check --output demo
```

The quickstart writes deterministic demo artifacts:

- `demo/fee_drag_packet.md`
- `demo/fee_drag_packet.json`
- `demo/sensitivity_matrix.md`
- `demo/history_comparison.md`
- `demo/review_ledger.md`
- `demo/dashboard.html`
- `demo/scenario_presets.json`
- `demo/case_gallery.md`
- `demo/case_gallery.json`
- `demo/case_gallery.html`
- `demo/visual_receipt.md`
- `demo/visual_receipt.json`
- `demo/visual_receipt.html`
- `demo/cold_start_walkthrough.md`
- `demo/cold_start_walkthrough.json`
- `demo/fixture_doctor.md`
- `demo/fixture_doctor.json`
- `demo/package_audit.md`
- `demo/package_audit.json`
- `demo/decision_journal.md`
- `demo/decision_journal.json`
- `demo/selfcheck.json`
- `demo/release_manifest.json`
- `demo/release_audit_summary.md`
- `demo/release_audit_summary.json`
- `demo/maturity_report.md`
- `demo/artifact_catalog.md`
- `demo/artifact_catalog.json`
- `demo/public_scan.json`

## Commands

- `build-packet`: create Markdown and JSON packet artifacts from holdings and assumptions.
- `compare-history`: compare bundled or supplied historical scenario snapshots.
- `sensitivity-matrix`: generate a static fee/return sensitivity table.
- `review-ledger`: validate and summarize a holdings ledger.
- `static-dashboard`: render a standalone HTML dashboard from a packet JSON file.
- `scenario-presets`: write or print bundled scenario preset JSON.
- `case-gallery`: render deterministic Markdown, JSON, and HTML gallery artifacts from scenario presets.
- `visual-receipt`: hash and summarize dashboard and case gallery artifacts with local routes, byte counts, SHA-256 hashes, roles, regeneration commands, and safety boundaries.
- `cold-start-walkthrough`: write a deterministic 10-minute Markdown/JSON guide for a first-time GitHub user to install, run, evaluate, and understand boundaries.
- `fixture-doctor`: validate holdings, assumptions, and scenario preset fixtures with actionable warnings.
- `package-audit`: inspect zero-dependency metadata, package-data readiness, script wiring, and command coverage.
- `decision-journal`: generate deterministic Markdown/JSON research-note prompts from packet, gallery, and audit artifacts, including assumptions changed, human verification needs, no-advice boundary, and a next review date field.
- `artifact-catalog`: inventory deterministic demo artifacts with route, bytes, SHA-256, producer command, role, and promotion usefulness.
- `quickstart-check`: run the full deterministic demo route.
- `release-manifest`: hash source files for release review.
- `release-audit-summary`: combine tests, selfcheck, public scan, manifest, visual receipt, fixture doctor, and package audit status into Markdown and JSON for release owners.
- `maturity-report`: print a public-readiness checklist.
- `selfcheck`: verify CLI wiring, bundled examples, and deterministic calculations.
- `public-scan`: scan local files for common secret markers and required finance boundaries.

## Input Model

Holdings CSV columns:

```csv
account,ticker,name,allocation,expense_ratio
Taxable,VTI,Total US Market,0.55,0.0003
```

Assumptions JSON fields:

```json
{
  "initial_value": 100000,
  "annual_contribution": 6000,
  "years": 20,
  "gross_return": 0.05,
  "cash_return": 0.02,
  "turnover_rate": 0.12,
  "realized_gain_rate": 0.35,
  "tax_rate": 0.15,
  "taxable_allocation": 0.7,
  "rebalance_frequency": "annual",
  "rebalance_cost": 0.0002,
  "contribution_timing": "beginning"
}
```

The simulator computes a weighted expense ratio plus explicit local assumptions for:

- cash drag: cash-like holding allocation multiplied by `max(gross_return - cash_return, 0)`;
- turnover/tax drag: `turnover_rate * realized_gain_rate * tax_rate * taxable_allocation`;
- rebalance drag: `rebalance_cost` multiplied by annual, quarterly, monthly, or no rebalance events;
- contribution timing: annual contributions applied at the beginning or end of each simulated year.

It compares annual compounding at the gross return against compounding at `gross_return - total_annual_drag_rate`. All fields are deterministic local scenario inputs, not recommendations or estimates from live data.

## Scenario Presets, Case Gallery, and Receipts

Version 0.5 bundles three deterministic scenario presets:

- `low-cost-etf`: diversified low-expense ETF-style allocation with modest turnover and limited cash drag.
- `high-turnover-taxable-fund`: taxable fund-style allocation with higher expense, turnover, realized gains, and quarterly rebalancing assumptions.
- `cash-heavy-waitlist`: staged-deployment scenario with high cash allocation and conservative turnover assumptions.

Export the preset bundle:

```bash
portfolio-fee-drag scenario-presets --output demo/scenario_presets.json
```

Build the gallery:

```bash
portfolio-fee-drag case-gallery --output demo
```

The gallery emits `case_gallery.md`, `case_gallery.json`, and `case_gallery.html`. It uses the same static arithmetic model and safety boundary as `build-packet`.

Build the visual receipt after dashboard and gallery artifacts exist:

```bash
portfolio-fee-drag visual-receipt --output demo
```

The receipt emits `visual_receipt.md`, `visual_receipt.json`, and `visual_receipt.html`. It records local routes, bytes, SHA-256 hashes, artifact roles, regeneration commands, and safety boundaries for dashboard and case gallery review.

Write the first-run walkthrough:

```bash
portfolio-fee-drag cold-start-walkthrough --output demo
```

The walkthrough emits `cold_start_walkthrough.md` and `cold_start_walkthrough.json` with a 10-minute GitHub install/run/evaluate path, expected outputs, and explicit boundaries.

Build the investor workflow prompts:

```bash
portfolio-fee-drag decision-journal --output demo
```

The decision journal emits `decision_journal.md` and `decision_journal.json`. It creates deterministic prompts for a research note covering assumptions changed, human verification needs, the no-advice boundary, and a blank `next_review_date` field for human completion.

Inventory generated demo artifacts:

```bash
portfolio-fee-drag artifact-catalog --output demo
```

The artifact catalog emits `artifact_catalog.md` and `artifact_catalog.json`. It records local routes, byte counts, SHA-256 hashes, producer commands, artifact roles, and promotion usefulness for deterministic demo artifacts produced before the catalog runs.

## Release-Owner Audit

Validate bundled fixtures:

```bash
portfolio-fee-drag fixture-doctor --output demo
```

Inspect package readiness:

```bash
portfolio-fee-drag package-audit --root . --output demo
```

After running tests, selfcheck, public scan, manifest generation, and visual receipt generation, write the release-owner summary:

```bash
portfolio-fee-drag release-audit-summary --output demo --tests-status pass
```

The summary emits `release_audit_summary.md` and `release_audit_summary.json`. `quickstart-check` also emits these files, but records tests as `not-run` because quickstart does not execute the unit test suite.

## Safety Boundaries

This project is for static local scenario review only. It intentionally has no live data and excludes broker APIs, order execution, predictions, portfolio optimization, tax advice, legal advice, investment advice, and buy/sell/hold recommendations.

## Development

```bash
python -m unittest discover -s tests
python -m portfolio_fee_drag_simulator selfcheck
python -m portfolio_fee_drag_simulator quickstart-check --output demo
python -m portfolio_fee_drag_simulator fixture-doctor --output demo
python -m portfolio_fee_drag_simulator package-audit --root . --output demo
python -m portfolio_fee_drag_simulator visual-receipt --output demo
python -m portfolio_fee_drag_simulator cold-start-walkthrough --output demo
python -m portfolio_fee_drag_simulator decision-journal --output demo
python -m portfolio_fee_drag_simulator artifact-catalog --output demo
python -m portfolio_fee_drag_simulator public-scan --root . --output demo/public_scan.json
python -m portfolio_fee_drag_simulator release-manifest --root . --output demo/release_manifest.json
python -m portfolio_fee_drag_simulator release-audit-summary --output demo --tests-status pass
```

No GitHub Actions workflows are included.
