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

- `open demo/dashboard.html`
- `open demo/case_gallery.html`
- `open demo/visual_receipt.html`

Expected output: A static dashboard, case gallery, and receipt open from local files. On Linux, use xdg-open instead of open.

## 7-9: Evaluate project health

Commands:

- `python -m unittest discover -s tests`
- `python -m portfolio_fee_drag_simulator selfcheck`
- `python -m portfolio_fee_drag_simulator public-scan --root . --output demo/public_scan.json`

Expected output: Tests pass, selfcheck returns status pass, and public_scan.json has status pass.

## 9-10: Know the boundary before sharing

Commands:

- `python -m portfolio_fee_drag_simulator visual-receipt --output demo`

Expected output: visual_receipt.md, visual_receipt.json, and visual_receipt.html list local routes, bytes, hashes, regeneration commands, and safety boundaries.

## Expected Artifacts

- `demo/fee_drag_packet.md`
- `demo/fee_drag_packet.json`
- `demo/dashboard.html`
- `demo/case_gallery.md`
- `demo/case_gallery.json`
- `demo/case_gallery.html`
- `demo/visual_receipt.md`
- `demo/visual_receipt.json`
- `demo/visual_receipt.html`
- `demo/cold_start_walkthrough.md`
- `demo/cold_start_walkthrough.json`

## Boundaries

- Use only local CSV/JSON assumptions or bundled examples.
- Do not treat output as tax, legal, investment, or buy/sell/hold advice.
- Do not connect this project to broker APIs, live market data, order execution, portfolio optimization, or prediction services.
