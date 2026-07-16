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
- `demo/release_manifest.json`
- `demo/maturity_report.md`
- `demo/public_scan.json`

## Commands

- `build-packet`: create Markdown and JSON packet artifacts from holdings and assumptions.
- `compare-history`: compare bundled or supplied historical scenario snapshots.
- `sensitivity-matrix`: generate a static fee/return sensitivity table.
- `review-ledger`: validate and summarize a holdings ledger.
- `static-dashboard`: render a standalone HTML dashboard from a packet JSON file.
- `scenario-presets`: write or print bundled scenario preset JSON.
- `case-gallery`: render deterministic Markdown, JSON, and HTML gallery artifacts from scenario presets.
- `quickstart-check`: run the full deterministic demo route.
- `release-manifest`: hash source files for release review.
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

## Scenario Presets and Case Gallery

Version 0.2 bundles three deterministic scenario presets:

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

## Safety Boundaries

This project is for static local scenario review only. It intentionally has no live data and excludes broker APIs, order execution, predictions, portfolio optimization, tax advice, legal advice, investment advice, and buy/sell/hold recommendations.

## Development

```bash
python -m unittest discover -s tests
python -m portfolio_fee_drag_simulator selfcheck
python -m portfolio_fee_drag_simulator quickstart-check --output demo
python -m portfolio_fee_drag_simulator public-scan --root . --output demo/public_scan.json
```

No GitHub Actions workflows are included.
