# v1.0.1 Source Distribution Smoke Evidence

Date: 2026-07-17

Status: pass

Scope: close the remaining P3 package-install follow-up for the v1.0.1 source distribution. Runtime behavior was not changed.

## Summary

No P0 or P1 install issue appeared. The source distribution installed successfully in a clean virtualenv from an empty command directory, the installed console script reported version 1.0.1, installed `selfcheck` passed, and installed `quickstart-check` completed.

The sandbox blocks network access. A first plain build-isolated `pip install ... --no-deps` attempt failed before package build while pip tried to fetch the declared build backend. The recorded pass path keeps build isolation but points pip at the local `ensurepip` bundled wheel source for `setuptools`; the package install still uses the requested source tarball and `--no-deps`.

## Smoke Root

- Strict smoke root: `/tmp/pfds_v1_0_1_sdist_smoke_20260717_strict`
- Empty command directory: `/tmp/pfds_v1_0_1_sdist_smoke_20260717_strict/empty_strict`
- Virtualenv: `/tmp/pfds_v1_0_1_sdist_smoke_20260717_strict/venv`
- Source distribution: `dist/portfolio_fee_drag_simulator-1.0.1.tar.gz`
- Empty directory check: `find /tmp/pfds_v1_0_1_sdist_smoke_20260717_strict/empty_strict -mindepth 1 -maxdepth 1 -print | sort` printed no paths before and after the smoke commands.

## Commands

| Step | Exact command | Expected output | Observed status |
| --- | --- | --- | --- |
| Create clean venv | `cd /tmp/pfds_v1_0_1_sdist_smoke_20260717_strict/empty_strict && python -m venv /tmp/pfds_v1_0_1_sdist_smoke_20260717_strict/venv` | no stdout/stderr; exit 0 | pass |
| Install sdist | `cd /tmp/pfds_v1_0_1_sdist_smoke_20260717_strict/empty_strict && /tmp/pfds_v1_0_1_sdist_smoke_20260717_strict/venv/bin/python -m pip install --no-index --find-links /home/xjyin/.local/share/uv/python/cpython-3.11.15-linux-x86_64-gnu/lib/python3.11/ensurepip/_bundled /home/xjyin/workspace/token-lab/20260717-portfolio-fee-drag-simulator/dist/portfolio_fee_drag_simulator-1.0.1.tar.gz --no-deps` | `Successfully built portfolio-fee-drag-simulator` and `Successfully installed portfolio-fee-drag-simulator-1.0.1`; exit 0 | pass |
| Version | `cd /tmp/pfds_v1_0_1_sdist_smoke_20260717_strict/empty_strict && /tmp/pfds_v1_0_1_sdist_smoke_20260717_strict/venv/bin/portfolio-fee-drag --version` | `portfolio-fee-drag 1.0.1` | pass |
| Selfcheck | `cd /tmp/pfds_v1_0_1_sdist_smoke_20260717_strict/empty_strict && /tmp/pfds_v1_0_1_sdist_smoke_20260717_strict/venv/bin/portfolio-fee-drag selfcheck --output /tmp/pfds_v1_0_1_sdist_smoke_20260717_strict/selfcheck.json` | JSON with `"status": "pass"`, `"version": "1.0.1"`, and empty `"errors"`; exit 0 | pass |
| Quickstart | `cd /tmp/pfds_v1_0_1_sdist_smoke_20260717_strict/empty_strict && /tmp/pfds_v1_0_1_sdist_smoke_20260717_strict/venv/bin/portfolio-fee-drag quickstart-check --output /tmp/pfds_v1_0_1_sdist_smoke_20260717_strict/quickstart_demo` | terminal output ending with `quickstart check complete`; 49 generated files; exit 0 | pass |
| Unit tests | `python -m unittest discover -s tests` | `Ran 15 tests` and `OK`; exit 0 | pass |
| Public scan | `python -m portfolio_fee_drag_simulator public-scan --root . --output /tmp/pfds_v1_0_1_sdist_smoke_repo_public_scan.json` | JSON with `"status": "pass"`, 67 files scanned, no marker findings, and finance boundary present; exit 0 | pass |

## Hashes

| Artifact | SHA-256 |
| --- | --- |
| `dist/portfolio_fee_drag_simulator-1.0.1.tar.gz` | `13c37f2941d99b88e198e9e503246a19e55ec97d3dc480de30a745c0df01eb09` |
| `/tmp/pfds_v1_0_1_sdist_smoke_20260717_strict/selfcheck.json` | `3117212a19cbd4309b19ad48d5ec8741b85e6c1433c6ee72ca8cdde950a8ca3e` |
| `/tmp/pfds_v1_0_1_sdist_smoke_20260717_strict/quickstart_demo/fee_drag_packet.json` | `4935b05dddbbf2bfc1c89565c1aa75dc6bbb669121f5161584b2835dad6d26e4` |
| `/tmp/pfds_v1_0_1_sdist_smoke_20260717_strict/quickstart_demo/public_scan.json` | `cf2e91ad7012bb46870f7d29b4423116dae00b600cee6575dad3a6cf198b8274` |
| `/tmp/pfds_v1_0_1_sdist_smoke_20260717_strict/quickstart_demo/artifact_catalog.json` | `30466cdfe5bf4b1c79d4e80cb5a16208046f6a439fc52229b8aee11c2fc104f1` |
| `/tmp/pfds_v1_0_1_sdist_smoke_20260717_strict/quickstart_demo/showcase.html` | `cee5e46fdba10a60f392872be29ea20ca7409be494708e1d730750c00132b5b7` |
| `/tmp/pfds_v1_0_1_sdist_smoke_repo_public_scan.json` | `85510dc5bacc2b4bc1a04c685bb908b061c7c992e620d5f3820dba85a7b20129` |

The generated quickstart bundle contained 49 files. Full per-file hashes are in `docs/v1_0_1_sdist_smoke_evidence.json`.

## Notes

- The sdist tarball hash was stable.
- The transient wheel hash printed by pip was `f1b3992d57581ea440adde528d51142a3f1b4d6255749aca306596a53e0a2dee`; this is recorded as build output evidence, not as a release artifact.
- Installed `quickstart-check` generated `public_scan.json` with status `review` because the command was intentionally run from an empty directory with no README boundary text. The command itself exited 0 and produced the expected artifact bundle, so this was not classified as an install issue.
