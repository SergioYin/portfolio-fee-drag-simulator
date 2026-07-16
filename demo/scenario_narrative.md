# Scenario Narrative

Version: 0.9.0

Boundary: Static local assumptions only; no live data, broker API, orders, predictions, portfolio optimization, tax/legal/investment advice, or buy/sell/hold recommendations.

Case gallery: `demo/case_gallery.json`
Batch compare: `demo/batch_compare.json`

## Cash-Heavy Waitlist

Cash-Heavy Waitlist is a static local scenario over 25 years. It compares a gross future value of $1,032,382.15 with a net future value of $735,164.08 after configured expense, cash, turnover/tax, and rebalance drags.

A staged-deployment scenario with high cash allocation and conservative turnover assumptions.

Key drag drivers:

- Cash Drag contributes 1.665% to the annual drag arithmetic.
- Expense Ratio contributes 0.068% to the annual drag arithmetic.
- Turnover/Tax Drag contributes 0.044% to the annual drag arithmetic.

Rank context:

- Total annual drag rank: `2`
- Total dollar drag rank: `2`
- Cash drag rank: `1`
- Turnover/tax drag rank: `3`
- Fee drag rank: `2`

Questions for human review:

- Do the holdings, allocations, and cash-like classifications match the intended local case?
- Who verified the gross return, cash return, turnover, realized gain, tax rate, taxable allocation, rebalance, and contribution timing assumptions?
- Which driver is largest, and does a human reviewer need to add context for why that input differs from the other bundled cases?
- Is the no-advice boundary visible wherever this scenario is shared?

No-advice boundary: Static local assumptions only; no live data, broker API, orders, predictions, portfolio optimization, tax/legal/investment advice, or buy/sell/hold recommendations.

## High-Turnover Taxable Fund

High-Turnover Taxable Fund is a static local scenario over 25 years. It compares a gross future value of $1,057,702.68 with a net future value of $280,670.11 after configured expense, cash, turnover/tax, and rebalance drags.

A taxable fund-style allocation with higher expense, turnover, realized gains, and quarterly rebalancing assumptions.

Key drag drivers:

- Turnover/Tax Drag contributes 6.075% to the annual drag arithmetic.
- Expense Ratio contributes 0.818% to the annual drag arithmetic.
- Cash Drag contributes 0.175% to the annual drag arithmetic.

Rank context:

- Total annual drag rank: `1`
- Total dollar drag rank: `1`
- Cash drag rank: `3`
- Turnover/tax drag rank: `1`
- Fee drag rank: `1`

Questions for human review:

- Do the holdings, allocations, and cash-like classifications match the intended local case?
- Who verified the gross return, cash return, turnover, realized gain, tax rate, taxable allocation, rebalance, and contribution timing assumptions?
- Which driver is largest, and does a human reviewer need to add context for why that input differs from the other bundled cases?
- Is the no-advice boundary visible wherever this scenario is shared?

No-advice boundary: Static local assumptions only; no live data, broker API, orders, predictions, portfolio optimization, tax/legal/investment advice, or buy/sell/hold recommendations.

## Low-Cost ETF

Low-Cost ETF is a static local scenario over 25 years. It compares a gross future value of $1,057,702.68 with a net future value of $1,002,828.08 after configured expense, cash, turnover/tax, and rebalance drags.

A diversified low-expense ETF-style allocation with modest turnover and limited cash drag.

Key drag drivers:

- Cash Drag contributes 0.150% to the annual drag arithmetic.
- Turnover/Tax Drag contributes 0.066% to the annual drag arithmetic.
- Expense Ratio contributes 0.045% to the annual drag arithmetic.

Rank context:

- Total annual drag rank: `3`
- Total dollar drag rank: `3`
- Cash drag rank: `2`
- Turnover/tax drag rank: `2`
- Fee drag rank: `3`

Questions for human review:

- Do the holdings, allocations, and cash-like classifications match the intended local case?
- Who verified the gross return, cash return, turnover, realized gain, tax rate, taxable allocation, rebalance, and contribution timing assumptions?
- Which driver is largest, and does a human reviewer need to add context for why that input differs from the other bundled cases?
- Is the no-advice boundary visible wherever this scenario is shared?

No-advice boundary: Static local assumptions only; no live data, broker API, orders, predictions, portfolio optimization, tax/legal/investment advice, or buy/sell/hold recommendations.

## Review Note

Narratives are plain-language explanations for human review only; they are not tax, legal, investment, or buy/sell/hold advice.
