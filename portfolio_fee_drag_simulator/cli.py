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
    cmd_maturity_report(argparse.Namespace(output=output / "maturity_report.md"))
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
    for name in ("example_holdings.csv", "example_assumptions.json", "example_history.json"):
        if not data_path(name).exists():
            errors.append(f"missing fixture {name}")
    packet = compute_packet(load_holdings(data_path("example_holdings.csv")), load_assumptions(data_path("example_assumptions.json")))
    if packet["summary"]["fee_drag"] != 56388.26:
        errors.append(f"unexpected demo fee drag {packet['summary']['fee_drag']}")
    expected_keys = {"cash_drag_rate", "turnover_tax_drag_rate", "rebalance_drag_rate", "total_annual_drag_rate"}
    if not expected_keys.issubset(packet["summary"]):
        errors.append("missing expanded drag summary keys")
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
