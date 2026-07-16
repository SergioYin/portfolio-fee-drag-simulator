# Portfolio Fee Drag Visual Receipt

Version: 0.8.0

Boundary: Static local assumptions only; no live data, broker API, orders, predictions, portfolio optimization, tax/legal/investment advice, or buy/sell/hold recommendations.

| Artifact | Route | Bytes | SHA-256 | Role | Regenerate |
| --- | --- | ---: | --- | --- | --- |
| `dashboard.html` | `file://demo/dashboard.html` | 2808 | `966abc2509c1ee136e95d5d508c871c6f2c786c430c370e943a65a6580a82381` | Standalone dashboard receipt for the bundled packet. | `python -m portfolio_fee_drag_simulator static-dashboard --packet demo/fee_drag_packet.json --output demo/dashboard.html` |
| `case_gallery.md` | `file://demo/case_gallery.md` | 2693 | `4896ca052b5643bbc2d292ddf8cdfa2dee114d3f9e62a213bcc282b014c95e5e` | Markdown comparison gallery for bundled deterministic scenarios. | `python -m portfolio_fee_drag_simulator case-gallery --output demo` |
| `case_gallery.json` | `file://demo/case_gallery.json` | 9655 | `f1583f111c7d31fac76c56ea662aecbc3cecc00211421d06b38e04eab0038de1` | Machine-readable case gallery with complete packet payloads. | `python -m portfolio_fee_drag_simulator case-gallery --output demo` |
| `case_gallery.html` | `file://demo/case_gallery.html` | 2854 | `f96b447afdeabc5b2ced578226d7b9a0366e76bbef18d04658734e5ee09edced` | Standalone HTML gallery for visual review. | `python -m portfolio_fee_drag_simulator case-gallery --output demo` |

## Safety Boundaries

- Static local arithmetic scenario review only.
- No live market data, broker connection, order execution, prediction, optimization, tax advice, legal advice, investment advice, or buy/sell/hold recommendation.
- Hashes identify local artifact bytes; they are not an attestation that assumptions are appropriate for any person or account.
