# v1.0.1 Release Readiness Review

Review date: 2026-07-17  
Reviewer stance: skeptical public GitHub reviewer  
Release: `portfolio-fee-drag-simulator` v1.0.1

## Executive Summary

No P0 or P1 issue was found in this review, so no source behavior was changed.

The package is release-ready for a public GitHub v1.0.1 tag if the release owner preserves the current boundary language and attaches fresh verification evidence. The remaining items are P2/P3 promotion and assurance gaps: broader secret scanning, sdist smoke testing, CLI onboarding clarity, and explicit release-note boundaries for finance outputs.

## Verification Evidence

| Check | Result | Evidence |
| --- | --- | --- |
| Unit tests | Pass, 15 tests | `python -m unittest discover -s tests` |
| Selfcheck | Pass | `python -m portfolio_fee_drag_simulator selfcheck` |
| Public scan | Pass | `demo/public_scan.json` |
| Package audit | Pass | `/tmp/pfds_review_audit/package_audit.json` |
| Fixture doctor | Pass | `/tmp/pfds_review_audit/fixture_doctor.json` |
| Security boundary report | Pass | `/tmp/pfds_review_audit/security_boundary_report.json` |
| Wheel build | Pass | `/tmp/pfds_review_dist/portfolio_fee_drag_simulator-1.0.1-py3-none-any.whl` |
| Wheel smoke install | Pass | `/tmp/pfds_review_smoke/bin/portfolio-fee-drag --version`; `/tmp/pfds_review_smoke/bin/python -m portfolio_fee_drag_simulator selfcheck` |

Wheel SHA-256 observed during review: `bf2cf391e8b99a5ee933a6f34a1bd16f561c635f163055ccb10992eb0f53f961`.

## Findings

### RR-001: Reproducibility path is strong, but release proof is still local and transcript-based

Severity: P3  
Category: reproducibility  
Status: follow-up

Evidence:

- `demo/reproducibility_pack.json` reports `status: pass` and lists clone, install, test, build, wheel smoke, and demo regeneration commands.
- `README.md` documents `quickstart-check --output demo` and lists deterministic demo outputs.
- `demo/release_manifest.json` hashes release files, but the manifest must be regenerated after any final docs or demo changes.

Why it matters:

Public reviewers can reproduce the package locally, but there is no hosted release workflow or immutable transcript attached to the tag. That is acceptable for this zero-dependency package, but promotion should not rely only on checked-in generated JSON.

Follow-up:

- Regenerate `demo/release_manifest.json` after the final commit.
- Attach a short release transcript showing tests, selfcheck, quickstart, public scan, wheel build, and wheel smoke.
- Keep the exact Python version in release notes; package metadata requires Python `>=3.11`.

### RR-002: Package install looks good for wheel, but sdist was not independently smoked

Severity: P3  
Category: package install  
Status: follow-up

Evidence:

- `pyproject.toml` declares `version = "1.0.1"`, `requires-python = ">=3.11"`, no runtime dependencies, package data for `data/*.csv` and `data/*.json`, and the `portfolio-fee-drag` script.
- Built wheel contains packaged fixtures under `portfolio_fee_drag_simulator/data/`.
- Clean venv wheel smoke returned `portfolio-fee-drag 1.0.1` and selfcheck `status: pass`.

Why it matters:

Wheel installation is the likely public path and passed. Source distributions can still fail because they exercise a different archive shape.

Follow-up:

- Build and install an sdist in a clean venv before publishing to PyPI or attaching release assets.
- Keep `--no-deps` in smoke commands to preserve the zero-runtime-dependency claim.

### RR-003: CLI discoverability is complete but dense

Severity: P3  
Category: CLI discoverability  
Status: follow-up

Evidence:

- `python -m portfolio_fee_drag_simulator --help` exposes all registered commands.
- `tests/test_cli.py` checks that parser choices match `COMMANDS`.
- `README.md` has command summaries and a quickstart, and `demo/showcase.html` provides a first page for demo artifacts.

Why it matters:

The CLI exposes 29 commands. That is useful for release evidence, but a first-time public reviewer may struggle to distinguish the primary path from supporting audit/report commands.

Follow-up:

- In release notes, lead with the narrow path: install, `quickstart-check`, open `demo/showcase.html`, then run tests/selfcheck/public-scan.
- Consider a future docs-only grouping of commands into "first run", "analysis", and "release owner" sections.

### RR-004: Finance boundaries are prominent, but promotion copy must not overstate the output

Severity: P2  
Category: finance boundaries  
Status: follow-up

Evidence:

- `README.md` states that the tool does not fetch market data, connect to brokerages, place orders, predict returns, optimize portfolios, or provide tax/legal/investment/buy/sell/hold advice.
- `portfolio_fee_drag_simulator/model.py` defines `SAFETY_BOUNDARY`, reused across generated artifacts.
- `demo/risk_flags.json`, `demo/scenario_narrative.json`, and `demo/promotion_checklist.json` repeat no-advice review language.

Why it matters:

The outputs include dollar estimates, rankings, and "risk flags". Those are appropriate as static local scenario prompts, but public promotion could make them look like personalized investment analysis if screenshots or release copy omit the boundary.

Follow-up:

- Release notes and screenshots should include the no-live-data, no-broker, no-advice, no-recommendation boundary.
- Avoid phrases like "optimize fees", "recommended allocation", or "tax-aware advice" in public promotion.
- Keep scenario language framed as deterministic examples from bundled or user-supplied assumptions.

### RR-005: No-network/security posture passes current checks, but scanner depth is limited

Severity: P2  
Category: no-network/security  
Status: follow-up

Evidence:

- `demo/security_boundary_report.json` reports pass for no secrets, no workflows, no network/live data, no broker/API/order execution, zero runtime dependencies, package data, and finance boundaries.
- `demo/public_scan.json` reports `status: pass`.
- `portfolio_fee_drag_simulator/cli.py` scans for direct imports of `requests`, `httpx`, `urllib`, `socket`, `aiohttp`, and `websocket`.
- There are no `.github/workflows` files in the reviewed tree.

Why it matters:

The built-in scan is useful but intentionally simple. It does not perform entropy detection, validate historical commits, or catch every indirect network-capable path.

Follow-up:

- Run an external secret scanner such as `gitleaks` or `trufflehog` before tagging.
- Include git history scanning if this repository has ever held private demo data.
- Consider a future hardening pass that uses Python AST parsing for import checks.

### RR-006: Demo artifact integrity is good, with two scope limits to document

Severity: P3  
Category: demo artifact integrity  
Status: follow-up

Evidence:

- `demo/artifact_catalog.json` is complete and inventories 47 generated demo artifacts.
- `demo/visual_receipt.json` is complete for `dashboard.html`, `case_gallery.md`, `case_gallery.json`, and `case_gallery.html`.
- `demo/showcase.html` is a no-JS static index; observed SHA-256: `cee5e46fdba10a60f392872be29ea20ca7409be494708e1d730750c00132b5b7`.

Why it matters:

The artifact catalog and visual receipt are useful evidence, but they are not a cryptographic release attestation. The visual receipt intentionally covers only selected visual artifacts, while the release manifest is the broader hash source.

Follow-up:

- Treat `demo/release_manifest.json` as the broad release hash inventory.
- Treat `demo/visual_receipt.json` as selected visual evidence only.
- Regenerate quickstart artifacts after any docs or demo changes, then rerun public scan.

### RR-007: Promotion readiness is pass-with-manual-proof

Severity: P2  
Category: promotion risks  
Status: follow-up

Evidence:

- `demo/promotion_checklist.json` reports pass for README, quickstart artifacts, showcase, docs export, package audit, public scan, reproducibility pack, security boundary report, and finance boundaries.
- The same checklist marks "Wheel install check" as `manual`.
- This review performed the manual wheel smoke successfully in `/tmp/pfds_review_smoke`.

Why it matters:

A generated checklist can say "pass" while still requiring release-owner judgment. Public release should include human-readable proof that manual checks actually ran.

Follow-up:

- Attach the wheel smoke command output or summarize it in release notes.
- Do not rely on `release-audit-summary --tests-status pass` unless tests were run after the final commit.
- Keep product behavior unchanged for v1.0.1 unless a true P0/P1 appears.

## P0/P1 Decision

No P0/P1 was identified.

Reasons:

- Core tests and selfcheck pass.
- Wheel install and console script smoke pass in a clean venv.
- No runtime dependencies are declared.
- Security and public scans pass for the current source tree.
- Finance boundary language is consistently present in README, model constants, and generated artifacts.

## Release-Owner Follow-Up Checklist

- Regenerate demo artifacts with `python -m portfolio_fee_drag_simulator quickstart-check --output demo`.
- Rerun `python -m unittest discover -s tests`.
- Rerun `python -m portfolio_fee_drag_simulator selfcheck`.
- Rerun `python -m portfolio_fee_drag_simulator public-scan --root . --output demo/public_scan.json`.
- Build wheel and sdist, then smoke both in clean venvs.
- Run an external secret scanner before tagging.
- Include no-advice/no-live-data boundaries in release notes and screenshots.
