# Promotion Checklist

Version: 1.0.0
Status: review

Boundary: Static local assumptions only; no live data, broker API, orders, predictions, portfolio optimization, tax/legal/investment advice, or buy/sell/hold recommendations.

| Review Area | Artifact | Status | Human Review Prompt |
| --- | --- | --- | --- |
| README boundary and command coverage | `README.md` | pass | Confirm README documents quickstart, scenario narrative, promotion checklist, and finance boundaries before promotion. |
| Quickstart demo artifacts | `demo` | pass | Run quickstart-check and confirm the generated demo includes showcase, scenario narrative, and promotion checklist artifacts. |
| Static showcase | `demo/showcase.html` | pass | Open demo/showcase.html and confirm it links public-safe review artifacts without JavaScript. |
| Docs export | `demo/docs_export.json` | pass | Confirm docs_export covers commands, input schema, artifact map, verification commands, and finance boundaries. |
| Release audit summary | `demo/release_audit_summary.json` | review | Release owner should rerun release-audit-summary with tests-status pass only after tests have actually run. |
| Package audit and zero dependencies | `demo/package_audit.json` | pass | Confirm package-audit reports zero runtime dependencies, package data, script wiring, version alignment, and command coverage. |
| Public scan | `demo/public_scan.json` | pass | Confirm public-scan passes before sharing public artifacts. |
| Reproducibility pack | `demo/reproducibility_pack.json` | pass | Confirm the pack lists exact local clone, install, test, build, wheel smoke, and demo regeneration commands plus expected artifacts. |
| Security boundary report | `demo/security_boundary_report.json` | pass | Confirm security-boundary-report passes for no secrets, no workflows, no network/live data, no broker/API/order execution, zero runtime dependencies, package data, and finance boundaries. |
| Wheel install check | `dist/*.whl` | manual | Build and install a wheel in a clean environment, then run portfolio-fee-drag --version and portfolio-fee-drag selfcheck. |
| Finance boundaries | `README.md and generated artifacts` | pass | Confirm all public-facing artifacts retain the no live data, no broker, no advice, no recommendation boundary. |

## Manual Items

- Wheel install check is intentionally manual because this zero-dependency repo does not add workflow automation.
- Promotion is a human release-owner decision; generated checks are evidence, not approval.

## Finance Boundaries

- Static local arithmetic scenario review only.
- No live market data, broker connection, order execution, prediction, portfolio optimization, tax advice, legal advice, investment advice, or buy/sell/hold recommendation.
- Outputs are deterministic examples from local CSV/JSON inputs and are not suitability analysis for any person or account.
