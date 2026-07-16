# Portfolio Fee Drag Docs Export

Version: 0.8.0

Boundary: Static local assumptions only; no live data, broker API, orders, predictions, portfolio optimization, tax/legal/investment advice, or buy/sell/hold recommendations.

## Commands

| Command | Summary |
| --- | --- |
| `artifact-catalog` | Inventory deterministic demo artifacts with routes, byte counts, SHA-256 hashes, producer commands, roles, and promotion usefulness. |
| `assumption-diff` | Compare two local assumptions JSON files and emit Markdown/JSON field deltas, observed direction, and review impact without advice. |
| `batch-compare` | Rank scenario presets by total annual drag, total dollar drag, cash drag, turnover tax drag, and fee drag with review questions instead of recommendations. |
| `build-packet` | Create Markdown and JSON fee-drag packet artifacts from holdings CSV and assumptions JSON. |
| `case-gallery` | Render deterministic Markdown, JSON, and HTML gallery artifacts from bundled scenario presets. |
| `cold-start-walkthrough` | Write a 10-minute Markdown/JSON first-run guide with expected outputs and safety boundaries. |
| `compare-history` | Compare bundled or supplied historical scenario snapshots in a static Markdown table. |
| `decision-journal` | Generate deterministic Markdown/JSON research-note prompts for human review and no-advice boundaries. |
| `docs-export` | Create deterministic Markdown and JSON public documentation for commands, schemas, artifacts, verification, and finance boundaries. |
| `fixture-doctor` | Validate holdings, assumptions, and scenario preset fixtures with actionable warnings. |
| `input-template` | Write example holdings and assumptions templates plus a README fragment for adapting local CSV/JSON without live data. |
| `maturity-report` | Write a public-readiness checklist for the current release scope. |
| `package-audit` | Inspect zero-dependency metadata, package-data readiness, script wiring, version alignment, and command coverage. |
| `public-scan` | Scan local release files for common secret markers and required finance boundary language. |
| `quickstart-check` | Run the full deterministic demo route and write public-safe demo artifacts. |
| `release-audit-summary` | Combine tests, selfcheck, public scan, manifest, visual receipt, fixture doctor, and package audit status. |
| `release-manifest` | Hash source and demo files for release review. |
| `review-ledger` | Validate and summarize the holdings ledger. |
| `risk-flags` | Read holdings and assumptions and emit Markdown/JSON review prompts for cash, expense, turnover/tax, allocation, horizon, and rebalancing risk flags without recommendations. |
| `scenario-presets` | Write or print bundled deterministic scenario preset JSON. |
| `selfcheck` | Verify CLI wiring, bundled examples, and deterministic calculations. |
| `sensitivity-matrix` | Generate a static fee/return sensitivity table from a packet JSON file. |
| `static-dashboard` | Render a standalone no-service HTML dashboard from a packet JSON file. |
| `static-showcase` | Create a no-JS public showcase page linking key review artifacts with short user-value copy. |
| `visual-receipt` | Hash and summarize visual demo artifacts with local routes, bytes, roles, regeneration commands, and safety boundaries. |

## Input Schema

### Holdings CSV

| Column | Type | Required | Description |
| --- | --- | --- | --- |
| `account` | string | True | Account label used for review grouping. |
| `ticker` | string | True | Ticker or local proxy label; CASH marks cash-like holdings. |
| `name` | string | True | Human-readable holding name. |
| `allocation` | number | True | Portfolio allocation as a decimal; bundled examples sum to 1.0. |
| `expense_ratio` | number | True | Annual expense ratio as a decimal. |

### Assumptions JSON

| Field | Type | Description |
| --- | --- | --- |
| `initial_value` | number | Starting portfolio value. |
| `annual_contribution` | number | Annual contribution used in compounding. |
| `years` | integer | Number of annual compounding periods. |
| `gross_return` | number | Local gross annual return assumption. |
| `cash_return` | number | Local annual return assumption for cash-like holdings. |
| `turnover_rate` | number | Local annual turnover assumption. |
| `realized_gain_rate` | number | Share of turnover treated as realized gains. |
| `tax_rate` | number | Local tax-rate assumption for turnover drag arithmetic. |
| `taxable_allocation` | number | Share of portfolio treated as taxable for turnover drag arithmetic. |
| `rebalance_frequency` | enum: none, annual, quarterly, monthly | Supported rebalance frequency. |
| `rebalance_cost` | number | Cost per rebalance event as a decimal. |
| `contribution_timing` | enum: beginning, end | Whether annual contributions compound for the current year. |

Calculation notes:

- Weighted expense ratio is allocation-weighted across holdings.
- Cash drag is cash-like allocation multiplied by max(gross_return - cash_return, 0).
- Turnover/tax drag is turnover_rate * realized_gain_rate * tax_rate * taxable_allocation.
- Rebalance drag is rebalance_cost multiplied by supported annual event count.

## Artifact Map

| Artifact | Route | Producer | User Value |
| --- | --- | --- | --- |
| `input_templates/holdings_template.csv` | `file://demo/input_templates/holdings_template.csv` | `python -m portfolio_fee_drag_simulator input-template --output demo/input_templates` | Useful for adapting local CSV inputs without live data. |
| `input_templates/assumptions_template.json` | `file://demo/input_templates/assumptions_template.json` | `python -m portfolio_fee_drag_simulator input-template --output demo/input_templates` | Useful for adapting local JSON assumptions without live data. |
| `input_templates/local_inputs_README.md` | `file://demo/input_templates/local_inputs_README.md` | `python -m portfolio_fee_drag_simulator input-template --output demo/input_templates` | Useful for public-safe onboarding to offline inputs. |
| `assumption_diff.md` | `file://demo/assumption_diff.md` | `python -m portfolio_fee_drag_simulator assumption-diff --output demo` | Useful for reviewing local assumption field deltas without advice. |
| `assumption_diff.json` | `file://demo/assumption_diff.json` | `python -m portfolio_fee_drag_simulator assumption-diff --output demo` | Useful for deterministic review workflow handoff without recommendations. |
| `risk_flags.md` | `file://demo/risk_flags.md` | `python -m portfolio_fee_drag_simulator risk-flags --output demo` | Useful for prompting human review of cash, expense, turnover/tax, allocation, horizon, and rebalancing inputs. |
| `risk_flags.json` | `file://demo/risk_flags.json` | `python -m portfolio_fee_drag_simulator risk-flags --output demo` | Useful for deterministic advanced review workflow checks. |
| `fee_drag_packet.md` | `file://demo/fee_drag_packet.md` | `python -m portfolio_fee_drag_simulator build-packet --output demo` | Useful for research-note review and public demo inspection. |
| `fee_drag_packet.json` | `file://demo/fee_drag_packet.json` | `python -m portfolio_fee_drag_simulator build-packet --output demo` | Useful as the canonical deterministic packet input. |
| `sensitivity_matrix.md` | `file://demo/sensitivity_matrix.md` | `python -m portfolio_fee_drag_simulator sensitivity-matrix --packet demo/fee_drag_packet.json --output demo/sensitivity_matrix.md` | Useful for explaining how local assumptions change arithmetic outputs. |
| `history_comparison.md` | `file://demo/history_comparison.md` | `python -m portfolio_fee_drag_simulator compare-history --output demo/history_comparison.md` | Useful for showing deterministic before/after-style review. |
| `review_ledger.md` | `file://demo/review_ledger.md` | `python -m portfolio_fee_drag_simulator review-ledger --output demo/review_ledger.md` | Useful for fixture QA before sharing packet outputs. |
| `dashboard.html` | `file://demo/dashboard.html` | `python -m portfolio_fee_drag_simulator static-dashboard --packet demo/fee_drag_packet.json --output demo/dashboard.html` | Useful for local visual review without a web service. |
| `scenario_presets.json` | `file://demo/scenario_presets.json` | `python -m portfolio_fee_drag_simulator scenario-presets --output demo/scenario_presets.json` | Useful for verifying scenario coverage and reproducibility. |
| `case_gallery.md` | `file://demo/case_gallery.md` | `python -m portfolio_fee_drag_simulator case-gallery --output demo` | Useful for reviewer-friendly scenario comparison. |
| `case_gallery.json` | `file://demo/case_gallery.json` | `python -m portfolio_fee_drag_simulator case-gallery --output demo` | Useful for downstream static review and prompt generation. |
| `case_gallery.html` | `file://demo/case_gallery.html` | `python -m portfolio_fee_drag_simulator case-gallery --output demo` | Useful for public demo inspection without runtime services. |
| `batch_compare.md` | `file://demo/batch_compare.md` | `python -m portfolio_fee_drag_simulator batch-compare --output demo` | Useful for comparing cases with review questions instead of recommendations. |
| `batch_compare.json` | `file://demo/batch_compare.json` | `python -m portfolio_fee_drag_simulator batch-compare --output demo` | Useful for deterministic case sorting across local review dimensions. |
| `visual_receipt.md` | `file://demo/visual_receipt.md` | `python -m portfolio_fee_drag_simulator visual-receipt --output demo` | Useful for promotion review of visual demo assets. |
| `visual_receipt.json` | `file://demo/visual_receipt.json` | `python -m portfolio_fee_drag_simulator visual-receipt --output demo` | Useful for release-owner checks that need hashes and byte counts. |
| `visual_receipt.html` | `file://demo/visual_receipt.html` | `python -m portfolio_fee_drag_simulator visual-receipt --output demo` | Useful for local visual artifact verification. |
| `cold_start_walkthrough.md` | `file://demo/cold_start_walkthrough.md` | `python -m portfolio_fee_drag_simulator cold-start-walkthrough --output demo` | Useful for onboarding and public README validation. |
| `cold_start_walkthrough.json` | `file://demo/cold_start_walkthrough.json` | `python -m portfolio_fee_drag_simulator cold-start-walkthrough --output demo` | Useful for deterministic checklist review. |
| `fixture_doctor.md` | `file://demo/fixture_doctor.md` | `python -m portfolio_fee_drag_simulator fixture-doctor --output demo` | Useful for release readiness review. |
| `fixture_doctor.json` | `file://demo/fixture_doctor.json` | `python -m portfolio_fee_drag_simulator fixture-doctor --output demo` | Useful for automated release-owner status checks. |
| `package_audit.md` | `file://demo/package_audit.md` | `python -m portfolio_fee_drag_simulator package-audit --root . --output demo` | Useful for confirming zero-dependency and command coverage claims. |
| `package_audit.json` | `file://demo/package_audit.json` | `python -m portfolio_fee_drag_simulator package-audit --root . --output demo` | Useful for release-owner status checks. |
| `selfcheck.json` | `file://demo/selfcheck.json` | `python -m portfolio_fee_drag_simulator selfcheck --output demo/selfcheck.json` | Useful as a quick health signal before promotion. |
| `public_scan.json` | `file://demo/public_scan.json` | `python -m portfolio_fee_drag_simulator public-scan --root . --output demo/public_scan.json` | Useful for checking public-safe language and obvious secret markers. |
| `release_manifest.json` | `file://demo/release_manifest.json` | `python -m portfolio_fee_drag_simulator release-manifest --root . --output demo/release_manifest.json` | Useful for release review and reproducibility checks. |
| `release_audit_summary.md` | `file://demo/release_audit_summary.md` | `python -m portfolio_fee_drag_simulator release-audit-summary --output demo --tests-status pass` | Useful for promotion decisions after owner-run tests. |
| `release_audit_summary.json` | `file://demo/release_audit_summary.json` | `python -m portfolio_fee_drag_simulator release-audit-summary --output demo --tests-status pass` | Useful for deterministic release status review. |
| `maturity_report.md` | `file://demo/maturity_report.md` | `python -m portfolio_fee_drag_simulator maturity-report --output demo/maturity_report.md` | Useful for explaining maturity scope and remaining boundaries. |
| `decision_journal.md` | `file://demo/decision_journal.md` | `python -m portfolio_fee_drag_simulator decision-journal --output demo` | Useful for human review of assumptions, verification needs, and boundaries. |
| `decision_journal.json` | `file://demo/decision_journal.json` | `python -m portfolio_fee_drag_simulator decision-journal --output demo` | Useful for deterministic prompt handoff without live data. |
| `docs_export.md` | `file://demo/docs_export.md` | `python -m portfolio_fee_drag_simulator docs-export --output demo` | Useful for first-screen project review and public showcase context. |
| `docs_export.json` | `file://demo/docs_export.json` | `python -m portfolio_fee_drag_simulator docs-export --output demo` | Useful for checking command coverage and artifact map completeness. |
| `showcase.html` | `file://demo/showcase.html` | `python -m portfolio_fee_drag_simulator static-showcase --output demo/showcase.html` | Useful as the first local page to open when evaluating the demo. |

## Verification Commands

- `python -m unittest discover -s tests`
- `python -m portfolio_fee_drag_simulator selfcheck`
- `python -m portfolio_fee_drag_simulator quickstart-check --output demo`
- `python -m portfolio_fee_drag_simulator public-scan --root . --output demo/public_scan.json`

## Finance Boundaries

- Static local arithmetic scenario review only.
- No live market data, broker connection, order execution, prediction, portfolio optimization, tax advice, legal advice, investment advice, or buy/sell/hold recommendation.
- Outputs are deterministic examples from local CSV/JSON inputs and are not suitability analysis for any person or account.
