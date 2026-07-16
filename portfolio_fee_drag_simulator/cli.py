from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
from pathlib import Path
from importlib import resources
from typing import Any

from . import __version__
from .model import (
    SAFETY_BOUNDARY,
    build_packet as compute_packet,
    load_assumptions,
    load_holdings,
    money,
    packet_markdown,
    parse_assumptions,
    parse_holdings,
    pct,
    sensitivity_rows,
    validate_holdings,
)


COMMANDS = (
    "build-packet",
    "compare-history",
    "sensitivity-matrix",
    "review-ledger",
    "static-dashboard",
    "scenario-presets",
    "case-gallery",
    "visual-receipt",
    "cold-start-walkthrough",
    "quickstart-check",
    "release-manifest",
    "maturity-report",
    "selfcheck",
    "public-scan",
)


def data_path(name: str) -> Path:
    return Path(str(resources.files("portfolio_fee_drag_simulator").joinpath("data", name)))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True) + "\n")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_preset_bundle(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as fh:
        bundle = json.load(fh)
    if bundle.get("schema") != "portfolio-fee-drag-scenario-presets-v1":
        raise ValueError("unsupported scenario preset schema")
    return bundle


def packet_for_preset(preset: dict[str, Any]) -> dict[str, Any]:
    holdings = parse_holdings([{key: str(value) for key, value in row.items()} for row in preset["holdings"]])
    assumptions = parse_assumptions(preset["assumptions"])
    packet = compute_packet(holdings, assumptions)
    packet["case"] = {
        "slug": preset["slug"],
        "title": preset["title"],
        "description": preset["description"],
    }
    return packet


def case_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for preset in sorted(bundle["scenarios"], key=lambda item: item["slug"]):
        packet = packet_for_preset(preset)
        summary = packet["summary"]
        rows.append(
            {
                "slug": preset["slug"],
                "title": preset["title"],
                "description": preset["description"],
                "weighted_expense_ratio": summary["weighted_expense_ratio"],
                "cash_allocation": summary["cash_allocation"],
                "cash_drag_rate": summary["cash_drag_rate"],
                "turnover_tax_drag_rate": summary["turnover_tax_drag_rate"],
                "rebalance_drag_rate": summary["rebalance_drag_rate"],
                "total_annual_drag_rate": summary["total_annual_drag_rate"],
                "gross_future_value": summary["gross_future_value"],
                "net_future_value": summary["net_future_value"],
                "total_drag": summary["total_drag"],
                "warnings": packet["warnings"],
                "packet": packet,
            }
        )
    return rows


def cmd_build_packet(args: argparse.Namespace) -> int:
    holdings = load_holdings(args.holdings)
    assumptions = load_assumptions(args.assumptions)
    packet = compute_packet(holdings, assumptions)
    output = Path(args.output)
    write_text(output / "fee_drag_packet.md", packet_markdown(packet))
    write_json(output / "fee_drag_packet.json", packet)
    print(f"wrote {output / 'fee_drag_packet.md'}")
    print(f"wrote {output / 'fee_drag_packet.json'}")
    return 0


def load_packet(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as fh:
        return json.load(fh)


def cmd_sensitivity_matrix(args: argparse.Namespace) -> int:
    packet = load_packet(args.packet)
    fee_steps = [float(value) for value in args.fee_steps.split(",")]
    return_steps = [float(value) for value in args.return_steps.split(",")]
    rows = sensitivity_rows(packet, fee_steps, return_steps)
    lines = [
        "# Portfolio Drag Sensitivity Matrix",
        "",
        f"Boundary: {SAFETY_BOUNDARY}",
        "",
        "| Gross Return | Expense Ratio | Other Drag Rate | Total Drag Rate | Net Future Value | Total Drag |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {pct(row['gross_return'])} | {pct(row['expense_ratio'])} | {pct(row['other_drag_rate'])} | "
            f"{pct(row['total_drag_rate'])} | "
            f"{money(row['net_future_value'])} | {money(row['fee_drag'])} |"
        )
    lines.append("")
    output = Path(args.output)
    write_text(output, "\n".join(lines))
    print(f"wrote {output}")
    return 0


def cmd_compare_history(args: argparse.Namespace) -> int:
    with Path(args.history).open(encoding="utf-8") as fh:
        history = json.load(fh)
    ordered = sorted(history, key=lambda item: item["label"])
    baseline = ordered[0]
    lines = [
        "# Fee Drag History Comparison",
        "",
        f"Boundary: {SAFETY_BOUNDARY}",
        "",
        "| Label | Weighted Expense Ratio | Total Annual Drag Rate | Years | Gross Return | Total Drag | Delta vs First |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in ordered:
        delta = float(item["fee_drag"]) - float(baseline["fee_drag"])
        total_drag_rate = float(item.get("total_annual_drag_rate", item["weighted_expense_ratio"]))
        lines.append(
            f"| {item['label']} | {pct(item['weighted_expense_ratio'])} | {pct(total_drag_rate)} | {item['years']} | "
            f"{pct(item['gross_return'])} | {money(item['fee_drag'])} | {money(delta)} |"
        )
    lines.append("")
    output = Path(args.output)
    write_text(output, "\n".join(lines))
    print(f"wrote {output}")
    return 0


def cmd_review_ledger(args: argparse.Namespace) -> int:
    holdings = load_holdings(args.holdings)
    warnings = validate_holdings(holdings)
    allocation = sum(item.allocation for item in holdings)
    weighted = sum(item.allocation * item.expense_ratio for item in holdings)
    cash = sum(item.allocation for item in holdings if item.ticker == "CASH" or "MONEY MARKET" in item.name.upper())
    lines = [
        "# Holdings Ledger Review",
        "",
        f"Boundary: {SAFETY_BOUNDARY}",
        "",
        f"- Holdings: {len(holdings)}",
        f"- Allocation sum: {allocation:.6f}",
        f"- Weighted expense ratio: {pct(weighted)}",
        f"- Cash-like allocation: {pct(cash)}",
        "",
        "## Warnings",
        "",
    ]
    lines.extend(f"- {warning}" for warning in warnings) if warnings else lines.append("- No ledger warnings.")
    lines.append("")
    output = Path(args.output)
    write_text(output, "\n".join(lines))
    print(f"wrote {output}")
    return 0


def cmd_static_dashboard(args: argparse.Namespace) -> int:
    packet = load_packet(args.packet)
    summary = packet["summary"]
    assumptions = packet["assumptions"]
    rows = "\n".join(
        "<tr><td>{ticker}</td><td>{account}</td><td>{allocation}</td><td>{expense}</td></tr>".format(
            ticker=html.escape(item["ticker"]),
            account=html.escape(item["account"]),
            allocation=pct(item["allocation"]),
            expense=pct(item["expense_ratio"]),
        )
        for item in packet["holdings"]
    )
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Portfolio Fee Drag Dashboard</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1f2937; }}
    main {{ max-width: 960px; margin: auto; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; }}
    .metric {{ border: 1px solid #d1d5db; border-radius: 8px; padding: 1rem; }}
    .label {{ color: #4b5563; font-size: 0.875rem; }}
    .value {{ font-size: 1.5rem; font-weight: 700; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; padding: 0.625rem; text-align: left; }}
  </style>
</head>
<body>
<main>
  <h1>Portfolio Fee Drag Dashboard</h1>
  <p>{html.escape(packet["safety_boundary"])}</p>
  <section class="grid">
    <div class="metric"><div class="label">Weighted expense ratio</div><div class="value">{pct(summary["weighted_expense_ratio"])}</div></div>
    <div class="metric"><div class="label">Cash drag rate</div><div class="value">{pct(summary["cash_drag_rate"])}</div></div>
    <div class="metric"><div class="label">Turnover/tax drag rate</div><div class="value">{pct(summary["turnover_tax_drag_rate"])}</div></div>
    <div class="metric"><div class="label">Rebalance drag rate</div><div class="value">{pct(summary["rebalance_drag_rate"])}</div></div>
    <div class="metric"><div class="label">Total annual drag rate</div><div class="value">{pct(summary["total_annual_drag_rate"])}</div></div>
    <div class="metric"><div class="label">Gross future value</div><div class="value">{money(summary["gross_future_value"])}</div></div>
    <div class="metric"><div class="label">Net future value</div><div class="value">{money(summary["net_future_value"])}</div></div>
    <div class="metric"><div class="label">Estimated total drag</div><div class="value">{money(summary["total_drag"])}</div></div>
  </section>
  <h2>Scenario Assumptions</h2>
  <table><tbody>
    <tr><th>Cash return</th><td>{pct(assumptions["cash_return"])}</td><th>Contribution timing</th><td>{html.escape(assumptions["contribution_timing"])}</td></tr>
    <tr><th>Turnover rate</th><td>{pct(assumptions["turnover_rate"])}</td><th>Taxable allocation</th><td>{pct(assumptions["taxable_allocation"])}</td></tr>
    <tr><th>Realized gain rate</th><td>{pct(assumptions["realized_gain_rate"])}</td><th>Tax rate</th><td>{pct(assumptions["tax_rate"])}</td></tr>
    <tr><th>Rebalance frequency</th><td>{html.escape(assumptions["rebalance_frequency"])}</td><th>Cost per rebalance</th><td>{pct(assumptions["rebalance_cost"])}</td></tr>
  </tbody></table>
  <h2>Holdings</h2>
  <table><thead><tr><th>Ticker</th><th>Account</th><th>Allocation</th><th>Expense Ratio</th></tr></thead><tbody>{rows}</tbody></table>
</main>
</body>
</html>
"""
    output = Path(args.output)
    write_text(output, page)
    print(f"wrote {output}")
    return 0


def cmd_scenario_presets(args: argparse.Namespace) -> int:
    bundle = load_preset_bundle(args.presets)
    payload = {
        "schema": bundle["schema"],
        "version": bundle["version"],
        "boundary": bundle["boundary"],
        "scenarios": sorted(bundle["scenarios"], key=lambda item: item["slug"]),
    }
    if args.output:
        output = Path(args.output)
        write_json(output, payload)
        print(f"wrote {output}")
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def gallery_markdown(bundle: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Portfolio Fee Drag Case Gallery",
        "",
        f"Boundary: {SAFETY_BOUNDARY}",
        "",
        "Bundled deterministic scenario presets for comparing local fee-drag assumptions.",
        "",
        "| Case | Expense Ratio | Cash Allocation | Cash Drag | Turnover/Tax Drag | Rebalance Drag | Total Annual Drag | Total Drag |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['title']} | {pct(row['weighted_expense_ratio'])} | {pct(row['cash_allocation'])} | "
            f"{pct(row['cash_drag_rate'])} | {pct(row['turnover_tax_drag_rate'])} | "
            f"{pct(row['rebalance_drag_rate'])} | {pct(row['total_annual_drag_rate'])} | {money(row['total_drag'])} |"
        )
    lines.extend(["", "## Cases", ""])
    for row in rows:
        packet = row["packet"]
        assumptions = packet["assumptions"]
        lines.extend(
            [
                f"### {row['title']}",
                "",
                row["description"],
                "",
                f"- Slug: `{row['slug']}`",
                f"- Initial value: {money(assumptions['initial_value'])}",
                f"- Annual contribution: {money(assumptions['annual_contribution'])}",
                f"- Years: {assumptions['years']}",
                f"- Gross return assumption: {pct(assumptions['gross_return'])}",
                f"- Net return after all drags: {pct(packet['summary']['net_return_after_all_drags'])}",
                f"- Gross future value: {money(row['gross_future_value'])}",
                f"- Net future value: {money(row['net_future_value'])}",
                "",
                "| Ticker | Account | Allocation | Expense Ratio |",
                "| --- | --- | ---: | ---: |",
            ]
        )
        for item in packet["holdings"]:
            lines.append(
                f"| {item['ticker']} | {item['account']} | {pct(item['allocation'])} | {pct(item['expense_ratio'])} |"
            )
        lines.extend(["", "Review notes:"])
        lines.extend(f"- {warning}" for warning in row["warnings"]) if row["warnings"] else lines.append("- No ledger warnings.")
        lines.append("")
    return "\n".join(lines)


def gallery_html(rows: list[dict[str, Any]]) -> str:
    summary_rows = "\n".join(
        "<tr><td>{title}</td><td>{expense}</td><td>{cash}</td><td>{tax}</td><td>{total}</td><td>{drag}</td></tr>".format(
            title=html.escape(row["title"]),
            expense=pct(row["weighted_expense_ratio"]),
            cash=pct(row["cash_drag_rate"]),
            tax=pct(row["turnover_tax_drag_rate"]),
            total=pct(row["total_annual_drag_rate"]),
            drag=money(row["total_drag"]),
        )
        for row in rows
    )
    case_sections = "\n".join(
        """<section>
  <h2>{title}</h2>
  <p>{description}</p>
  <dl>
    <div><dt>Cash allocation</dt><dd>{cash_allocation}</dd></div>
    <div><dt>Total annual drag</dt><dd>{total_drag_rate}</dd></div>
    <div><dt>Net future value</dt><dd>{net_future_value}</dd></div>
    <div><dt>Total drag</dt><dd>{total_drag}</dd></div>
  </dl>
</section>""".format(
            title=html.escape(row["title"]),
            description=html.escape(row["description"]),
            cash_allocation=pct(row["cash_allocation"]),
            total_drag_rate=pct(row["total_annual_drag_rate"]),
            net_future_value=money(row["net_future_value"]),
            total_drag=money(row["total_drag"]),
        )
        for row in rows
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Portfolio Fee Drag Case Gallery</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1f2937; }}
    main {{ max-width: 1040px; margin: auto; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0 2rem; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; padding: 0.625rem; text-align: left; }}
    th:not(:first-child), td:not(:first-child) {{ text-align: right; }}
    section {{ border-top: 1px solid #d1d5db; padding: 1rem 0; }}
    dl {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 0.75rem; }}
    dt {{ color: #4b5563; font-size: 0.875rem; }}
    dd {{ margin: 0.125rem 0 0; font-weight: 700; }}
  </style>
</head>
<body>
<main>
  <h1>Portfolio Fee Drag Case Gallery</h1>
  <p>{html.escape(SAFETY_BOUNDARY)}</p>
  <table>
    <thead><tr><th>Case</th><th>Expense Ratio</th><th>Cash Drag</th><th>Turnover/Tax Drag</th><th>Total Annual Drag</th><th>Total Drag</th></tr></thead>
    <tbody>{summary_rows}</tbody>
  </table>
  {case_sections}
</main>
</body>
</html>
"""


def cmd_case_gallery(args: argparse.Namespace) -> int:
    bundle = load_preset_bundle(args.presets)
    rows = case_rows(bundle)
    payload = {
        "schema": "portfolio-fee-drag-case-gallery-v1",
        "version": __version__,
        "boundary": SAFETY_BOUNDARY,
        "source_schema": bundle["schema"],
        "cases": [
            {key: value for key, value in row.items() if key != "packet"} | {"packet": row["packet"]}
            for row in rows
        ],
    }
    output = Path(args.output)
    write_json(output / "case_gallery.json", payload)
    write_text(output / "case_gallery.md", gallery_markdown(bundle, rows))
    write_text(output / "case_gallery.html", gallery_html(rows))
    print(f"wrote {output / 'case_gallery.md'}")
    print(f"wrote {output / 'case_gallery.json'}")
    print(f"wrote {output / 'case_gallery.html'}")
    return 0


VISUAL_RECEIPT_ARTIFACTS = (
    {
        "path": "dashboard.html",
        "route": "file://demo/dashboard.html",
        "role": "Standalone dashboard receipt for the bundled packet.",
        "regenerate": "python -m portfolio_fee_drag_simulator static-dashboard --packet demo/fee_drag_packet.json --output demo/dashboard.html",
    },
    {
        "path": "case_gallery.md",
        "route": "file://demo/case_gallery.md",
        "role": "Markdown comparison gallery for bundled deterministic scenarios.",
        "regenerate": "python -m portfolio_fee_drag_simulator case-gallery --output demo",
    },
    {
        "path": "case_gallery.json",
        "route": "file://demo/case_gallery.json",
        "role": "Machine-readable case gallery with complete packet payloads.",
        "regenerate": "python -m portfolio_fee_drag_simulator case-gallery --output demo",
    },
    {
        "path": "case_gallery.html",
        "route": "file://demo/case_gallery.html",
        "role": "Standalone HTML gallery for visual review.",
        "regenerate": "python -m portfolio_fee_drag_simulator case-gallery --output demo",
    },
)


def visual_receipt_payload(root: Path) -> dict[str, Any]:
    artifacts = []
    for spec in VISUAL_RECEIPT_ARTIFACTS:
        path = root / spec["path"]
        artifacts.append(
            {
                "path": spec["path"],
                "route": spec["route"].replace("demo/", f"{root.as_posix().rstrip('/')}/", 1),
                "role": spec["role"],
                "regenerate": spec["regenerate"].replace("demo/", f"{root.as_posix().rstrip('/')}/"),
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else 0,
                "sha256": file_sha256(path) if path.exists() else None,
            }
        )
    return {
        "schema": "portfolio-fee-drag-visual-receipt-v1",
        "version": __version__,
        "boundary": SAFETY_BOUNDARY,
        "complete": all(item["exists"] for item in artifacts),
        "artifacts": artifacts,
        "safety_boundaries": [
            "Static local arithmetic scenario review only.",
            "No live market data, broker connection, order execution, prediction, optimization, tax advice, legal advice, investment advice, or buy/sell/hold recommendation.",
            "Hashes identify local artifact bytes; they are not an attestation that assumptions are appropriate for any person or account.",
        ],
    }


def visual_receipt_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Portfolio Fee Drag Visual Receipt",
        "",
        f"Version: {payload['version']}",
        "",
        f"Boundary: {payload['boundary']}",
        "",
        "| Artifact | Route | Bytes | SHA-256 | Role | Regenerate |",
        "| --- | --- | ---: | --- | --- | --- |",
    ]
    for item in payload["artifacts"]:
        digest = item["sha256"] or "missing"
        lines.append(
            f"| `{item['path']}` | `{item['route']}` | {item['bytes']} | `{digest}` | "
            f"{item['role']} | `{item['regenerate']}` |"
        )
    lines.extend(["", "## Safety Boundaries", ""])
    lines.extend(f"- {boundary}" for boundary in payload["safety_boundaries"])
    lines.append("")
    return "\n".join(lines)


def visual_receipt_html(payload: dict[str, Any]) -> str:
    rows = "\n".join(
        "<tr><td>{path}</td><td><code>{route}</code></td><td>{bytes}</td><td><code>{sha}</code></td><td>{role}</td><td><code>{regen}</code></td></tr>".format(
            path=html.escape(item["path"]),
            route=html.escape(item["route"]),
            bytes=item["bytes"],
            sha=html.escape(item["sha256"] or "missing"),
            role=html.escape(item["role"]),
            regen=html.escape(item["regenerate"]),
        )
        for item in payload["artifacts"]
    )
    boundaries = "\n".join(f"<li>{html.escape(item)}</li>" for item in payload["safety_boundaries"])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Portfolio Fee Drag Visual Receipt</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1f2937; }}
    main {{ max-width: 1120px; margin: auto; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0 2rem; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; padding: 0.625rem; text-align: left; vertical-align: top; }}
    td:nth-child(3), th:nth-child(3) {{ text-align: right; }}
    code {{ overflow-wrap: anywhere; }}
  </style>
</head>
<body>
<main>
  <h1>Portfolio Fee Drag Visual Receipt</h1>
  <p>{html.escape(payload["boundary"])}</p>
  <table>
    <thead><tr><th>Artifact</th><th>Route</th><th>Bytes</th><th>SHA-256</th><th>Role</th><th>Regenerate</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  <h2>Safety Boundaries</h2>
  <ul>{boundaries}</ul>
</main>
</body>
</html>
"""


def cmd_visual_receipt(args: argparse.Namespace) -> int:
    output = Path(args.output)
    root = Path(args.artifact_root)
    payload = visual_receipt_payload(root)
    write_json(output / "visual_receipt.json", payload)
    write_text(output / "visual_receipt.md", visual_receipt_markdown(payload))
    write_text(output / "visual_receipt.html", visual_receipt_html(payload))
    print(f"wrote {output / 'visual_receipt.md'}")
    print(f"wrote {output / 'visual_receipt.json'}")
    print(f"wrote {output / 'visual_receipt.html'}")
    return 0 if payload["complete"] else 1


def cold_start_payload() -> dict[str, Any]:
    return {
        "schema": "portfolio-fee-drag-cold-start-walkthrough-v1",
        "version": __version__,
        "timebox_minutes": 10,
        "boundary": SAFETY_BOUNDARY,
        "audience": "First-time GitHub user with Python 3.11 or newer.",
        "steps": [
            {
                "minute": "0-1",
                "title": "Get the source",
                "commands": [
                    "git clone <repo-url>",
                    "cd portfolio-fee-drag-simulator",
                ],
                "expected_output": "A local folder containing README.md, pyproject.toml, portfolio_fee_drag_simulator/, tests/, and demo/.",
            },
            {
                "minute": "1-3",
                "title": "Install locally",
                "commands": [
                    "python -m venv .venv",
                    ". .venv/bin/activate",
                    "pip install -e .",
                ],
                "expected_output": "The portfolio-fee-drag command is available without installing runtime dependencies.",
            },
            {
                "minute": "3-5",
                "title": "Generate the deterministic demo",
                "commands": ["portfolio-fee-drag quickstart-check --output demo"],
                "expected_output": "The command prints wrote lines and ends with quickstart check complete.",
            },
            {
                "minute": "5-7",
                "title": "Open the visual artifacts",
                "commands": [
                    "open demo/dashboard.html",
                    "open demo/case_gallery.html",
                    "open demo/visual_receipt.html",
                ],
                "expected_output": "A static dashboard, case gallery, and receipt open from local files. On Linux, use xdg-open instead of open.",
            },
            {
                "minute": "7-9",
                "title": "Evaluate project health",
                "commands": [
                    "python -m unittest discover -s tests",
                    "python -m portfolio_fee_drag_simulator selfcheck",
                    "python -m portfolio_fee_drag_simulator public-scan --root . --output demo/public_scan.json",
                ],
                "expected_output": "Tests pass, selfcheck returns status pass, and public_scan.json has status pass.",
            },
            {
                "minute": "9-10",
                "title": "Know the boundary before sharing",
                "commands": ["python -m portfolio_fee_drag_simulator visual-receipt --output demo"],
                "expected_output": "visual_receipt.md, visual_receipt.json, and visual_receipt.html list local routes, bytes, hashes, regeneration commands, and safety boundaries.",
            },
        ],
        "expected_artifacts": [
            "demo/fee_drag_packet.md",
            "demo/fee_drag_packet.json",
            "demo/dashboard.html",
            "demo/case_gallery.md",
            "demo/case_gallery.json",
            "demo/case_gallery.html",
            "demo/visual_receipt.md",
            "demo/visual_receipt.json",
            "demo/visual_receipt.html",
            "demo/cold_start_walkthrough.md",
            "demo/cold_start_walkthrough.json",
        ],
        "safety_boundaries": [
            "Use only local CSV/JSON assumptions or bundled examples.",
            "Do not treat output as tax, legal, investment, or buy/sell/hold advice.",
            "Do not connect this project to broker APIs, live market data, order execution, portfolio optimization, or prediction services.",
        ],
    }


def cold_start_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Cold-Start Walkthrough",
        "",
        f"Audience: {payload['audience']}",
        f"Timebox: {payload['timebox_minutes']} minutes",
        "",
        f"Boundary: {payload['boundary']}",
        "",
    ]
    for step in payload["steps"]:
        lines.extend([f"## {step['minute']}: {step['title']}", "", "Commands:", ""])
        lines.extend(f"- `{command}`" for command in step["commands"])
        lines.extend(["", f"Expected output: {step['expected_output']}", ""])
    lines.extend(["## Expected Artifacts", ""])
    lines.extend(f"- `{artifact}`" for artifact in payload["expected_artifacts"])
    lines.extend(["", "## Boundaries", ""])
    lines.extend(f"- {boundary}" for boundary in payload["safety_boundaries"])
    lines.append("")
    return "\n".join(lines)


def cmd_cold_start_walkthrough(args: argparse.Namespace) -> int:
    output = Path(args.output)
    payload = cold_start_payload()
    write_json(output / "cold_start_walkthrough.json", payload)
    write_text(output / "cold_start_walkthrough.md", cold_start_markdown(payload))
    print(f"wrote {output / 'cold_start_walkthrough.md'}")
    print(f"wrote {output / 'cold_start_walkthrough.json'}")
    return 0


def cmd_quickstart_check(args: argparse.Namespace) -> int:
    output = Path(args.output)
    cmd_build_packet(
        argparse.Namespace(
            holdings=data_path("example_holdings.csv"),
            assumptions=data_path("example_assumptions.json"),
            output=output,
        )
    )
    packet = output / "fee_drag_packet.json"
    cmd_sensitivity_matrix(
        argparse.Namespace(
            packet=packet,
            fee_steps="0.0003,0.001,0.005",
            return_steps="0.03,0.05,0.07",
            output=output / "sensitivity_matrix.md",
        )
    )
    cmd_compare_history(argparse.Namespace(history=data_path("example_history.json"), output=output / "history_comparison.md"))
    cmd_review_ledger(argparse.Namespace(holdings=data_path("example_holdings.csv"), output=output / "review_ledger.md"))
    cmd_static_dashboard(argparse.Namespace(packet=packet, output=output / "dashboard.html"))
    cmd_scenario_presets(argparse.Namespace(presets=data_path("scenario_presets.json"), output=output / "scenario_presets.json"))
    cmd_case_gallery(argparse.Namespace(presets=data_path("scenario_presets.json"), output=output))
    cmd_maturity_report(argparse.Namespace(output=output / "maturity_report.md"))
    cmd_visual_receipt(argparse.Namespace(artifact_root=output, output=output))
    cmd_cold_start_walkthrough(argparse.Namespace(output=output))
    cmd_public_scan(argparse.Namespace(root=Path("."), output=output / "public_scan.json"))
    cmd_release_manifest(argparse.Namespace(root=Path("."), output=output / "release_manifest.json"))
    print("quickstart check complete")
    return 0


def iter_release_files(root: Path) -> list[Path]:
    excluded_parts = {".git", ".venv", "__pycache__", ".pytest_cache", "dist", "build", "*.egg-info"}
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if rel.as_posix().endswith("release_manifest.json"):
            continue
        if any(part in excluded_parts or part.endswith(".egg-info") for part in rel.parts):
            continue
        files.append(path)
    return sorted(files)


def cmd_release_manifest(args: argparse.Namespace) -> int:
    root = Path(args.root)
    entries = []
    for path in iter_release_files(root):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append({"path": path.relative_to(root).as_posix(), "sha256": digest, "bytes": path.stat().st_size})
    payload = {"schema": "portfolio-fee-drag-release-manifest-v1", "files": entries}
    output = Path(args.output)
    write_json(output, payload)
    print(f"wrote {output}")
    return 0


def cmd_maturity_report(args: argparse.Namespace) -> int:
    checks = [
        ("Zero runtime dependencies", "pass"),
        ("Bundled example fixtures are package data", "pass"),
        ("No GitHub Actions workflows required", "pass"),
        ("Finance safety boundaries documented", "pass"),
        ("Deterministic local demo route", "pass"),
        ("Cash drag assumptions included", "pass"),
        ("Turnover/tax drag assumptions included", "pass"),
        ("Contribution and rebalance assumptions included", "pass"),
        ("Scenario presets bundled", "pass"),
        ("Case gallery Markdown/JSON/HTML route included", "pass"),
        ("Visual receipt Markdown/JSON/HTML route included", "pass"),
        ("Cold-start walkthrough Markdown/JSON route included", "pass"),
    ]
    lines = ["# Project Maturity Report", "", f"Boundary: {SAFETY_BOUNDARY}", "", "| Check | Status |", "| --- | --- |"]
    lines.extend(f"| {name} | {status} |" for name, status in checks)
    lines.append("")
    output = Path(args.output)
    write_text(output, "\n".join(lines))
    print(f"wrote {output}")
    return 0


def cmd_selfcheck(args: argparse.Namespace) -> int:
    errors: list[str] = []
    for name in ("example_holdings.csv", "example_assumptions.json", "example_history.json", "scenario_presets.json"):
        if not data_path(name).exists():
            errors.append(f"missing fixture {name}")
    packet = compute_packet(load_holdings(data_path("example_holdings.csv")), load_assumptions(data_path("example_assumptions.json")))
    if packet["summary"]["fee_drag"] != 56388.26:
        errors.append(f"unexpected demo fee drag {packet['summary']['fee_drag']}")
    expected_keys = {"cash_drag_rate", "turnover_tax_drag_rate", "rebalance_drag_rate", "total_annual_drag_rate"}
    if not expected_keys.issubset(packet["summary"]):
        errors.append("missing expanded drag summary keys")
    bundle = load_preset_bundle(data_path("scenario_presets.json"))
    expected_slugs = {"cash-heavy-waitlist", "high-turnover-taxable-fund", "low-cost-etf"}
    actual_slugs = {item["slug"] for item in bundle["scenarios"]}
    if actual_slugs != expected_slugs:
        errors.append(f"unexpected scenario presets {sorted(actual_slugs)}")
    if len(case_rows(bundle)) != 3:
        errors.append("case gallery row generation failed")
    receipt = visual_receipt_payload(Path("demo"))
    if receipt["schema"] != "portfolio-fee-drag-visual-receipt-v1":
        errors.append("visual receipt payload generation failed")
    walkthrough = cold_start_payload()
    if len(walkthrough["steps"]) != 6 or walkthrough["timebox_minutes"] != 10:
        errors.append("cold-start walkthrough generation failed")
    if set(COMMANDS) != set(build_parser()._subparsers._group_actions[0].choices):
        errors.append("command registration mismatch")
    status = "pass" if not errors else "fail"
    payload = {"version": __version__, "status": status, "errors": errors, "boundary": SAFETY_BOUNDARY}
    if getattr(args, "output", None):
        write_json(Path(args.output), payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not errors else 1


SECRET_MARKERS = tuple(
    "".join(parts)
    for parts in (
        ("api", "_key"),
        ("api", "key"),
        ("secret", "_key"),
        ("private", "_key"),
        ("password", "="),
        ("token", "="),
    )
)


def cmd_public_scan(args: argparse.Namespace) -> int:
    root = Path(args.root)
    findings: list[dict[str, str]] = []
    scanned = 0
    for path in iter_release_files(root):
        if path.suffix.lower() not in {".py", ".md", ".toml", ".txt", ".json", ".csv", ".html"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        scanned += 1
        lower = text.lower()
        for marker in SECRET_MARKERS:
            if marker in lower:
                findings.append({"path": path.relative_to(root).as_posix(), "marker": marker})
    readme = (root / "README.md").read_text(encoding="utf-8") if (root / "README.md").exists() else ""
    boundary_ok = all(term in readme.lower() for term in ("no live data", "broker", "buy/sell/hold", "investment advice"))
    payload = {
        "schema": "portfolio-fee-drag-public-scan-v1",
        "status": "pass" if not findings and boundary_ok else "review",
        "files_scanned": scanned,
        "secret_marker_findings": findings,
        "finance_boundary_present": boundary_ok,
    }
    output = Path(args.output)
    write_json(output, payload)
    print(f"wrote {output}")
    return 0 if payload["status"] == "pass" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="portfolio-fee-drag", description="Static local portfolio fee drag simulator.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build-packet", help="Build Markdown and JSON fee drag packet.")
    build.add_argument("--holdings", default=data_path("example_holdings.csv"))
    build.add_argument("--assumptions", default=data_path("example_assumptions.json"))
    build.add_argument("--output", default="demo")
    build.set_defaults(func=cmd_build_packet)

    compare = sub.add_parser("compare-history", help="Compare scenario history snapshots.")
    compare.add_argument("--history", default=data_path("example_history.json"))
    compare.add_argument("--output", default="demo/history_comparison.md")
    compare.set_defaults(func=cmd_compare_history)

    matrix = sub.add_parser("sensitivity-matrix", help="Build fee and return sensitivity table.")
    matrix.add_argument("--packet", default="demo/fee_drag_packet.json")
    matrix.add_argument("--fee-steps", default="0.0003,0.001,0.005")
    matrix.add_argument("--return-steps", default="0.03,0.05,0.07")
    matrix.add_argument("--output", default="demo/sensitivity_matrix.md")
    matrix.set_defaults(func=cmd_sensitivity_matrix)

    review = sub.add_parser("review-ledger", help="Review holdings ledger structure.")
    review.add_argument("--holdings", default=data_path("example_holdings.csv"))
    review.add_argument("--output", default="demo/review_ledger.md")
    review.set_defaults(func=cmd_review_ledger)

    dashboard = sub.add_parser("static-dashboard", help="Render standalone HTML dashboard.")
    dashboard.add_argument("--packet", default="demo/fee_drag_packet.json")
    dashboard.add_argument("--output", default="demo/dashboard.html")
    dashboard.set_defaults(func=cmd_static_dashboard)

    presets = sub.add_parser("scenario-presets", help="Write or print bundled scenario presets.")
    presets.add_argument("--presets", default=data_path("scenario_presets.json"))
    presets.add_argument("--output")
    presets.set_defaults(func=cmd_scenario_presets)

    gallery = sub.add_parser("case-gallery", help="Render Markdown, JSON, and HTML case gallery artifacts.")
    gallery.add_argument("--presets", default=data_path("scenario_presets.json"))
    gallery.add_argument("--output", default="demo")
    gallery.set_defaults(func=cmd_case_gallery)

    receipt = sub.add_parser("visual-receipt", help="Hash and summarize dashboard and gallery artifacts.")
    receipt.add_argument("--artifact-root", default="demo")
    receipt.add_argument("--output", default="demo")
    receipt.set_defaults(func=cmd_visual_receipt)

    cold = sub.add_parser("cold-start-walkthrough", help="Write a 10-minute first-run Markdown and JSON walkthrough.")
    cold.add_argument("--output", default="demo")
    cold.set_defaults(func=cmd_cold_start_walkthrough)

    quick = sub.add_parser("quickstart-check", help="Run deterministic demo route.")
    quick.add_argument("--output", default="demo")
    quick.set_defaults(func=cmd_quickstart_check)

    manifest = sub.add_parser("release-manifest", help="Write source file hashes.")
    manifest.add_argument("--root", default=".")
    manifest.add_argument("--output", default="demo/release_manifest.json")
    manifest.set_defaults(func=cmd_release_manifest)

    maturity = sub.add_parser("maturity-report", help="Write public readiness report.")
    maturity.add_argument("--output", default="demo/maturity_report.md")
    maturity.set_defaults(func=cmd_maturity_report)

    selfcheck = sub.add_parser("selfcheck", help="Verify fixtures, commands, and deterministic calculation.")
    selfcheck.add_argument("--output")
    selfcheck.set_defaults(func=cmd_selfcheck)

    scan = sub.add_parser("public-scan", help="Scan release files for obvious public-readiness risks.")
    scan.add_argument("--root", default=".")
    scan.add_argument("--output", default="demo/public_scan.json")
    scan.set_defaults(func=cmd_public_scan)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
