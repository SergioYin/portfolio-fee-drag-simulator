# Batch Scenario Comparison

Version: 0.9.0

Boundary: Static local assumptions only; no live data, broker API, orders, predictions, portfolio optimization, tax/legal/investment advice, or buy/sell/hold recommendations.

Component dollar drag is allocated from total dollar drag in proportion to each annual drag-rate component.

| Case | Total Annual Drag | Total Dollar Drag | Cash Drag | Turnover/Tax Drag | Fee Drag |
| --- | ---: | ---: | ---: | ---: | ---: |
| Cash-Heavy Waitlist | 1.777% | $297,218.06 | $278,426.37 | $7,336.91 | $11,454.78 |
| High-Turnover Taxable Fund | 7.168% | $777,032.57 | $18,971.85 | $658,594.05 | $88,625.62 |
| Low-Cost ETF | 0.272% | $54,874.59 | $30,317.45 | $13,339.68 | $9,196.29 |

## Ranking: Total Annual Drag

| Rank | Case | Value |
| ---: | --- | ---: |
| 1 | High-Turnover Taxable Fund | 7.168% |
| 2 | Cash-Heavy Waitlist | 1.777% |
| 3 | Low-Cost ETF | 0.272% |

## Ranking: Total Dollar Drag

| Rank | Case | Value |
| ---: | --- | ---: |
| 1 | High-Turnover Taxable Fund | $777,032.57 |
| 2 | Cash-Heavy Waitlist | $297,218.06 |
| 3 | Low-Cost ETF | $54,874.59 |

## Ranking: Cash Drag

| Rank | Case | Value |
| ---: | --- | ---: |
| 1 | Cash-Heavy Waitlist | $278,426.37 |
| 2 | Low-Cost ETF | $30,317.45 |
| 3 | High-Turnover Taxable Fund | $18,971.85 |

## Ranking: Turnover Tax Drag

| Rank | Case | Value |
| ---: | --- | ---: |
| 1 | High-Turnover Taxable Fund | $658,594.05 |
| 2 | Low-Cost ETF | $13,339.68 |
| 3 | Cash-Heavy Waitlist | $7,336.91 |

## Ranking: Fee Drag

| Rank | Case | Value |
| ---: | --- | ---: |
| 1 | High-Turnover Taxable Fund | $88,625.62 |
| 2 | Cash-Heavy Waitlist | $11,454.78 |
| 3 | Low-Cost ETF | $9,196.29 |

## Next-Action Review Questions

- Which input fields changed between local cases, and who verified those fields?
- Do allocations sum to 1.0 and do cash-like rows match the intended local classification?
- Are expense ratios, cash return, gross return, turnover, realized gain, tax rate, taxable allocation, rebalance frequency, rebalance cost, and contribution timing current for this static review?
- Which cases require a human note explaining why the assumptions differ?
- What next review date should a human reviewer enter after validating the local inputs?

These questions are for human review only and are not recommendations.
