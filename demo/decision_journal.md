# Decision Journal Prompts

Version: 0.9.0

Boundary: Static local assumptions only; no live data, broker API, orders, predictions, portfolio optimization, tax/legal/investment advice, or buy/sell/hold recommendations.

Packet: `demo/fee_drag_packet.json`
Gallery: `demo/case_gallery.json`
Next review date: ``

## Research Note Prompts

### assumptions_changed

Draft a research-note section named Assumptions Changed. Use only the local packet and gallery artifacts. Compare the packet assumptions against the gallery cases and identify which assumption fields would need a human reviewer to mark as changed. Do not infer live market conditions or make tax, legal, investment, or buy/sell/hold recommendations.

### human_verification

Draft a research-note section named Human Verification Needed. List the inputs a human must verify before sharing: holdings, allocation sum, expense ratios, cash return, gross return, turnover, realized gain, tax rate, taxable allocation, rebalance frequency, contribution timing, and audit statuses. Use public-safe wording and do not imply that the arithmetic is personalized advice.

### no_advice_boundary

Draft a research-note boundary paragraph using this exact boundary: Static local assumptions only; no live data, broker API, orders, predictions, portfolio optimization, tax/legal/investment advice, or buy/sell/hold recommendations. State that the note is a deterministic local scenario review and not tax, legal, investment, or buy/sell/hold advice.

### next_review_date

Add a Next Review Date field in YYYY-MM-DD format for a human reviewer to fill in. Leave the value blank unless a human supplies the date.

## Packet Summary

| Field | Value |
| --- | ---: |
| weighted_expense_ratio | `0.00047` |
| cash_allocation | `0.1` |
| cash_drag_rate | `0.003` |
| turnover_tax_drag_rate | `0.00441` |
| rebalance_drag_rate | `0.0002` |
| total_annual_drag_rate | `0.00808` |
| total_drag | `56388.26` |

## Packet Assumptions

- `annual_contribution: 6000.0`
- `cash_return: 0.02`
- `contribution_timing: beginning`
- `gross_return: 0.05`
- `initial_value: 100000.0`
- `realized_gain_rate: 0.35`
- `rebalance_cost: 0.0002`
- `rebalance_frequency: annual`
- `tax_rate: 0.15`
- `taxable_allocation: 0.7`
- `turnover_rate: 0.12`
- `years: 20`

## Gallery Cases

- Cash-Heavy Waitlist
- High-Turnover Taxable Fund
- Low-Cost ETF

## Audit Statuses

| Source | Schema | Status |
| --- | --- | --- |
| `demo/fixture_doctor.json` | `portfolio-fee-drag-fixture-doctor-v1` | pass |
| `demo/package_audit.json` | `portfolio-fee-drag-package-audit-v1` | pass |
| `demo/visual_receipt.json` | `portfolio-fee-drag-visual-receipt-v1` | present |
| `demo/public_scan.json` | `portfolio-fee-drag-public-scan-v1` | pass |

## Human Verification Needed

- Confirm holdings and allocation sum against the source ledger.
- Confirm expense ratios and cash-like classifications from approved source material.
- Confirm gross return, cash return, turnover, realized gain, tax rate, taxable allocation, rebalance, and contribution timing assumptions.
- Confirm audit artifacts are current for the artifacts being reviewed.
- Confirm the next review date is supplied by a human reviewer.
