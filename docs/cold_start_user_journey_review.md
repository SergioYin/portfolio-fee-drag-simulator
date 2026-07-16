# v1.0.1 Cold-Start User Journey Review

Review date: 2026-07-17  
Local timestamp: 2026-07-17T03:06:16+08:00  
UTC timestamp: 2026-07-16T19:06:11Z  
Reviewer stance: skeptical first-time public user after release readiness review  
Release under review: `portfolio-fee-drag-simulator` v1.0.1

## Verdict

No P0 or P1 issue was found. No runtime behavior was changed.

The wheel-based cold-start path works when the user has both a repository clone and the v1.0.1 wheel release asset. The first-run flow successfully covers clone, clean venv creation, wheel installation, help, selfcheck, quickstart demo generation, showcase inspection, finance boundary review, generated artifact interpretation, and public-scan.

## Evidence Environment

| Item | Value |
| --- | --- |
| Source workspace | `/home/xjyin/workspace/token-lab/20260717-portfolio-fee-drag-simulator` |
| Fresh local clone | `/tmp/pfds_cold_start_review_20260717/repo` |
| Clean venv | `/tmp/pfds_cold_start_review_20260717/venv` |
| Generated demo evidence | `/tmp/pfds_cold_start_review_20260717/demo` |
| Extra evidence JSON | `/tmp/pfds_cold_start_review_20260717/evidence` |
| Clone commit | `3a09ed0` |
| Wheel installed | `/home/xjyin/workspace/token-lab/20260717-portfolio-fee-drag-simulator/dist/portfolio_fee_drag_simulator-1.0.1-py3-none-any.whl` |
| Wheel SHA-256 | `389c8ca7463610f40259e818cbb0519f70c230195a740d5a80b5b9ea341f4f9c` |

## Journey Commands And Expected Outputs

| Step | Exact command | Expected output observed | Evidence path |
| --- | --- | --- | --- |
| Timestamp | `date -u +%Y-%m-%dT%H:%M:%SZ` | `2026-07-16T19:06:11Z` | terminal transcript |
| Local timestamp | `date +%Y-%m-%dT%H:%M:%S%z` | `2026-07-17T03:06:16+0800` | terminal transcript |
| Clone | `git clone /home/xjyin/workspace/token-lab/20260717-portfolio-fee-drag-simulator /tmp/pfds_cold_start_review_20260717/repo` | `Cloning into ...` then `done.` | `/tmp/pfds_cold_start_review_20260717/repo` |
| Clone revision | `git rev-parse --short HEAD` | `3a09ed0` | `/tmp/pfds_cold_start_review_20260717/repo` |
| Check clone for wheel | `ls -l dist` | `ls: cannot access 'dist': No such file or directory` | terminal transcript |
| Create venv | `python -m venv /tmp/pfds_cold_start_review_20260717/venv` | exit code 0 | `/tmp/pfds_cold_start_review_20260717/venv` |
| Install wheel | `/tmp/pfds_cold_start_review_20260717/venv/bin/python -m pip install --no-deps /home/xjyin/workspace/token-lab/20260717-portfolio-fee-drag-simulator/dist/portfolio_fee_drag_simulator-1.0.1-py3-none-any.whl` | `Successfully installed portfolio-fee-drag-simulator-1.0.1` | installed venv |
| Version | `/tmp/pfds_cold_start_review_20260717/venv/bin/portfolio-fee-drag --version` | `portfolio-fee-drag 1.0.1` | terminal transcript |
| Help | `/tmp/pfds_cold_start_review_20260717/venv/bin/portfolio-fee-drag --help` | usage text plus all command names, including `quickstart-check`, `selfcheck`, and `public-scan` | terminal transcript |
| Module help | `/tmp/pfds_cold_start_review_20260717/venv/bin/python -m portfolio_fee_drag_simulator --help` | same command surface as the console script | terminal transcript |
| Selfcheck | `/tmp/pfds_cold_start_review_20260717/venv/bin/portfolio-fee-drag selfcheck --output /tmp/pfds_cold_start_review_20260717/evidence/selfcheck.json` | JSON with `"status": "pass"`, `"version": "1.0.1"`, and empty errors | `/tmp/pfds_cold_start_review_20260717/evidence/selfcheck.json` |
| Quickstart | `/tmp/pfds_cold_start_review_20260717/venv/bin/portfolio-fee-drag quickstart-check --output /tmp/pfds_cold_start_review_20260717/demo` | many `wrote ...` lines followed by `quickstart check complete` | `/tmp/pfds_cold_start_review_20260717/demo` |
| Artifact count | `find /tmp/pfds_cold_start_review_20260717/demo -type f \| wc -l` | `49` | `/tmp/pfds_cold_start_review_20260717/demo` |
| Open showcase by file path | `sed -n '1,120p' /tmp/pfds_cold_start_review_20260717/demo/showcase.html` | HTML title `Portfolio Fee Drag Public Showcase`, expected links, visible finance boundaries, no script tag in inspected page | `/tmp/pfds_cold_start_review_20260717/demo/showcase.html` |
| Showcase checks | `rg -n "<script\|dashboard.html\|case_gallery.html\|docs_export.md\|security_boundary_report.md\|promotion_checklist.md\|buy/sell/hold\|No live\|Static local" /tmp/pfds_cold_start_review_20260717/demo/showcase.html /tmp/pfds_cold_start_review_20260717/demo/docs_export.md /tmp/pfds_cold_start_review_20260717/demo/artifact_catalog.md` | links and finance boundary text found; no `<script` match found | showcase, docs export, artifact catalog |
| Public scan | `/tmp/pfds_cold_start_review_20260717/venv/bin/portfolio-fee-drag public-scan --root /tmp/pfds_cold_start_review_20260717/repo --output /tmp/pfds_cold_start_review_20260717/evidence/public_scan.json` | `wrote ...public_scan.json`; JSON status `pass` | `/tmp/pfds_cold_start_review_20260717/evidence/public_scan.json` |

## Finance Boundaries Read

The boundary language was visible in README, generated docs, showcase, security boundary report, and selfcheck output.

Observed boundary:

`Static local assumptions only; no live data, broker API, orders, predictions, portfolio optimization, tax/legal/investment advice, or buy/sell/hold recommendations.`

The generated docs also state:

- Static local arithmetic scenario review only.
- No live market data, broker connection, order execution, prediction, portfolio optimization, tax advice, legal advice, investment advice, or buy/sell/hold recommendation.
- Outputs are deterministic examples from local CSV/JSON inputs and are not suitability analysis for any person or account.

## Generated Artifacts Understanding

`quickstart-check` generated 49 files under `/tmp/pfds_cold_start_review_20260717/demo`. `artifact_catalog.json` catalogs 47 generated artifacts and intentionally excludes the catalog files themselves from its hash inventory. Important evidence paths:

- `/tmp/pfds_cold_start_review_20260717/demo/showcase.html`: first page to open.
- `/tmp/pfds_cold_start_review_20260717/demo/docs_export.md`: command, input schema, artifact map, verification, and finance boundary reference.
- `/tmp/pfds_cold_start_review_20260717/demo/artifact_catalog.json`: file routes, byte counts, SHA-256 hashes, producers, roles, and promotion usefulness.
- `/tmp/pfds_cold_start_review_20260717/demo/security_boundary_report.json`: no secrets, no workflows, no network/live data, no broker/API/order execution, zero runtime dependencies, package data, and finance boundary checks.
- `/tmp/pfds_cold_start_review_20260717/demo/public_scan.json`: public-readiness scan created by quickstart.
- `/tmp/pfds_cold_start_review_20260717/evidence/public_scan.json`: explicit public-scan run after quickstart.

## Issue Table

| ID | Severity | Area | Finding | Evidence | Recommended action |
| --- | --- | --- | --- | --- | --- |
| CS-001 | P2 | Wheel onboarding | A fresh repository clone does not include `dist/`, so install-from-wheel requires a separately downloaded or attached v1.0.1 wheel. This is normal release packaging, but the cold-start path is not self-contained from clone alone. | `ls -l dist` in `/tmp/pfds_cold_start_review_20260717/repo` returned `No such file or directory`; wheel install succeeded only from the source workspace release asset path. | In release notes, say whether users should install from PyPI, a GitHub release wheel, or editable source. Keep README quickstart source-install oriented unless wheel distribution is the primary public path. |
| CS-002 | P2 | Release evidence consistency | The wheel used in this cold-start review has SHA-256 `389c8ca7463610f40259e818cbb0519f70c230195a740d5a80b5b9ea341f4f9c`, while `docs/release_readiness_review.md` records a different reviewed wheel SHA from a prior `/tmp` build. This does not prove a product defect, but it weakens release evidence if both are treated as the same artifact. | `sha256sum dist/portfolio_fee_drag_simulator-1.0.1-py3-none-any.whl`; prior release readiness review evidence. | Attach the exact final wheel hash in the release note or final audit transcript. Do not reuse earlier wheel evidence after rebuilding. |
| CS-003 | P3 | Help discoverability | Help renders correctly but exposes 29 commands in a dense single list. A cold-start user can run quickstart, but the primary path competes with release-owner and audit commands. | `portfolio-fee-drag --help` output includes the full command set in one positional list. | In release notes or README, lead with four commands: install, `--help`, `quickstart-check`, and open `demo/showcase.html`. |
| CS-004 | P3 | Showcase opening evidence | The sandbox can inspect the static HTML file but cannot prove an end-user GUI browser render. The file is no-JS, links resolve by static path, and the first 120 lines show the expected content. | `sed -n '1,120p' .../showcase.html`; `rg` checks for expected links and boundary text. | For final promotion, include a screenshot or manual browser note if visual proof is required. |
| CS-005 | P3 | Public scan depth | Built-in public-scan passes, but it is intentionally simple and checks common marker strings plus boundary text. It is not an entropy scanner or git-history scan. | explicit public-scan JSON: 61 files scanned, no secret marker findings, finance boundary present. | Before public tagging, run an external secret scanner if this repository has ever contained private sample data. |

## P0/P1 Decision

No P0/P1 issue was found.

Reasons:

- Wheel installation in a clean venv succeeds with `--no-deps`.
- Console script and `python -m portfolio_fee_drag_simulator` help both work.
- Selfcheck passes for v1.0.1.
- `quickstart-check` completes and generates the expected demo tree.
- The static showcase contains expected links and finance boundary text.
- Explicit public-scan passes with no secret marker findings.
- The observed issues are release evidence and onboarding clarity gaps, not runtime correctness or safety blockers.

## Verification Run After Review Artifacts

The requested final verification commands were run after adding this review:

| Check | Exact command | Result | Evidence path |
| --- | --- | --- | --- |
| Unit tests | `python -m unittest discover -s tests` | Pass, 15 tests, `OK` | terminal transcript |
| Selfcheck | `python -m portfolio_fee_drag_simulator selfcheck` | Pass, JSON status `pass`, version `1.0.1`, empty errors | terminal transcript |
| Quickstart-check | `python -m portfolio_fee_drag_simulator quickstart-check --output /tmp/pfds_cold_start_review_20260717/final_quickstart` | Pass, `quickstart check complete`, 49 files generated | `/tmp/pfds_cold_start_review_20260717/final_quickstart` |
| Public-scan | `python -m portfolio_fee_drag_simulator public-scan --root . --output /tmp/pfds_cold_start_review_20260717/final_public_scan.json` | Pass, 63 files scanned, no secret marker findings, finance boundary present | `/tmp/pfds_cold_start_review_20260717/final_public_scan.json` |
