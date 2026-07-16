# Cold-Start Walkthrough

Audience: First-time GitHub user with Python 3.11 or newer.
Timebox: 10 minutes

Boundary: Static local assumptions only; no live data, broker API, orders, predictions, portfolio optimization, tax/legal/investment advice, or buy/sell/hold recommendations.

## 0-1: Get the source

Commands:

- `git clone <repo-url>`
- `cd portfolio-fee-drag-simulator`

Expected output: A local folder containing README.md, pyproject.toml, portfolio_fee_drag_simulator/, tests/, and demo/.

## 1-3: Install locally

Commands:

- `python -m venv .venv`
- `. .venv/bin/activate`
- `pip install -e .`

Expected output: The portfolio-fee-drag command is available without installing runtime dependencies.

## 3-5: Generate the deterministic demo

Commands:

- `portfolio-fee-drag quickstart-check --output demo`

Expected output: The command prints wrote lines and ends with quickstart check complete.

## 5-7: Open the visual artifacts

Commands:

- `open demo/showcase.html`
- `open demo/dashboard.html`
- `open demo/case_gallery.html`
- `open demo/visual_receipt.html`

Expected output: A static showcase, dashboard, case gallery, and receipt open from local files. On Linux, use xdg-open instead of open.

## 7-9: Evaluate project health

Commands:

- `python -m unittest discover -s tests`
- `python -m portfolio_fee_drag_simulator selfcheck`
- `python -m portfolio_fee_drag_simulator public-scan --root . --output demo/public_scan.json`

Expected output: Tests pass, selfcheck returns status pass, and public_scan.json has status pass.

## 9-10: Know the boundary before sharing

Commands:

- `python -m portfolio_fee_drag_simulator input-template --output demo/input_templates`
- `python -m portfolio_fee_drag_simulator batch-compare --output demo`
- `python -m portfolio_fee_drag_simulator visual-receipt --output demo`
- `python -m portfolio_fee_drag_simulator decision-journal --output demo`
- `python -m portfolio_fee_drag_simulator docs-export --output demo`
- `python -m portfolio_fee_drag_simulator static-showcase --output demo/showcase.html`
- `python -m portfolio_fee_drag_simulator artifact-catalog --output demo`

Expected output: Input templates, batch comparison, visual receipt, decision journal, docs export, showcase, and artifact catalog files list local routes, prompts, hashes, regeneration commands, review questions, and safety boundaries.

## Expected Artifacts

- `demo/fee_drag_packet.md`
- `demo/fee_drag_packet.json`
- `demo/input_templates/holdings_template.csv`
- `demo/input_templates/assumptions_template.json`
- `demo/input_templates/local_inputs_README.md`
- `demo/dashboard.html`
- `demo/case_gallery.md`
- `demo/case_gallery.json`
- `demo/case_gallery.html`
- `demo/batch_compare.md`
- `demo/batch_compare.json`
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
- `demo/public_scan.json`
- `demo/release_manifest.json`
- `demo/release_audit_summary.md`
- `demo/release_audit_summary.json`
- `demo/artifact_catalog.md`
- `demo/artifact_catalog.json`
- `demo/docs_export.md`
- `demo/docs_export.json`
- `demo/showcase.html`

## Boundaries

- Use only local CSV/JSON assumptions or bundled examples.
- Do not treat output as tax, legal, investment, or buy/sell/hold advice.
- Do not connect this project to broker APIs, live market data, order execution, portfolio optimization, or prediction services.
