# Local Input Template Fragment

Boundary: Static local assumptions only; no live data, broker API, orders, predictions, portfolio optimization, tax/legal/investment advice, or buy/sell/hold recommendations.

Use `holdings_template.csv` and `assumptions_template.json` as offline starter files without live data. Replace the sample labels, allocations, expense ratios, and assumptions with values a human reviewer has approved from local records.

Adaptation checklist:

- Keep holdings columns exactly as `account,ticker,name,allocation,expense_ratio`.
- Enter allocations as decimals and check that they sum to `1.0` before sharing outputs.
- Use `CASH` as the ticker, or include cash-like wording in the holding name, when the row should be counted in cash drag arithmetic.
- Enter expense ratios, returns, turnover, tax, rebalance cost, and taxable allocation as decimals.
- Keep `rebalance_frequency` to one of `none`, `annual`, `quarterly`, or `monthly`.
- Keep `contribution_timing` to `beginning` or `end`.
- Do not paste secrets, account numbers, live data exports, broker credentials, or personally identifying details into templates intended for public demos.
- Treat generated outputs as deterministic local scenario review, not tax, legal, investment, or buy/sell/hold advice.

Example build command after editing local files:

```bash
portfolio-fee-drag build-packet --holdings holdings_template.csv --assumptions assumptions_template.json --output demo/local_packet
```
