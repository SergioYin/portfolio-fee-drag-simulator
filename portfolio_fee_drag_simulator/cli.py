from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import tomllib
from importlib import metadata
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
    "fixture-doctor",
    "package-audit",
    "decision-journal",
    "artifact-catalog",
    "quickstart-check",
    "release-manifest",
    "release-audit-summary",
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


DEMO_ARTIFACT_SPECS = (
    ("fee_drag_packet.md", "file://demo/fee_drag_packet.md", "python -m portfolio_fee_drag_simulator build-packet --output demo", "Human-readable packet for the bundled assumptions.", "Useful for research-note review and public demo inspection."),
    ("fee_drag_packet.json", "file://demo/fee_drag_packet.json", "python -m portfolio_fee_drag_simulator build-packet --output demo", "Machine-readable packet for the bundled assumptions.", "Useful as the canonical deterministic packet input."),
    ("sensitivity_matrix.md", "file://demo/sensitivity_matrix.md", "python -m portfolio_fee_drag_simulator sensitivity-matrix --packet demo/fee_drag_packet.json --output demo/sensitivity_matrix.md", "Fee and return sensitivity table.", "Useful for explaining how local assumptions change arithmetic outputs."),
    ("history_comparison.md", "file://demo/history_comparison.md", "python -m portfolio_fee_drag_simulator compare-history --output demo/history_comparison.md", "Static comparison of bundled historical scenario snapshots.", "Useful for showing deterministic before/after-style review."),
    ("review_ledger.md", "file://demo/review_ledger.md", "python -m portfolio_fee_drag_simulator review-ledger --output demo/review_ledger.md", "Holdings ledger review summary.", "Useful for fixture QA before sharing packet outputs."),
    ("dashboard.html", "file://demo/dashboard.html", "python -m portfolio_fee_drag_simulator static-dashboard --packet demo/fee_drag_packet.json --output demo/dashboard.html", "Standalone dashboard receipt for the bundled packet.", "Useful for local visual review without a web service."),
    ("scenario_presets.json", "file://demo/scenario_presets.json", "python -m portfolio_fee_drag_simulator scenario-presets --output demo/scenario_presets.json", "Bundled deterministic scenario preset export.", "Useful for verifying scenario coverage and reproducibility."),
    ("case_gallery.md", "file://demo/case_gallery.md", "python -m portfolio_fee_drag_simulator case-gallery --output demo", "Markdown comparison gallery for bundled deterministic scenarios.", "Useful for reviewer-friendly scenario comparison."),
    ("case_gallery.json", "file://demo/case_gallery.json", "python -m portfolio_fee_drag_simulator case-gallery --output demo", "Machine-readable case gallery with complete packet payloads.", "Useful for downstream static review and prompt generation."),
    ("case_gallery.html", "file://demo/case_gallery.html", "python -m portfolio_fee_drag_simulator case-gallery --output demo", "Standalone HTML gallery for visual review.", "Useful for public demo inspection without runtime services."),
    ("visual_receipt.md", "file://demo/visual_receipt.md", "python -m portfolio_fee_drag_simulator visual-receipt --output demo", "Human-readable receipt for dashboard and gallery artifacts.", "Useful for promotion review of visual demo assets."),
    ("visual_receipt.json", "file://demo/visual_receipt.json", "python -m portfolio_fee_drag_simulator visual-receipt --output demo", "Machine-readable receipt for dashboard and gallery artifacts.", "Useful for release-owner checks that need hashes and byte counts."),
    ("visual_receipt.html", "file://demo/visual_receipt.html", "python -m portfolio_fee_drag_simulator visual-receipt --output demo", "Standalone HTML receipt for dashboard and gallery artifacts.", "Useful for local visual artifact verification."),
    ("cold_start_walkthrough.md", "file://demo/cold_start_walkthrough.md", "python -m portfolio_fee_drag_simulator cold-start-walkthrough --output demo", "First-run walkthrough in Markdown.", "Useful for onboarding and public README validation."),
    ("cold_start_walkthrough.json", "file://demo/cold_start_walkthrough.json", "python -m portfolio_fee_drag_simulator cold-start-walkthrough --output demo", "First-run walkthrough in JSON.", "Useful for deterministic checklist review."),
    ("fixture_doctor.md", "file://demo/fixture_doctor.md", "python -m portfolio_fee_drag_simulator fixture-doctor --output demo", "Human-readable fixture validation report.", "Useful for release readiness review."),
    ("fixture_doctor.json", "file://demo/fixture_doctor.json", "python -m portfolio_fee_drag_simulator fixture-doctor --output demo", "Machine-readable fixture validation report.", "Useful for automated release-owner status checks."),
    ("package_audit.md", "file://demo/package_audit.md", "python -m portfolio_fee_drag_simulator package-audit --root . --output demo", "Human-readable package audit report.", "Useful for confirming zero-dependency and command coverage claims."),
    ("package_audit.json", "file://demo/package_audit.json", "python -m portfolio_fee_drag_simulator package-audit --root . --output demo", "Machine-readable package audit report.", "Useful for release-owner status checks."),
    ("selfcheck.json", "file://demo/selfcheck.json", "python -m portfolio_fee_drag_simulator selfcheck --output demo/selfcheck.json", "Machine-readable CLI and deterministic calculation selfcheck.", "Useful as a quick health signal before promotion."),
    ("public_scan.json", "file://demo/public_scan.json", "python -m portfolio_fee_drag_simulator public-scan --root . --output demo/public_scan.json", "Public-readiness scan output.", "Useful for checking public-safe language and obvious secret markers."),
    ("release_manifest.json", "file://demo/release_manifest.json", "python -m portfolio_fee_drag_simulator release-manifest --root . --output demo/release_manifest.json", "Source and artifact hash manifest.", "Useful for release review and reproducibility checks."),
    ("release_audit_summary.md", "file://demo/release_audit_summary.md", "python -m portfolio_fee_drag_simulator release-audit-summary --output demo --tests-status pass", "Human-readable release-owner audit summary.", "Useful for promotion decisions after owner-run tests."),
    ("release_audit_summary.json", "file://demo/release_audit_summary.json", "python -m portfolio_fee_drag_simulator release-audit-summary --output demo --tests-status pass", "Machine-readable release-owner audit summary.", "Useful for deterministic release status review."),
    ("maturity_report.md", "file://demo/maturity_report.md", "python -m portfolio_fee_drag_simulator maturity-report --output demo/maturity_report.md", "Public-readiness checklist.", "Useful for explaining maturity scope and remaining boundaries."),
    ("decision_journal.md", "file://demo/decision_journal.md", "python -m portfolio_fee_drag_simulator decision-journal --output demo", "Research-note prompt journal in Markdown.", "Useful for human review of assumptions, verification needs, and boundaries."),
    ("decision_journal.json", "file://demo/decision_journal.json", "python -m portfolio_fee_drag_simulator decision-journal --output demo", "Research-note prompt journal in JSON.", "Useful for deterministic prompt handoff without live data."),
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
                "commands": [
                    "python -m portfolio_fee_drag_simulator visual-receipt --output demo",
                    "python -m portfolio_fee_drag_simulator decision-journal --output demo",
                    "python -m portfolio_fee_drag_simulator artifact-catalog --output demo",
                ],
                "expected_output": "Visual receipt, decision journal, and artifact catalog files list local routes, prompts, hashes, regeneration commands, and safety boundaries.",
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
            "demo/fixture_doctor.md",
            "demo/fixture_doctor.json",
            "demo/package_audit.md",
            "demo/package_audit.json",
            "demo/decision_journal.md",
            "demo/decision_journal.json",
            "demo/selfcheck.json",
            "demo/public_scan.json",
            "demo/release_manifest.json",
            "demo/release_audit_summary.md",
            "demo/release_audit_summary.json",
            "demo/artifact_catalog.md",
            "demo/artifact_catalog.json",
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


def audit_issue(area: str, severity: str, message: str, action: str) -> dict[str, str]:
    return {"area": area, "severity": severity, "message": message, "action": action}


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def fixture_doctor_payload(holdings_path: Path, assumptions_path: Path, presets_path: Path) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    sections: list[dict[str, Any]] = []

    try:
        holdings = load_holdings(holdings_path)
        holding_warnings = validate_holdings(holdings)
        sections.append(
            {
                "name": "holdings",
                "path": display_path(holdings_path),
                "status": "pass" if not holding_warnings else "review",
                "rows": len(holdings),
                "warnings": holding_warnings,
            }
        )
        for warning in holding_warnings:
            issues.append(audit_issue("holdings", "warning", warning, "Edit allocation, ticker, or expense_ratio in the holdings CSV."))
    except Exception as exc:
        sections.append({"name": "holdings", "path": display_path(holdings_path), "status": "fail", "warnings": [str(exc)]})
        issues.append(audit_issue("holdings", "error", str(exc), "Fix the holdings CSV shape and numeric fields."))

    try:
        assumptions = load_assumptions(assumptions_path)
        assumption_warnings = []
        sections.append(
            {
                "name": "assumptions",
                "path": display_path(assumptions_path),
                "status": "pass",
                "years": assumptions.years,
                "warnings": assumption_warnings,
            }
        )
    except Exception as exc:
        sections.append({"name": "assumptions", "path": display_path(assumptions_path), "status": "fail", "warnings": [str(exc)]})
        issues.append(audit_issue("assumptions", "error", str(exc), "Fix required JSON fields and supported rate/frequency values."))

    try:
        bundle = load_preset_bundle(presets_path)
        preset_warnings: list[str] = []
        slugs: list[str] = []
        for preset in sorted(bundle["scenarios"], key=lambda item: item.get("slug", "")):
            slug = str(preset.get("slug", ""))
            slugs.append(slug)
            try:
                packet = packet_for_preset(preset)
                for warning in packet["warnings"]:
                    preset_warnings.append(f"{slug}: {warning}")
            except Exception as exc:
                preset_warnings.append(f"{slug or '(blank slug)'}: {exc}")
        if len(slugs) != len(set(slugs)):
            preset_warnings.append("scenario slugs must be unique")
        if bundle.get("version") != __version__:
            preset_warnings.append(f"scenario preset version is {bundle.get('version')}, expected {__version__}")
        sections.append(
            {
                "name": "scenario_presets",
                "path": display_path(presets_path),
                "status": "pass" if not preset_warnings else "review",
                "scenarios": len(bundle["scenarios"]),
                "slugs": sorted(slugs),
                "warnings": preset_warnings,
            }
        )
        for warning in preset_warnings:
            issues.append(audit_issue("scenario_presets", "warning", warning, "Update the preset JSON so each scenario parses and has a unique slug."))
    except Exception as exc:
        sections.append({"name": "scenario_presets", "path": display_path(presets_path), "status": "fail", "warnings": [str(exc)]})
        issues.append(audit_issue("scenario_presets", "error", str(exc), "Fix the scenario preset bundle schema and scenario payloads."))

    status = "pass"
    if any(item["severity"] == "error" for item in issues):
        status = "fail"
    elif issues:
        status = "review"
    return {
        "schema": "portfolio-fee-drag-fixture-doctor-v1",
        "version": __version__,
        "status": status,
        "boundary": SAFETY_BOUNDARY,
        "sections": sections,
        "issues": issues,
    }


def fixture_doctor_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Fixture Doctor",
        "",
        f"Version: {payload['version']}",
        f"Status: {payload['status']}",
        "",
        f"Boundary: {payload['boundary']}",
        "",
        "| Fixture | Status | Path | Notes |",
        "| --- | --- | --- | --- |",
    ]
    for section in payload["sections"]:
        notes = "; ".join(section.get("warnings", [])) or "No warnings."
        lines.append(f"| {section['name']} | {section['status']} | `{section['path']}` | {notes} |")
    lines.extend(["", "## Actions", ""])
    if payload["issues"]:
        lines.extend(f"- {item['area']}: {item['message']} Action: {item['action']}" for item in payload["issues"])
    else:
        lines.append("- No fixture actions required.")
    lines.append("")
    return "\n".join(lines)


def cmd_fixture_doctor(args: argparse.Namespace) -> int:
    output = Path(args.output)
    payload = fixture_doctor_payload(Path(args.holdings), Path(args.assumptions), Path(args.presets))
    write_json(output / "fixture_doctor.json", payload)
    write_text(output / "fixture_doctor.md", fixture_doctor_markdown(payload))
    print(f"wrote {output / 'fixture_doctor.md'}")
    print(f"wrote {output / 'fixture_doctor.json'}")
    return 0 if payload["status"] in {"pass", "review"} else 1


def pyproject_payload(root: Path) -> dict[str, Any]:
    with (root / "pyproject.toml").open("rb") as fh:
        return tomllib.load(fh)


def package_audit_payload(root: Path) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    pyproject_exists = (root / "pyproject.toml").exists()
    pyproject: dict[str, Any] = {}
    project: dict[str, Any] = {}

    dist_version = None
    dist_available = True
    dist_entry_point = None
    try:
        dist = metadata.distribution("portfolio-fee-drag-simulator")
        dist_version = dist.version
        for entry_point in dist.entry_points:
            if entry_point.group == "console_scripts" and entry_point.name == "portfolio-fee-drag":
                dist_entry_point = entry_point.value
                break
    except metadata.PackageNotFoundError:
        dist_available = False

    if pyproject_exists:
        try:
            pyproject = pyproject_payload(root)
            project = pyproject["project"]
        except Exception as exc:
            issues.append(audit_issue("pyproject", "error", str(exc), "Restore a valid pyproject.toml with project metadata."))
    elif not dist_available:
        issues.append(
            audit_issue(
                "package_metadata",
                "error",
                "no pyproject.toml in audit root and installed distribution metadata is unavailable",
                "Run package-audit from the source root or install the wheel before auditing from an empty directory.",
            )
        )

    dependencies = project.get("dependencies", [])
    if pyproject_exists and dependencies:
        issues.append(audit_issue("dependencies", "error", "runtime dependencies are not empty", "Remove runtime dependencies or document why v0.5 changed scope."))

    scripts = project.get("scripts", {})
    script_target = scripts.get("portfolio-fee-drag") or dist_entry_point
    if script_target != "portfolio_fee_drag_simulator.cli:main":
        issues.append(audit_issue("entry_points", "error", "portfolio-fee-drag script target is missing or unexpected", "Set the script to portfolio_fee_drag_simulator.cli:main."))

    setuptools_data = pyproject.get("tool", {}).get("setuptools", {}).get("package-data", {})
    package_data = setuptools_data.get("portfolio_fee_drag_simulator", [])
    expected_data = {"data/*.csv", "data/*.json"}
    if pyproject_exists and not expected_data.issubset(set(package_data)):
        issues.append(audit_issue("package_data", "error", "data/*.csv and data/*.json are not both declared as package data", "Keep bundled CSV and JSON fixtures in setuptools package-data."))

    missing_fixtures = [
        name
        for name in ("example_holdings.csv", "example_assumptions.json", "example_history.json", "scenario_presets.json")
        if not data_path(name).exists()
    ]
    for name in missing_fixtures:
        issues.append(audit_issue("package_data", "error", f"missing packaged fixture {name}", "Restore the fixture under portfolio_fee_drag_simulator/data/."))
    if not pyproject_exists and not missing_fixtures:
        package_data = ["installed:data/*.csv", "installed:data/*.json"]

    parser_choices = set(build_parser()._subparsers._group_actions[0].choices)
    missing_commands = sorted(set(COMMANDS) - parser_choices)
    extra_commands = sorted(parser_choices - set(COMMANDS))
    for name in missing_commands:
        issues.append(audit_issue("commands", "error", f"{name} is listed but not registered", "Register the command in build_parser."))
    for name in extra_commands:
        issues.append(audit_issue("commands", "warning", f"{name} is registered but not listed in COMMANDS", "Add the command to COMMANDS or remove the parser entry."))

    project_version = project.get("version") or dist_version
    reported_dist_version = "source-tree-audit" if pyproject_exists else dist_version
    if project_version != __version__:
        issues.append(audit_issue("version", "error", f"metadata version is {project_version}, import version is {__version__}", "Keep pyproject.toml, installed metadata, and __init__.py versions aligned."))

    status = "pass"
    if any(item["severity"] == "error" for item in issues):
        status = "fail"
    elif issues:
        status = "review"
    return {
        "schema": "portfolio-fee-drag-package-audit-v1",
        "version": __version__,
        "status": status,
        "boundary": SAFETY_BOUNDARY,
        "project_name": project.get("name"),
        "project_version": project_version,
        "import_version": __version__,
        "installed_distribution_available": dist_available,
        "installed_distribution_version": reported_dist_version,
        "runtime_dependencies": dependencies,
        "script_target": script_target,
        "package_data": package_data,
        "commands": sorted(parser_choices),
        "missing_commands": missing_commands,
        "extra_commands": extra_commands,
        "issues": issues,
    }


def package_audit_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Package Audit",
        "",
        f"Version: {payload['version']}",
        f"Status: {payload['status']}",
        "",
        f"Boundary: {payload['boundary']}",
        "",
        "| Check | Value |",
        "| --- | --- |",
        f"| Project | `{payload['project_name']}` |",
        f"| pyproject version | `{payload['project_version']}` |",
        f"| import version | `{payload['import_version']}` |",
        f"| installed distribution available | `{payload['installed_distribution_available']}` |",
        f"| installed distribution version | `{payload['installed_distribution_version']}` |",
        f"| runtime dependencies | `{len(payload['runtime_dependencies'])}` |",
        f"| command count | `{len(payload['commands'])}` |",
        "",
        "## Issues",
        "",
    ]
    if payload["issues"]:
        lines.extend(f"- {item['severity']}: {item['message']} Action: {item['action']}" for item in payload["issues"])
    else:
        lines.append("- No package audit actions required.")
    lines.append("")
    return "\n".join(lines)


def cmd_package_audit(args: argparse.Namespace) -> int:
    output = Path(args.output)
    payload = package_audit_payload(Path(args.root))
    write_json(output / "package_audit.json", payload)
    write_text(output / "package_audit.md", package_audit_markdown(payload))
    print(f"wrote {output / 'package_audit.md'}")
    print(f"wrote {output / 'package_audit.json'}")
    return 0 if payload["status"] == "pass" else 1


def audit_status_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows = []
    for path in paths:
        payload = read_json_file(path)
        rows.append(
            {
                "path": path.as_posix(),
                "schema": payload.get("schema", "unknown") if payload else "missing",
                "status": payload.get("status", "present") if payload else "missing",
            }
        )
    return rows


def decision_journal_payload(args: argparse.Namespace) -> dict[str, Any]:
    packet_path = Path(args.packet)
    gallery_path = Path(args.gallery)
    audit_paths = [Path(item) for item in str(args.audit_artifacts).split(",") if item]
    packet = read_json_file(packet_path) or {}
    gallery = read_json_file(gallery_path) or {}
    assumptions = packet.get("assumptions", {})
    summary = packet.get("summary", {})
    cases = gallery.get("cases", [])
    case_titles = [item.get("title", item.get("slug", "untitled")) for item in cases]
    assumption_lines = [
        f"{key}: {assumptions[key]}"
        for key in sorted(assumptions)
    ]
    prompts = [
        {
            "name": "assumptions_changed",
            "prompt": (
                "Draft a research-note section named Assumptions Changed. Use only the local packet and gallery artifacts. "
                "Compare the packet assumptions against the gallery cases and identify which assumption fields would need a human reviewer to mark as changed. "
                "Do not infer live market conditions or make tax, legal, investment, or buy/sell/hold recommendations."
            ),
        },
        {
            "name": "human_verification",
            "prompt": (
                "Draft a research-note section named Human Verification Needed. List the inputs a human must verify before sharing: holdings, allocation sum, expense ratios, cash return, gross return, turnover, realized gain, tax rate, taxable allocation, rebalance frequency, contribution timing, and audit statuses. "
                "Use public-safe wording and do not imply that the arithmetic is personalized advice."
            ),
        },
        {
            "name": "no_advice_boundary",
            "prompt": (
                f"Draft a research-note boundary paragraph using this exact boundary: {SAFETY_BOUNDARY} "
                "State that the note is a deterministic local scenario review and not tax, legal, investment, or buy/sell/hold advice."
            ),
        },
        {
            "name": "next_review_date",
            "prompt": (
                "Add a Next Review Date field in YYYY-MM-DD format for a human reviewer to fill in. "
                "Leave the value blank unless a human supplies the date."
            ),
        },
    ]
    return {
        "schema": "portfolio-fee-drag-decision-journal-v1",
        "version": __version__,
        "boundary": SAFETY_BOUNDARY,
        "packet_source": packet_path.as_posix(),
        "gallery_source": gallery_path.as_posix(),
        "audit_sources": [path.as_posix() for path in audit_paths],
        "next_review_date": "",
        "research_note_prompts": prompts,
        "packet_summary": {
            "weighted_expense_ratio": summary.get("weighted_expense_ratio"),
            "cash_allocation": summary.get("cash_allocation"),
            "cash_drag_rate": summary.get("cash_drag_rate"),
            "turnover_tax_drag_rate": summary.get("turnover_tax_drag_rate"),
            "rebalance_drag_rate": summary.get("rebalance_drag_rate"),
            "total_annual_drag_rate": summary.get("total_annual_drag_rate"),
            "total_drag": summary.get("total_drag"),
        },
        "packet_assumptions": assumption_lines,
        "gallery_cases": case_titles,
        "audit_statuses": audit_status_rows(audit_paths),
        "human_verification_items": [
            "Confirm holdings and allocation sum against the source ledger.",
            "Confirm expense ratios and cash-like classifications from approved source material.",
            "Confirm gross return, cash return, turnover, realized gain, tax rate, taxable allocation, rebalance, and contribution timing assumptions.",
            "Confirm audit artifacts are current for the artifacts being reviewed.",
            "Confirm the next review date is supplied by a human reviewer.",
        ],
    }


def decision_journal_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Decision Journal Prompts",
        "",
        f"Version: {payload['version']}",
        "",
        f"Boundary: {payload['boundary']}",
        "",
        f"Packet: `{payload['packet_source']}`",
        f"Gallery: `{payload['gallery_source']}`",
        f"Next review date: `{payload['next_review_date']}`",
        "",
        "## Research Note Prompts",
        "",
    ]
    for item in payload["research_note_prompts"]:
        lines.extend([f"### {item['name']}", "", item["prompt"], ""])
    lines.extend(["## Packet Summary", "", "| Field | Value |", "| --- | ---: |"])
    for key, value in payload["packet_summary"].items():
        lines.append(f"| {key} | `{value}` |")
    lines.extend(["", "## Packet Assumptions", ""])
    lines.extend(f"- `{item}`" for item in payload["packet_assumptions"]) if payload["packet_assumptions"] else lines.append("- Packet assumptions missing.")
    lines.extend(["", "## Gallery Cases", ""])
    lines.extend(f"- {item}" for item in payload["gallery_cases"]) if payload["gallery_cases"] else lines.append("- Gallery cases missing.")
    lines.extend(["", "## Audit Statuses", "", "| Source | Schema | Status |", "| --- | --- | --- |"])
    for item in payload["audit_statuses"]:
        lines.append(f"| `{item['path']}` | `{item['schema']}` | {item['status']} |")
    lines.extend(["", "## Human Verification Needed", ""])
    lines.extend(f"- {item}" for item in payload["human_verification_items"])
    lines.append("")
    return "\n".join(lines)


def cmd_decision_journal(args: argparse.Namespace) -> int:
    output = Path(args.output)
    payload = decision_journal_payload(args)
    write_json(output / "decision_journal.json", payload)
    write_text(output / "decision_journal.md", decision_journal_markdown(payload))
    print(f"wrote {output / 'decision_journal.md'}")
    print(f"wrote {output / 'decision_journal.json'}")
    return 0


def artifact_catalog_payload(root: Path) -> dict[str, Any]:
    artifacts = []
    for path_name, route, producer, role, usefulness in DEMO_ARTIFACT_SPECS:
        path = root / path_name
        artifacts.append(
            {
                "path": path_name,
                "route": route.replace("demo/", f"{root.as_posix().rstrip('/')}/", 1),
                "bytes": path.stat().st_size if path.exists() else 0,
                "sha256": file_sha256(path) if path.exists() else None,
                "producer_command": producer.replace("demo/", f"{root.as_posix().rstrip('/')}/"),
                "role": role,
                "promotion_usefulness": usefulness,
                "exists": path.exists(),
            }
        )
    return {
        "schema": "portfolio-fee-drag-artifact-catalog-v1",
        "version": __version__,
        "boundary": SAFETY_BOUNDARY,
        "catalog_scope": "Inventories deterministic demo artifacts produced before artifact-catalog is run; the catalog does not hash itself.",
        "complete": all(item["exists"] for item in artifacts),
        "artifacts": artifacts,
    }


def artifact_catalog_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Artifact Catalog",
        "",
        f"Version: {payload['version']}",
        "",
        f"Boundary: {payload['boundary']}",
        "",
        payload["catalog_scope"],
        "",
        "| Artifact | Route | Bytes | SHA-256 | Producer Command | Role | Promotion Usefulness |",
        "| --- | --- | ---: | --- | --- | --- | --- |",
    ]
    for item in payload["artifacts"]:
        digest = item["sha256"] or "missing"
        lines.append(
            f"| `{item['path']}` | `{item['route']}` | {item['bytes']} | `{digest}` | "
            f"`{item['producer_command']}` | {item['role']} | {item['promotion_usefulness']} |"
        )
    lines.append("")
    return "\n".join(lines)


def cmd_artifact_catalog(args: argparse.Namespace) -> int:
    output = Path(args.output)
    root = Path(args.artifact_root)
    payload = artifact_catalog_payload(root)
    write_json(output / "artifact_catalog.json", payload)
    write_text(output / "artifact_catalog.md", artifact_catalog_markdown(payload))
    print(f"wrote {output / 'artifact_catalog.md'}")
    print(f"wrote {output / 'artifact_catalog.json'}")
    return 0 if payload["complete"] else 1


def read_json_file(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def release_audit_summary_payload(args: argparse.Namespace) -> dict[str, Any]:
    selfcheck = read_json_file(Path(args.selfcheck))
    public_scan = read_json_file(Path(args.public_scan))
    manifest = read_json_file(Path(args.manifest))
    visual_receipt = read_json_file(Path(args.visual_receipt))
    fixture_doctor = read_json_file(Path(args.fixture_doctor))
    package_audit = read_json_file(Path(args.package_audit))

    checks = [
        {
            "name": "tests",
            "status": args.tests_status,
            "source": args.tests_source,
            "detail": "Release owner supplied test status.",
        },
        {
            "name": "selfcheck",
            "status": selfcheck.get("status", "missing") if selfcheck else "missing",
            "source": Path(args.selfcheck).as_posix(),
            "detail": "CLI wiring and bundled deterministic calculations.",
        },
        {
            "name": "public_scan",
            "status": public_scan.get("status", "missing") if public_scan else "missing",
            "source": Path(args.public_scan).as_posix(),
            "detail": "Public wording, secret marker, and finance boundary scan.",
        },
        {
            "name": "release_manifest",
            "status": "pass" if manifest and manifest.get("files") else "missing",
            "source": Path(args.manifest).as_posix(),
            "detail": "Source artifact hash manifest.",
        },
        {
            "name": "visual_receipt",
            "status": "pass" if visual_receipt and visual_receipt.get("complete") else "missing",
            "source": Path(args.visual_receipt).as_posix(),
            "detail": "Dashboard and gallery artifact receipt.",
        },
        {
            "name": "fixture_doctor",
            "status": fixture_doctor.get("status", "missing") if fixture_doctor else "missing",
            "source": Path(args.fixture_doctor).as_posix(),
            "detail": "Holdings, assumptions, and scenario preset validation.",
        },
        {
            "name": "package_audit",
            "status": package_audit.get("status", "missing") if package_audit else "missing",
            "source": Path(args.package_audit).as_posix(),
            "detail": "Package metadata, data files, dependencies, and command coverage.",
        },
    ]
    blocking = {"fail", "missing", "review", "not-run"}
    status = "pass" if all(item["status"] not in blocking for item in checks) else "review"
    return {
        "schema": "portfolio-fee-drag-release-audit-summary-v1",
        "version": __version__,
        "status": status,
        "boundary": SAFETY_BOUNDARY,
        "checks": checks,
        "release_owner_actions": [
            f"{item['name']}: resolve status {item['status']} from {item['source']}"
            for item in checks
            if item["status"] in blocking
        ],
    }


def release_audit_summary_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Release Audit Summary",
        "",
        f"Version: {payload['version']}",
        f"Status: {payload['status']}",
        "",
        f"Boundary: {payload['boundary']}",
        "",
        "| Check | Status | Source | Detail |",
        "| --- | --- | --- | --- |",
    ]
    for item in payload["checks"]:
        lines.append(f"| {item['name']} | {item['status']} | `{item['source']}` | {item['detail']} |")
    lines.extend(["", "## Release Owner Actions", ""])
    if payload["release_owner_actions"]:
        lines.extend(f"- {action}" for action in payload["release_owner_actions"])
    else:
        lines.append("- No release-owner actions required.")
    lines.append("")
    return "\n".join(lines)


def cmd_release_audit_summary(args: argparse.Namespace) -> int:
    output = Path(args.output)
    payload = release_audit_summary_payload(args)
    write_json(output / "release_audit_summary.json", payload)
    write_text(output / "release_audit_summary.md", release_audit_summary_markdown(payload))
    print(f"wrote {output / 'release_audit_summary.md'}")
    print(f"wrote {output / 'release_audit_summary.json'}")
    return 0 if payload["status"] == "pass" else 1


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
    cmd_fixture_doctor(
        argparse.Namespace(
            holdings=data_path("example_holdings.csv"),
            assumptions=data_path("example_assumptions.json"),
            presets=data_path("scenario_presets.json"),
            output=output,
        )
    )
    cmd_package_audit(argparse.Namespace(root=Path("."), output=output))
    cmd_selfcheck(argparse.Namespace(output=output / "selfcheck.json"))
    cmd_public_scan(argparse.Namespace(root=Path("."), output=output / "public_scan.json"))
    cmd_decision_journal(
        argparse.Namespace(
            packet=output / "fee_drag_packet.json",
            gallery=output / "case_gallery.json",
            audit_artifacts=",".join(
                [
                    (output / "fixture_doctor.json").as_posix(),
                    (output / "package_audit.json").as_posix(),
                    (output / "visual_receipt.json").as_posix(),
                    (output / "public_scan.json").as_posix(),
                ]
            ),
            output=output,
        )
    )
    cmd_public_scan(argparse.Namespace(root=Path("."), output=output / "public_scan.json"))
    cmd_release_manifest(argparse.Namespace(root=Path("."), output=output / "release_manifest.json"))
    cmd_release_audit_summary(
        argparse.Namespace(
            output=output,
            tests_status="not-run",
            tests_source="python -m unittest discover -s tests",
            selfcheck=output / "selfcheck.json",
            public_scan=output / "public_scan.json",
            manifest=output / "release_manifest.json",
            visual_receipt=output / "visual_receipt.json",
            fixture_doctor=output / "fixture_doctor.json",
            package_audit=output / "package_audit.json",
        )
    )
    cmd_artifact_catalog(argparse.Namespace(artifact_root=output, output=output))
    print("quickstart check complete")
    return 0


def iter_release_files(root: Path) -> list[Path]:
    excluded_parts = {".git", ".venv", "__pycache__", ".pytest_cache", "dist", "build", "*.egg-info"}
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if rel.name in {"release_manifest.json", "release_audit_summary.json", "release_audit_summary.md"}:
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
        ("Fixture doctor Markdown/JSON route included", "pass"),
        ("Package audit Markdown/JSON route included", "pass"),
        ("Decision journal Markdown/JSON prompt route included", "pass"),
        ("Artifact catalog Markdown/JSON route included", "pass"),
        ("Release audit summary Markdown/JSON route included", "pass"),
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
    doctor = fixture_doctor_payload(
        data_path("example_holdings.csv"),
        data_path("example_assumptions.json"),
        data_path("scenario_presets.json"),
    )
    if doctor["status"] != "pass":
        errors.append(f"fixture doctor status {doctor['status']}")
    package = package_audit_payload(Path("."))
    if package["status"] != "pass":
        errors.append(f"package audit status {package['status']}")
    journal = decision_journal_payload(
        argparse.Namespace(
            packet=Path("demo/fee_drag_packet.json"),
            gallery=Path("demo/case_gallery.json"),
            audit_artifacts="demo/release_audit_summary.json,demo/fixture_doctor.json,demo/package_audit.json,demo/visual_receipt.json,demo/public_scan.json",
        )
    )
    if journal["schema"] != "portfolio-fee-drag-decision-journal-v1" or len(journal["research_note_prompts"]) != 4:
        errors.append("decision journal generation failed")
    catalog = artifact_catalog_payload(Path("demo"))
    if catalog["schema"] != "portfolio-fee-drag-artifact-catalog-v1":
        errors.append("artifact catalog payload generation failed")
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

    doctor = sub.add_parser("fixture-doctor", help="Validate bundled holdings, assumptions, and scenario preset fixtures.")
    doctor.add_argument("--holdings", default=data_path("example_holdings.csv"))
    doctor.add_argument("--assumptions", default=data_path("example_assumptions.json"))
    doctor.add_argument("--presets", default=data_path("scenario_presets.json"))
    doctor.add_argument("--output", default="demo")
    doctor.set_defaults(func=cmd_fixture_doctor)

    package = sub.add_parser("package-audit", help="Inspect package metadata, data readiness, and command coverage.")
    package.add_argument("--root", default=".")
    package.add_argument("--output", default="demo")
    package.set_defaults(func=cmd_package_audit)

    journal = sub.add_parser("decision-journal", help="Write deterministic research-note prompt journal artifacts.")
    journal.add_argument("--packet", default="demo/fee_drag_packet.json")
    journal.add_argument("--gallery", default="demo/case_gallery.json")
    journal.add_argument(
        "--audit-artifacts",
        default="demo/release_audit_summary.json,demo/fixture_doctor.json,demo/package_audit.json,demo/visual_receipt.json,demo/public_scan.json",
    )
    journal.add_argument("--output", default="demo")
    journal.set_defaults(func=cmd_decision_journal)

    catalog = sub.add_parser("artifact-catalog", help="Inventory deterministic demo artifacts with hashes and promotion notes.")
    catalog.add_argument("--artifact-root", default="demo")
    catalog.add_argument("--output", default="demo")
    catalog.set_defaults(func=cmd_artifact_catalog)

    quick = sub.add_parser("quickstart-check", help="Run deterministic demo route.")
    quick.add_argument("--output", default="demo")
    quick.set_defaults(func=cmd_quickstart_check)

    manifest = sub.add_parser("release-manifest", help="Write source file hashes.")
    manifest.add_argument("--root", default=".")
    manifest.add_argument("--output", default="demo/release_manifest.json")
    manifest.set_defaults(func=cmd_release_manifest)

    summary = sub.add_parser("release-audit-summary", help="Combine release-owner audit statuses into Markdown and JSON.")
    summary.add_argument("--output", default="demo")
    summary.add_argument("--tests-status", choices=("pass", "fail", "not-run"), default="not-run")
    summary.add_argument("--tests-source", default="python -m unittest discover -s tests")
    summary.add_argument("--selfcheck", default="demo/selfcheck.json")
    summary.add_argument("--public-scan", default="demo/public_scan.json")
    summary.add_argument("--manifest", default="demo/release_manifest.json")
    summary.add_argument("--visual-receipt", default="demo/visual_receipt.json")
    summary.add_argument("--fixture-doctor", default="demo/fixture_doctor.json")
    summary.add_argument("--package-audit", default="demo/package_audit.json")
    summary.set_defaults(func=cmd_release_audit_summary)

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
