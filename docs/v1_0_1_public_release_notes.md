# v1.0.1 Public Release Notes Evidence

Review date: 2026-07-17  
Package: `portfolio-fee-drag-simulator`  
Version: `1.0.1`  
Python: `>=3.11`  
Runtime dependencies: none

## Release Status

No P0/P1 issue was identified in the v1.0.1 release readiness review or cold-start user journey review. No runtime behavior was changed for this release evidence pass.

This note is public release evidence for the final local assets currently present in `dist/`. It records the final asset names and hashes, the intended user path, install choices, safety boundaries, verification commands, and remaining P2/P3 follow-ups.

## Release URL

Repository remote verified locally:

```text
origin https://github.com/SergioYin/portfolio-fee-drag-simulator.git
```

Derived release URL:

```text
https://github.com/SergioYin/portfolio-fee-drag-simulator/releases/tag/v1.0.1
```

Remote publication was confirmed after this evidence note by `gh release view v1.0.1 --repo SergioYin/portfolio-fee-drag-simulator --json url,tagName,isDraft,isPrerelease,name,assets` and `git ls-remote --tags origin v1.0.1`. The public release is not a draft or prerelease, and both wheel/sdist assets are uploaded with SHA-256 digests matching the hashes below.

## Final Assets

| Asset | Bytes | SHA-256 |
| --- | ---: | --- |
| `portfolio_fee_drag_simulator-1.0.1-py3-none-any.whl` | 46097 | `389c8ca7463610f40259e818cbb0519f70c230195a740d5a80b5b9ea341f4f9c` |
| `portfolio_fee_drag_simulator-1.0.1.tar.gz` | 50676 | `13c37f2941d99b88e198e9e503246a19e55ec97d3dc480de30a745c0df01eb09` |

Expected GitHub release asset URLs after publication:

```text
https://github.com/SergioYin/portfolio-fee-drag-simulator/releases/download/v1.0.1/portfolio_fee_drag_simulator-1.0.1-py3-none-any.whl
https://github.com/SergioYin/portfolio-fee-drag-simulator/releases/download/v1.0.1/portfolio_fee_drag_simulator-1.0.1.tar.gz
```

## Install Choices

Preferred public wheel install after release assets are attached:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --no-deps https://github.com/SergioYin/portfolio-fee-drag-simulator/releases/download/v1.0.1/portfolio_fee_drag_simulator-1.0.1-py3-none-any.whl
```

Local wheel install from downloaded assets:

```bash
python -m pip install --no-deps dist/portfolio_fee_drag_simulator-1.0.1-py3-none-any.whl
```

Source checkout install, matching the README quickstart:

```bash
git clone https://github.com/SergioYin/portfolio-fee-drag-simulator.git
cd portfolio-fee-drag-simulator
python -m venv .venv
. .venv/bin/activate
python -m pip install -e . --no-deps
```

Source distribution install option:

```bash
python -m pip install --no-deps dist/portfolio_fee_drag_simulator-1.0.1.tar.gz
```

## Concise User Path

1. Install with Python `>=3.11`, preferably from the v1.0.1 wheel.
2. Confirm the console script with `portfolio-fee-drag --version`.
3. Run `portfolio-fee-drag selfcheck`.
4. Generate the deterministic demo with `portfolio-fee-drag quickstart-check --output demo`.
5. Open `demo/showcase.html`.
6. Review `demo/docs_export.md`, `demo/security_boundary_report.md`, `demo/reproducibility_pack.md`, and `demo/promotion_checklist.md` before sharing outputs.
7. Adapt only local CSV/JSON inputs from human-reviewed records; do not add broker credentials, account numbers, secrets, or private personal data to public examples.

## Safety Boundaries

`portfolio-fee-drag-simulator` is for static local scenario review only. It does not fetch live market data, connect to brokerages, place orders, predict returns, optimize portfolios, or provide tax, legal, investment, or buy/sell/hold advice.

Exact boundary used by generated artifacts:

```text
Static local assumptions only; no live data, broker API, orders, predictions, portfolio optimization, tax/legal/investment advice, or buy/sell/hold recommendations.
```

Public release copy should avoid language implying recommendations, optimization, personalized suitability, tax-aware advice, or portfolio advice. Scenario rankings, dollar estimates, and risk flags are deterministic prompts from bundled or user-supplied assumptions, not recommendations.

## Verification Commands

Final verification for this docs evidence pass:

| Check | Command | Result |
| --- | --- | --- |
| Unit tests | `python -m unittest discover -s tests` | pass; 15 tests, `OK` |
| Selfcheck | `python -m portfolio_fee_drag_simulator selfcheck` | pass; JSON status `pass`, version `1.0.1`, no errors |
| Quickstart-check | `python -m portfolio_fee_drag_simulator quickstart-check --output /tmp/pfds_v1_0_1_public_release_notes/quickstart` | pass; `quickstart check complete`, 49 files generated |
| Public-scan | `python -m portfolio_fee_drag_simulator public-scan --root . --output /tmp/pfds_v1_0_1_public_release_notes/public_scan.json` | pass; 65 files scanned, no secret marker findings, finance boundary present |
| Wheel/sdist hashes | `sha256sum dist/portfolio_fee_drag_simulator-1.0.1-py3-none-any.whl dist/portfolio_fee_drag_simulator-1.0.1.tar.gz` | pass; hashes recorded above |
| Release URL check | `git remote -v`; `git ls-remote --tags origin v1.0.1`; `gh release view v1.0.1 --repo SergioYin/portfolio-fee-drag-simulator --json url,tagName,isDraft,isPrerelease,name,assets` | pass; release URL confirmed, tag `v1.0.1`, draft false, prerelease false, both assets uploaded with matching SHA-256 digests |

Prior review evidence read for this release note:

- `README.md`
- `demo/release_manifest.json`
- `demo/selfcheck.json`
- `demo/public_scan.json`
- `demo/release_audit_summary.json`
- `docs/release_readiness_review.md`
- `docs/release_readiness_review.json`
- `docs/cold_start_user_journey_review.md`
- `docs/cold_start_user_journey_review.json`

## Known P2/P3 Follow-Ups

P2 follow-ups:

- Preserve finance boundaries in release notes, screenshots, and promotion copy; do not imply personalized investment analysis.
- Run an external secret scanner such as `gitleaks` or `trufflehog`, including git history if private data may ever have been committed.
- Attach manual wheel smoke evidence to the public release.
- State clearly that wheel installation requires attached release assets or a package index, while source checkout uses `pip install -e .`.
- Use only the final local wheel hash recorded in this note for v1.0.1 evidence.

P3 follow-ups:

- Regenerate the release manifest after the final commit if release owners want the new docs artifacts included in the hash inventory.
- Smoke the sdist in a clean venv before publishing beyond GitHub assets.
- Consider future docs grouping for the dense CLI command list.
- Treat `demo/release_manifest.json` as the broad hash inventory and `demo/visual_receipt.json` as selected visual evidence only.
- Add a manual browser screenshot if promotion requires rendered showcase proof.
- Document that built-in `public-scan` is intentionally simple and does not replace entropy or git-history secret scanning.
