# Reproducibility Pack

Version: 1.0.1
Status: pass

Boundary: Static local assumptions only; no live data, broker API, orders, predictions, portfolio optimization, tax/legal/investment advice, or buy/sell/hold recommendations.

Source root: `/home/xjyin/workspace/token-lab/20260717-portfolio-fee-drag-simulator`
Repo URL placeholder: `<repo-url>`
Python: Python 3.11 or newer
Runtime dependencies: `0`

## Clone

Commands:

- `git clone <repo-url> portfolio-fee-drag-simulator`
- `cd portfolio-fee-drag-simulator`
- `git status --short`

Expected artifacts:

- `README.md`
- `pyproject.toml`
- `portfolio_fee_drag_simulator/`
- `tests/`

## Install

Commands:

- `python -m venv .venv`
- `. .venv/bin/activate`
- `python -m pip install -e . --no-deps`
- `portfolio-fee-drag --version`

Expected artifacts:

- `.venv/`
- `portfolio_fee_drag_simulator.egg-info/`

## Test

Commands:

- `python -m unittest discover -s tests`
- `python -m portfolio_fee_drag_simulator selfcheck`
- `python -m portfolio_fee_drag_simulator public-scan --root . --output demo/public_scan.json`

Expected artifacts:

- `demo/public_scan.json`

## Build

Commands:

- `python -m pip wheel . --no-deps --no-build-isolation --wheel-dir dist`

Expected artifacts:

- `dist/portfolio_fee_drag_simulator-1.0.1-py3-none-any.whl`

## Wheel Smoke

Commands:

- `python -m venv /tmp/portfolio-fee-drag-smoke`
- `/tmp/portfolio-fee-drag-smoke/bin/python -m pip install dist/portfolio_fee_drag_simulator-1.0.1-py3-none-any.whl --no-deps`
- `/tmp/portfolio-fee-drag-smoke/bin/portfolio-fee-drag --version`
- `/tmp/portfolio-fee-drag-smoke/bin/python -m portfolio_fee_drag_simulator selfcheck`

Expected artifacts:

- `dist/portfolio_fee_drag_simulator-1.0.1-py3-none-any.whl`

## Demo Regeneration

Commands:

- `python -m portfolio_fee_drag_simulator quickstart-check --output demo`
- `python -m portfolio_fee_drag_simulator release-audit-summary --output demo --tests-status pass`
- `python -m portfolio_fee_drag_simulator security-boundary-report --root . --output demo`
- `python -m portfolio_fee_drag_simulator reproducibility-pack --output demo`
- `python -m portfolio_fee_drag_simulator artifact-catalog --artifact-root demo --output demo`
- `python -m portfolio_fee_drag_simulator docs-export --output demo`
- `python -m portfolio_fee_drag_simulator static-showcase --output demo/showcase.html`

Expected artifacts:

- `demo/input_templates/holdings_template.csv`
- `demo/input_templates/assumptions_template.json`
- `demo/input_templates/local_inputs_README.md`
- `demo/assumption_diff.md`
- `demo/assumption_diff.json`
- `demo/risk_flags.md`
- `demo/risk_flags.json`
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
- `demo/batch_compare.md`
- `demo/batch_compare.json`
- `demo/scenario_narrative.md`
- `demo/scenario_narrative.json`
- `demo/visual_receipt.md`
- `demo/visual_receipt.json`
- `demo/visual_receipt.html`
- `demo/cold_start_walkthrough.md`
- `demo/cold_start_walkthrough.json`
- `demo/fixture_doctor.md`
- `demo/fixture_doctor.json`
- `demo/package_audit.md`
- `demo/package_audit.json`
- `demo/selfcheck.json`
- `demo/public_scan.json`
- `demo/release_manifest.json`
- `demo/release_audit_summary.md`
- `demo/release_audit_summary.json`
- `demo/maturity_report.md`
- `demo/decision_journal.md`
- `demo/decision_journal.json`
- `demo/docs_export.md`
- `demo/docs_export.json`
- `demo/reproducibility_pack.md`
- `demo/reproducibility_pack.json`
- `demo/security_boundary_report.md`
- `demo/security_boundary_report.json`
- `demo/promotion_checklist.md`
- `demo/promotion_checklist.json`
- `demo/showcase.html`

## Verification Commands

- `python -m unittest discover -s tests`
- `python -m portfolio_fee_drag_simulator selfcheck`
- `python -m portfolio_fee_drag_simulator quickstart-check --output demo`
- `python -m portfolio_fee_drag_simulator reproducibility-pack --output demo`
- `python -m portfolio_fee_drag_simulator security-boundary-report --root . --output demo`
- `python -m portfolio_fee_drag_simulator public-scan --root . --output demo/public_scan.json`

## Finance Boundaries

- Static local arithmetic scenario review only.
- No live market data, broker connection, order execution, prediction, portfolio optimization, tax advice, legal advice, investment advice, or buy/sell/hold recommendation.
- Outputs are deterministic examples from local CSV/JSON inputs and are not suitability analysis for any person or account.
