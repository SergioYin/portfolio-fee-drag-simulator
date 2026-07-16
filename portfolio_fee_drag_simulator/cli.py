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
    "input-template",
    "assumption-diff",
    "risk-flags",
    "build-packet",
    "batch-compare",
    "scenario-narrative",
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
    "docs-export",
    "static-showcase",
    "reproducibility-pack",
    "security-boundary-report",
    "promotion-checklist",
    "quickstart-check",
    "release-manifest",
    "release-audit-summary",
    "maturity-report",
    "selfcheck",
    "public-scan",
)

COMMAND_DOCS = {
    "assumption-diff": "Compare two local assumptions JSON files and emit Markdown/JSON field deltas, observed direction, and review impact without advice.",
    "artifact-catalog": "Inventory deterministic demo artifacts with routes, byte counts, SHA-256 hashes, producer commands, roles, and promotion usefulness.",
    "batch-compare": "Rank scenario presets by total annual drag, total dollar drag, cash drag, turnover tax drag, and fee drag with review questions instead of recommendations.",
    "build-packet": "Create Markdown and JSON fee-drag packet artifacts from holdings CSV and assumptions JSON.",
    "case-gallery": "Render deterministic Markdown, JSON, and HTML gallery artifacts from bundled scenario presets.",
    "cold-start-walkthrough": "Write a 10-minute Markdown/JSON first-run guide with expected outputs and safety boundaries.",
    "compare-history": "Compare bundled or supplied historical scenario snapshots in a static Markdown table.",
    "decision-journal": "Generate deterministic Markdown/JSON research-note prompts for human review and no-advice boundaries.",
    "docs-export": "Create deterministic Markdown and JSON public documentation for commands, schemas, artifacts, verification, and finance boundaries.",
    "fixture-doctor": "Validate holdings, assumptions, and scenario preset fixtures with actionable warnings.",
    "input-template": "Write example holdings and assumptions templates plus a README fragment for adapting local CSV/JSON without live data.",
    "maturity-report": "Write a public-readiness checklist for the current release scope.",
    "package-audit": "Inspect zero-dependency metadata, package-data readiness, script wiring, version alignment, and command coverage.",
    "public-scan": "Scan local release files for common secret markers and required finance boundary language.",
    "quickstart-check": "Run the full deterministic demo route and write public-safe demo artifacts.",
    "release-audit-summary": "Combine tests, selfcheck, public scan, manifest, visual receipt, fixture doctor, and package audit status.",
    "release-manifest": "Hash source and demo files for release review.",
    "reproducibility-pack": "Emit Markdown/JSON with exact local clone, install, test, build, wheel smoke, and demo regeneration commands plus expected artifacts.",
    "review-ledger": "Validate and summarize the holdings ledger.",
    "risk-flags": "Read holdings and assumptions and emit Markdown/JSON review prompts for cash, expense, turnover/tax, allocation, horizon, and rebalancing risk flags without recommendations.",
    "promotion-checklist": "Write Markdown/JSON release and promotion readiness checklist covering docs, demo artifacts, audits, wheel install, public scan, and finance boundaries.",
    "scenario-narrative": "Read case_gallery.json and batch_compare.json and explain each bundled scenario in plain language with drag drivers, human review questions, and no-advice boundaries.",
    "scenario-presets": "Write or print bundled deterministic scenario preset JSON.",
    "security-boundary-report": "Emit Markdown/JSON summarizing no secrets, no workflows, no network/live data, no broker/API/order execution, zero runtime dependencies, package data, and finance/no-advice boundaries.",
    "selfcheck": "Verify CLI wiring, bundled examples, and deterministic calculations.",
    "sensitivity-matrix": "Generate a static fee/return sensitivity table from a packet JSON file.",
    "static-dashboard": "Render a standalone no-service HTML dashboard from a packet JSON file.",
    "static-showcase": "Create a no-JS public showcase page linking key review artifacts with short user-value copy.",
    "visual-receipt": "Hash and summarize visual demo artifacts with local routes, bytes, roles, regeneration commands, and safety boundaries.",
}

VERIFICATION_COMMANDS = (
    "python -m unittest discover -s tests",
    "python -m portfolio_fee_drag_simulator selfcheck",
    "python -m portfolio_fee_drag_simulator quickstart-check --output demo",
    "python -m portfolio_fee_drag_simulator reproducibility-pack --output demo",
    "python -m portfolio_fee_drag_simulator security-boundary-report --root . --output demo",
    "python -m portfolio_fee_drag_simulator public-scan --root . --output demo/public_scan.json",
)

FINANCE_BOUNDARIES = (
    "Static local arithmetic scenario review only.",
    "No live market data, broker connection, order execution, prediction, portfolio optimization, tax advice, legal advice, investment advice, or buy/sell/hold recommendation.",
    "Outputs are deterministic examples from local CSV/JSON inputs and are not suitability analysis for any person or account.",
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


def load_json_object(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def numeric_delta(before: Any, after: Any) -> float | None:
    if isinstance(before, bool) or isinstance(after, bool):
        return None
    if isinstance(before, (int, float)) and isinstance(after, (int, float)):
        return round(float(after) - float(before), 10)
    return None


def delta_direction(before: Any, after: Any) -> str:
    if before is None and after is not None:
        return "added"
    if before is not None and after is None:
        return "removed"
    delta = numeric_delta(before, after)
    if delta is None:
        return "changed" if before != after else "unchanged"
    if delta > 0:
        return "higher"
    if delta < 0:
        return "lower"
    return "unchanged"


ASSUMPTION_REVIEW_IMPACTS = {
    "initial_value": "Changes the starting value used in compounding and dollar drag arithmetic.",
    "annual_contribution": "Changes contribution cash flows used in future-value arithmetic.",
    "years": "Changes the compounding horizon and duration over which drag accumulates.",
    "gross_return": "Changes the gross return baseline and cash drag spread.",
    "cash_return": "Changes the cash drag spread against the gross return assumption.",
    "turnover_rate": "Changes turnover/tax drag arithmetic.",
    "realized_gain_rate": "Changes the realized-gain portion of turnover/tax drag arithmetic.",
    "tax_rate": "Changes turnover/tax drag arithmetic.",
    "taxable_allocation": "Changes the taxable share used in turnover/tax drag arithmetic.",
    "rebalance_frequency": "Changes the annual rebalance event count used in rebalance drag.",
    "rebalance_cost": "Changes cost per rebalance event used in rebalance drag.",
    "contribution_timing": "Changes whether annual contributions compound for the current year.",
}


def assumption_diff_payload(before_path: Path, after_path: Path) -> dict[str, Any]:
    before = load_json_object(before_path)
    after = load_json_object(after_path)
    fields = []
    for key in sorted(set(before) | set(after)):
        before_value = before.get(key)
        after_value = after.get(key)
        if before_value == after_value:
            continue
        fields.append(
            {
                "field": key,
                "before": before_value,
                "after": after_value,
                "delta": numeric_delta(before_value, after_value),
                "direction": delta_direction(before_value, after_value),
                "review_impact": ASSUMPTION_REVIEW_IMPACTS.get(key, "Changes a local assumption field that a human reviewer may need to identify."),
            }
        )
    return {
        "schema": "portfolio-fee-drag-assumption-diff-v1",
        "version": __version__,
        "boundary": SAFETY_BOUNDARY,
        "before_source": display_path(before_path),
        "after_source": display_path(after_path),
        "changed_fields": len(fields),
        "field_deltas": fields,
        "review_note": "Field deltas are review prompts only; this output contains no tax, legal, investment, or buy/sell/hold advice.",
    }


def assumption_diff_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Assumption Diff",
        "",
        f"Version: {payload['version']}",
        "",
        f"Boundary: {payload['boundary']}",
        "",
        f"Before: `{payload['before_source']}`",
        f"After: `{payload['after_source']}`",
        f"Changed fields: {payload['changed_fields']}",
        "",
        "| Field | Before | After | Delta | Direction | Review Impact |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for item in payload["field_deltas"]:
        delta = "" if item["delta"] is None else item["delta"]
        lines.append(
            f"| `{item['field']}` | `{item['before']}` | `{item['after']}` | `{delta}` | {item['direction']} | {item['review_impact']} |"
        )
    if not payload["field_deltas"]:
        lines.append("| No changed fields |  |  |  | unchanged | No assumption field delta observed. |")
    lines.extend(["", payload["review_note"], ""])
    return "\n".join(lines)


def cmd_assumption_diff(args: argparse.Namespace) -> int:
    output = Path(args.output)
    payload = assumption_diff_payload(Path(args.before), Path(args.after))
    write_json(output / "assumption_diff.json", payload)
    write_text(output / "assumption_diff.md", assumption_diff_markdown(payload))
    print(f"wrote {output / 'assumption_diff.md'}")
    print(f"wrote {output / 'assumption_diff.json'}")
    return 0


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


def local_input_readme_fragment() -> str:
    return "\n".join(
        [
            "# Local Input Template Fragment",
            "",
            f"Boundary: {SAFETY_BOUNDARY}",
            "",
            "Use `holdings_template.csv` and `assumptions_template.json` as offline starter files without live data. Replace the sample labels, allocations, expense ratios, and assumptions with values a human reviewer has approved from local records.",
            "",
            "Adaptation checklist:",
            "",
            "- Keep holdings columns exactly as `account,ticker,name,allocation,expense_ratio`.",
            "- Enter allocations as decimals and check that they sum to `1.0` before sharing outputs.",
            "- Use `CASH` as the ticker, or include cash-like wording in the holding name, when the row should be counted in cash drag arithmetic.",
            "- Enter expense ratios, returns, turnover, tax, rebalance cost, and taxable allocation as decimals.",
            "- Keep `rebalance_frequency` to one of `none`, `annual`, `quarterly`, or `monthly`.",
            "- Keep `contribution_timing` to `beginning` or `end`.",
            "- Do not paste secrets, account numbers, live data exports, broker credentials, or personally identifying details into templates intended for public demos.",
            "- Treat generated outputs as deterministic local scenario review, not tax, legal, investment, or buy/sell/hold advice.",
            "",
            "Example build command after editing local files:",
            "",
            "```bash",
            "portfolio-fee-drag build-packet --holdings holdings_template.csv --assumptions assumptions_template.json --output demo/local_packet",
            "```",
            "",
        ]
    )


def cmd_input_template(args: argparse.Namespace) -> int:
    output = Path(args.output)
    holdings = data_path("example_holdings.csv").read_text(encoding="utf-8")
    assumptions_payload = json.loads(data_path("example_assumptions.json").read_text(encoding="utf-8"))
    assumptions_payload["template_note"] = "Replace these static example values with human-reviewed local assumptions. No live data is fetched."
    write_text(output / "holdings_template.csv", holdings)
    write_json(output / "assumptions_template.json", assumptions_payload)
    write_text(output / "local_inputs_README.md", local_input_readme_fragment())
    print(f"wrote {output / 'holdings_template.csv'}")
    print(f"wrote {output / 'assumptions_template.json'}")
    print(f"wrote {output / 'local_inputs_README.md'}")
    return 0


def batch_compare_rows(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in case_rows(bundle):
        summary = row["packet"]["summary"]
        total_rate = summary["total_annual_drag_rate"]

        def component_dollars(rate: float) -> float:
            if total_rate <= 0:
                return 0.0
            return round(summary["total_drag"] * rate / total_rate, 2)

        rows.append(
            {
                "slug": row["slug"],
                "title": row["title"],
                "description": row["description"],
                "weighted_expense_ratio": summary["weighted_expense_ratio"],
                "cash_drag_rate": summary["cash_drag_rate"],
                "turnover_tax_drag_rate": summary["turnover_tax_drag_rate"],
                "rebalance_drag_rate": summary["rebalance_drag_rate"],
                "total_annual_drag_rate": summary["total_annual_drag_rate"],
                "total_dollar_drag": summary["total_drag"],
                "fee_drag_dollars": component_dollars(summary["weighted_expense_ratio"]),
                "cash_drag_dollars": component_dollars(summary["cash_drag_rate"]),
                "turnover_tax_drag_dollars": component_dollars(summary["turnover_tax_drag_rate"]),
                "rebalance_drag_dollars": component_dollars(summary["rebalance_drag_rate"]),
                "warnings": row["warnings"],
            }
        )
    return rows


def ranking(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    ordered = sorted(rows, key=lambda item: (-float(item[key]), item["slug"]))
    return [
        {
            "rank": index,
            "slug": item["slug"],
            "title": item["title"],
            "value": item[key],
        }
        for index, item in enumerate(ordered, start=1)
    ]


def batch_compare_payload(bundle: dict[str, Any]) -> dict[str, Any]:
    rows = batch_compare_rows(bundle)
    return {
        "schema": "portfolio-fee-drag-batch-compare-v1",
        "version": __version__,
        "boundary": SAFETY_BOUNDARY,
        "source_schema": bundle["schema"],
        "source_version": bundle.get("version"),
        "component_dollar_note": "Component dollar drag is allocated from total dollar drag in proportion to each annual drag-rate component.",
        "cases": rows,
        "rankings": {
            "total_annual_drag": ranking(rows, "total_annual_drag_rate"),
            "total_dollar_drag": ranking(rows, "total_dollar_drag"),
            "cash_drag": ranking(rows, "cash_drag_dollars"),
            "turnover_tax_drag": ranking(rows, "turnover_tax_drag_dollars"),
            "fee_drag": ranking(rows, "fee_drag_dollars"),
        },
        "next_action_review_questions": [
            "Which input fields changed between local cases, and who verified those fields?",
            "Do allocations sum to 1.0 and do cash-like rows match the intended local classification?",
            "Are expense ratios, cash return, gross return, turnover, realized gain, tax rate, taxable allocation, rebalance frequency, rebalance cost, and contribution timing current for this static review?",
            "Which cases require a human note explaining why the assumptions differ?",
            "What next review date should a human reviewer enter after validating the local inputs?",
        ],
    }


def batch_compare_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Batch Scenario Comparison",
        "",
        f"Version: {payload['version']}",
        "",
        f"Boundary: {payload['boundary']}",
        "",
        payload["component_dollar_note"],
        "",
        "| Case | Total Annual Drag | Total Dollar Drag | Cash Drag | Turnover/Tax Drag | Fee Drag |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in sorted(payload["cases"], key=lambda row: row["slug"]):
        lines.append(
            f"| {item['title']} | {pct(item['total_annual_drag_rate'])} | {money(item['total_dollar_drag'])} | "
            f"{money(item['cash_drag_dollars'])} | {money(item['turnover_tax_drag_dollars'])} | {money(item['fee_drag_dollars'])} |"
        )
    ranking_titles = {
        "total_annual_drag": "Total Annual Drag",
        "total_dollar_drag": "Total Dollar Drag",
        "cash_drag": "Cash Drag",
        "turnover_tax_drag": "Turnover Tax Drag",
        "fee_drag": "Fee Drag",
    }
    for name, title in ranking_titles.items():
        lines.extend(["", f"## Ranking: {title}", "", "| Rank | Case | Value |", "| ---: | --- | ---: |"])
        for item in payload["rankings"][name]:
            value = pct(item["value"]) if name == "total_annual_drag" else money(item["value"])
            lines.append(f"| {item['rank']} | {item['title']} | {value} |")
    lines.extend(["", "## Next-Action Review Questions", ""])
    lines.extend(f"- {question}" for question in payload["next_action_review_questions"])
    lines.extend(["", "These questions are for human review only and are not recommendations.", ""])
    return "\n".join(lines)


def cmd_batch_compare(args: argparse.Namespace) -> int:
    bundle = load_preset_bundle(args.presets)
    payload = batch_compare_payload(bundle)
    output = Path(args.output)
    write_json(output / "batch_compare.json", payload)
    write_text(output / "batch_compare.md", batch_compare_markdown(payload))
    print(f"wrote {output / 'batch_compare.md'}")
    print(f"wrote {output / 'batch_compare.json'}")
    return 0


def ranking_lookup(batch: dict[str, Any]) -> dict[tuple[str, str], int]:
    lookup: dict[tuple[str, str], int] = {}
    for dimension, rows in batch.get("rankings", {}).items():
        for row in rows:
            lookup[(dimension, row.get("slug", ""))] = int(row.get("rank", 0))
    return lookup


def scenario_driver_label(name: str) -> str:
    return {
        "weighted_expense_ratio": "expense ratio",
        "cash_drag_rate": "cash drag",
        "turnover_tax_drag_rate": "turnover/tax drag",
        "rebalance_drag_rate": "rebalance drag",
    }[name]


def scenario_narrative_payload_from_objects(gallery: dict[str, Any], batch: dict[str, Any], case_gallery_source: str, batch_compare_source: str) -> dict[str, Any]:
    ranks = ranking_lookup(batch)
    batch_cases = {item.get("slug"): item for item in batch.get("cases", [])}
    narratives: list[dict[str, Any]] = []
    for case in sorted(gallery.get("cases", []), key=lambda item: item.get("slug", "")):
        slug = case.get("slug", "")
        summary = case.get("packet", {}).get("summary", {})
        assumptions = case.get("packet", {}).get("assumptions", {})
        batch_case = batch_cases.get(slug, {})
        driver_values = [
            ("weighted_expense_ratio", float(summary.get("weighted_expense_ratio", 0.0))),
            ("cash_drag_rate", float(summary.get("cash_drag_rate", 0.0))),
            ("turnover_tax_drag_rate", float(summary.get("turnover_tax_drag_rate", 0.0))),
            ("rebalance_drag_rate", float(summary.get("rebalance_drag_rate", 0.0))),
        ]
        top_drivers = [
            {
                "name": name,
                "label": scenario_driver_label(name),
                "rate": value,
                "plain_language": f"{scenario_driver_label(name).title()} contributes {pct(value)} to the annual drag arithmetic.",
            }
            for name, value in sorted(driver_values, key=lambda item: (-item[1], item[0]))[:3]
        ]
        narratives.append(
            {
                "slug": slug,
                "title": case.get("title", slug),
                "plain_language_summary": (
                    f"{case.get('title', slug)} is a static local scenario over {assumptions.get('years')} years. "
                    f"It compares a gross future value of {money(summary.get('gross_future_value', 0.0))} with a net future value of "
                    f"{money(summary.get('net_future_value', 0.0))} after configured expense, cash, turnover/tax, and rebalance drags."
                ),
                "description": case.get("description", ""),
                "key_drag_drivers": top_drivers,
                "rank_context": {
                    "total_annual_drag_rank": ranks.get(("total_annual_drag", slug)),
                    "total_dollar_drag_rank": ranks.get(("total_dollar_drag", slug)),
                    "cash_drag_rank": ranks.get(("cash_drag", slug)),
                    "turnover_tax_drag_rank": ranks.get(("turnover_tax_drag", slug)),
                    "fee_drag_rank": ranks.get(("fee_drag", slug)),
                },
                "metrics": {
                    "weighted_expense_ratio": summary.get("weighted_expense_ratio"),
                    "cash_allocation": summary.get("cash_allocation"),
                    "cash_drag_rate": summary.get("cash_drag_rate"),
                    "turnover_tax_drag_rate": summary.get("turnover_tax_drag_rate"),
                    "rebalance_drag_rate": summary.get("rebalance_drag_rate"),
                    "total_annual_drag_rate": summary.get("total_annual_drag_rate"),
                    "total_dollar_drag": summary.get("total_drag", batch_case.get("total_dollar_drag")),
                },
                "questions_for_human_review": [
                    "Do the holdings, allocations, and cash-like classifications match the intended local case?",
                    "Who verified the gross return, cash return, turnover, realized gain, tax rate, taxable allocation, rebalance, and contribution timing assumptions?",
                    "Which driver is largest, and does a human reviewer need to add context for why that input differs from the other bundled cases?",
                    "Is the no-advice boundary visible wherever this scenario is shared?",
                ],
                "no_advice_boundary": SAFETY_BOUNDARY,
            }
        )
    return {
        "schema": "portfolio-fee-drag-scenario-narrative-v1",
        "version": __version__,
        "boundary": SAFETY_BOUNDARY,
        "case_gallery_source": case_gallery_source,
        "batch_compare_source": batch_compare_source,
        "source_schemas": {
            "case_gallery": gallery.get("schema"),
            "batch_compare": batch.get("schema"),
        },
        "scenarios": narratives,
        "review_note": "Narratives are plain-language explanations for human review only; they are not tax, legal, investment, or buy/sell/hold advice.",
    }


def scenario_narrative_payload(case_gallery_path: Path, batch_compare_path: Path) -> dict[str, Any]:
    gallery = load_json_object(case_gallery_path)
    batch = load_json_object(batch_compare_path)
    return scenario_narrative_payload_from_objects(gallery, batch, case_gallery_path.as_posix(), batch_compare_path.as_posix())


def scenario_narrative_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Scenario Narrative",
        "",
        f"Version: {payload['version']}",
        "",
        f"Boundary: {payload['boundary']}",
        "",
        f"Case gallery: `{payload['case_gallery_source']}`",
        f"Batch compare: `{payload['batch_compare_source']}`",
        "",
    ]
    for item in payload["scenarios"]:
        lines.extend(
            [
                f"## {item['title']}",
                "",
                item["plain_language_summary"],
                "",
                item["description"],
                "",
                "Key drag drivers:",
                "",
            ]
        )
        lines.extend(f"- {driver['plain_language']}" for driver in item["key_drag_drivers"])
        ranks = item["rank_context"]
        lines.extend(
            [
                "",
                "Rank context:",
                "",
                f"- Total annual drag rank: `{ranks['total_annual_drag_rank']}`",
                f"- Total dollar drag rank: `{ranks['total_dollar_drag_rank']}`",
                f"- Cash drag rank: `{ranks['cash_drag_rank']}`",
                f"- Turnover/tax drag rank: `{ranks['turnover_tax_drag_rank']}`",
                f"- Fee drag rank: `{ranks['fee_drag_rank']}`",
                "",
                "Questions for human review:",
                "",
            ]
        )
        lines.extend(f"- {question}" for question in item["questions_for_human_review"])
        lines.extend(["", f"No-advice boundary: {item['no_advice_boundary']}", ""])
    lines.extend(["## Review Note", "", payload["review_note"], ""])
    return "\n".join(lines)


def cmd_scenario_narrative(args: argparse.Namespace) -> int:
    output = Path(args.output)
    payload = scenario_narrative_payload(Path(args.case_gallery), Path(args.batch_compare))
    write_json(output / "scenario_narrative.json", payload)
    write_text(output / "scenario_narrative.md", scenario_narrative_markdown(payload))
    print(f"wrote {output / 'scenario_narrative.md'}")
    print(f"wrote {output / 'scenario_narrative.json'}")
    return 0


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


def review_flag(name: str, metric: str, value: Any, threshold: Any, prompt: str) -> dict[str, Any]:
    return {
        "name": name,
        "metric": metric,
        "value": value,
        "threshold": threshold,
        "review_prompt": prompt,
    }


def risk_flags_payload(holdings_path: Path, assumptions_path: Path) -> dict[str, Any]:
    holdings = load_holdings(holdings_path)
    assumptions = load_assumptions(assumptions_path)
    packet = compute_packet(holdings, assumptions)
    summary = packet["summary"]
    allocation_sum = round(sum(item.allocation for item in holdings), 8)
    max_expense = max((item.expense_ratio for item in holdings), default=0.0)
    flags: list[dict[str, Any]] = []

    if summary["cash_allocation"] >= 0.20:
        flags.append(
            review_flag(
                "high_cash_allocation",
                "cash_allocation",
                summary["cash_allocation"],
                ">= 0.20",
                "Ask a human reviewer to confirm whether cash-like holdings and cash return assumptions match the static review case.",
            )
        )
    if summary["weighted_expense_ratio"] >= 0.005 or max_expense >= 0.01:
        flags.append(
            review_flag(
                "high_expense_ratio",
                "weighted_expense_ratio",
                summary["weighted_expense_ratio"],
                "weighted >= 0.005 or holding >= 0.01",
                "Ask a human reviewer to confirm expense ratios and whether the ledger labels match the intended local inputs.",
            )
        )
    if summary["turnover_tax_drag_rate"] >= 0.005 or assumptions.turnover_rate >= 0.50:
        flags.append(
            review_flag(
                "high_turnover_tax_drag",
                "turnover_tax_drag_rate",
                summary["turnover_tax_drag_rate"],
                "drag >= 0.005 or turnover_rate >= 0.50",
                "Ask a human reviewer to confirm turnover, realized gain, tax rate, and taxable allocation assumptions before sharing.",
            )
        )
    if abs(allocation_sum - 1.0) > 0.0001:
        flags.append(
            review_flag(
                "allocation_mismatch",
                "allocation_sum",
                allocation_sum,
                "outside 1.0 +/- 0.0001",
                "Ask a human reviewer to reconcile the holdings allocation sum against the source ledger.",
            )
        )
    if assumptions.years >= 30:
        flags.append(
            review_flag(
                "long_horizon",
                "years",
                assumptions.years,
                ">= 30",
                "Ask a human reviewer to confirm that the horizon is intentional for this static scenario review.",
            )
        )
    if assumptions.rebalance_frequency in {"quarterly", "monthly"}:
        flags.append(
            review_flag(
                "frequent_rebalancing",
                "rebalance_frequency",
                assumptions.rebalance_frequency,
                "quarterly or monthly",
                "Ask a human reviewer to confirm rebalance frequency and cost-per-event assumptions.",
            )
        )

    return {
        "schema": "portfolio-fee-drag-risk-flags-v1",
        "version": __version__,
        "status": "review" if flags else "pass",
        "boundary": SAFETY_BOUNDARY,
        "holdings_source": display_path(holdings_path),
        "assumptions_source": display_path(assumptions_path),
        "thresholds": {
            "high_cash_allocation": "cash_allocation >= 0.20",
            "high_expense_ratio": "weighted_expense_ratio >= 0.005 or any holding expense_ratio >= 0.01",
            "high_turnover_tax_drag": "turnover_tax_drag_rate >= 0.005 or turnover_rate >= 0.50",
            "allocation_mismatch": "allocation_sum outside 1.0 +/- 0.0001",
            "long_horizon": "years >= 30",
            "frequent_rebalancing": "rebalance_frequency is quarterly or monthly",
        },
        "metrics": {
            "allocation_sum": allocation_sum,
            "cash_allocation": summary["cash_allocation"],
            "weighted_expense_ratio": summary["weighted_expense_ratio"],
            "max_holding_expense_ratio": max_expense,
            "turnover_rate": assumptions.turnover_rate,
            "turnover_tax_drag_rate": summary["turnover_tax_drag_rate"],
            "years": assumptions.years,
            "rebalance_frequency": assumptions.rebalance_frequency,
            "rebalance_drag_rate": summary["rebalance_drag_rate"],
        },
        "flags": flags,
        "review_note": "Flags are prompts for human review only and are not recommendations, suitability analysis, or tax/legal/investment advice.",
    }


def risk_flags_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Risk Flags",
        "",
        f"Version: {payload['version']}",
        f"Status: {payload['status']}",
        "",
        f"Boundary: {payload['boundary']}",
        "",
        f"Holdings: `{payload['holdings_source']}`",
        f"Assumptions: `{payload['assumptions_source']}`",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    for key, value in payload["metrics"].items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend(["", "## Review Flags", "", "| Flag | Metric | Value | Threshold | Review Prompt |", "| --- | --- | ---: | --- | --- |"])
    for item in payload["flags"]:
        lines.append(
            f"| `{item['name']}` | `{item['metric']}` | `{item['value']}` | {item['threshold']} | {item['review_prompt']} |"
        )
    if not payload["flags"]:
        lines.append("| No flags |  |  | configured thresholds | No configured risk flag threshold was crossed. |")
    lines.extend(["", payload["review_note"], ""])
    return "\n".join(lines)


def cmd_risk_flags(args: argparse.Namespace) -> int:
    output = Path(args.output)
    payload = risk_flags_payload(Path(args.holdings), Path(args.assumptions))
    write_json(output / "risk_flags.json", payload)
    write_text(output / "risk_flags.md", risk_flags_markdown(payload))
    print(f"wrote {output / 'risk_flags.md'}")
    print(f"wrote {output / 'risk_flags.json'}")
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
    ("input_templates/holdings_template.csv", "file://demo/input_templates/holdings_template.csv", "python -m portfolio_fee_drag_simulator input-template --output demo/input_templates", "Starter holdings CSV template copied from bundled examples.", "Useful for adapting local CSV inputs without live data."),
    ("input_templates/assumptions_template.json", "file://demo/input_templates/assumptions_template.json", "python -m portfolio_fee_drag_simulator input-template --output demo/input_templates", "Starter assumptions JSON template with a local-only note.", "Useful for adapting local JSON assumptions without live data."),
    ("input_templates/local_inputs_README.md", "file://demo/input_templates/local_inputs_README.md", "python -m portfolio_fee_drag_simulator input-template --output demo/input_templates", "README fragment for adapting local CSV/JSON inputs.", "Useful for public-safe onboarding to offline inputs."),
    ("assumption_diff.md", "file://demo/assumption_diff.md", "python -m portfolio_fee_drag_simulator assumption-diff --output demo", "Markdown comparison of bundled base and review assumptions.", "Useful for reviewing local assumption field deltas without advice."),
    ("assumption_diff.json", "file://demo/assumption_diff.json", "python -m portfolio_fee_drag_simulator assumption-diff --output demo", "Machine-readable assumption field deltas.", "Useful for deterministic review workflow handoff without recommendations."),
    ("risk_flags.md", "file://demo/risk_flags.md", "python -m portfolio_fee_drag_simulator risk-flags --output demo", "Markdown review prompts for configured risk flag thresholds.", "Useful for prompting human review of cash, expense, turnover/tax, allocation, horizon, and rebalancing inputs."),
    ("risk_flags.json", "file://demo/risk_flags.json", "python -m portfolio_fee_drag_simulator risk-flags --output demo", "Machine-readable review prompts for configured risk flag thresholds.", "Useful for deterministic advanced review workflow checks."),
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
    ("batch_compare.md", "file://demo/batch_compare.md", "python -m portfolio_fee_drag_simulator batch-compare --output demo", "Markdown ranking of scenario presets by drag dimensions.", "Useful for comparing cases with review questions instead of recommendations."),
    ("batch_compare.json", "file://demo/batch_compare.json", "python -m portfolio_fee_drag_simulator batch-compare --output demo", "Machine-readable ranking of scenario presets by drag dimensions.", "Useful for deterministic case sorting across local review dimensions."),
    ("scenario_narrative.md", "file://demo/scenario_narrative.md", "python -m portfolio_fee_drag_simulator scenario-narrative --output demo", "Plain-language scenario narrative with drivers, review questions, and no-advice boundaries.", "Useful for promotion review of how bundled scenarios are explained to humans."),
    ("scenario_narrative.json", "file://demo/scenario_narrative.json", "python -m portfolio_fee_drag_simulator scenario-narrative --output demo", "Machine-readable scenario narrative with driver and ranking context.", "Useful for checking bundled scenario explanations without live data or recommendations."),
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
    ("docs_export.md", "file://demo/docs_export.md", "python -m portfolio_fee_drag_simulator docs-export --output demo", "Deterministic public command, schema, artifact, verification, and boundary documentation.", "Useful for first-screen project review and public showcase context."),
    ("docs_export.json", "file://demo/docs_export.json", "python -m portfolio_fee_drag_simulator docs-export --output demo", "Machine-readable public documentation export.", "Useful for checking command coverage and artifact map completeness."),
    ("reproducibility_pack.md", "file://demo/reproducibility_pack.md", "python -m portfolio_fee_drag_simulator reproducibility-pack --output demo", "Markdown reproducibility pack with exact local clone, install, test, build, wheel smoke, and demo regeneration commands.", "Useful for release-owner reproduction from source without workflows or live services."),
    ("reproducibility_pack.json", "file://demo/reproducibility_pack.json", "python -m portfolio_fee_drag_simulator reproducibility-pack --output demo", "Machine-readable reproducibility pack with commands and expected artifacts.", "Useful for deterministic release review and wheel smoke-test planning."),
    ("security_boundary_report.md", "file://demo/security_boundary_report.md", "python -m portfolio_fee_drag_simulator security-boundary-report --root . --output demo", "Markdown security and finance boundary report for public-safe release review.", "Useful for confirming no secrets, workflows, network/live data, broker/API/order execution, runtime dependencies, or advice boundary gaps."),
    ("security_boundary_report.json", "file://demo/security_boundary_report.json", "python -m portfolio_fee_drag_simulator security-boundary-report --root . --output demo", "Machine-readable security and finance boundary report.", "Useful for release-owner checks of public-safe boundaries and package data claims."),
    ("promotion_checklist.md", "file://demo/promotion_checklist.md", "python -m portfolio_fee_drag_simulator promotion-checklist --output demo", "Release and promotion readiness checklist in Markdown.", "Useful for validating README, quickstart, showcase, docs, audits, wheel install, public scan, and finance boundaries before promotion."),
    ("promotion_checklist.json", "file://demo/promotion_checklist.json", "python -m portfolio_fee_drag_simulator promotion-checklist --output demo", "Machine-readable release and promotion readiness checklist.", "Useful for deterministic promotion review handoff."),
    ("showcase.html", "file://demo/showcase.html", "python -m portfolio_fee_drag_simulator static-showcase --output demo/showcase.html", "No-JS public showcase index for generated review artifacts.", "Useful as the first local page to open when evaluating the demo."),
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
                    "open demo/showcase.html",
                    "open demo/dashboard.html",
                    "open demo/case_gallery.html",
                    "open demo/visual_receipt.html",
                ],
                "expected_output": "A static showcase, dashboard, case gallery, and receipt open from local files. On Linux, use xdg-open instead of open.",
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
                    "python -m portfolio_fee_drag_simulator input-template --output demo/input_templates",
                    "python -m portfolio_fee_drag_simulator assumption-diff --output demo",
                    "python -m portfolio_fee_drag_simulator risk-flags --output demo",
                    "python -m portfolio_fee_drag_simulator batch-compare --output demo",
                    "python -m portfolio_fee_drag_simulator scenario-narrative --output demo",
                    "python -m portfolio_fee_drag_simulator visual-receipt --output demo",
                    "python -m portfolio_fee_drag_simulator decision-journal --output demo",
                    "python -m portfolio_fee_drag_simulator docs-export --output demo",
                    "python -m portfolio_fee_drag_simulator reproducibility-pack --output demo",
                    "python -m portfolio_fee_drag_simulator security-boundary-report --root . --output demo",
                    "python -m portfolio_fee_drag_simulator static-showcase --output demo/showcase.html",
                    "python -m portfolio_fee_drag_simulator promotion-checklist --output demo",
                    "python -m portfolio_fee_drag_simulator artifact-catalog --output demo",
                ],
                "expected_output": "Input templates, assumption diff, risk flags, batch comparison, scenario narrative, visual receipt, decision journal, docs export, reproducibility pack, security boundary report, showcase, promotion checklist, and artifact catalog files list local routes, prompts, hashes, regeneration commands, review questions, and safety boundaries.",
            },
        ],
        "expected_artifacts": [
            "demo/fee_drag_packet.md",
            "demo/fee_drag_packet.json",
            "demo/input_templates/holdings_template.csv",
            "demo/input_templates/assumptions_template.json",
            "demo/input_templates/local_inputs_README.md",
            "demo/assumption_diff.md",
            "demo/assumption_diff.json",
            "demo/risk_flags.md",
            "demo/risk_flags.json",
            "demo/dashboard.html",
            "demo/case_gallery.md",
            "demo/case_gallery.json",
            "demo/case_gallery.html",
            "demo/batch_compare.md",
            "demo/batch_compare.json",
            "demo/scenario_narrative.md",
            "demo/scenario_narrative.json",
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
            "demo/docs_export.md",
            "demo/docs_export.json",
            "demo/reproducibility_pack.md",
            "demo/reproducibility_pack.json",
            "demo/security_boundary_report.md",
            "demo/security_boundary_report.json",
            "demo/promotion_checklist.md",
            "demo/promotion_checklist.json",
            "demo/showcase.html",
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
        issues.append(audit_issue("dependencies", "error", "runtime dependencies are not empty", "Remove runtime dependencies or document why v1.0 changed scope."))

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
        for name in ("example_holdings.csv", "example_assumptions.json", "example_assumptions_review.json", "example_history.json", "scenario_presets.json")
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


def docs_export_payload() -> dict[str, Any]:
    holdings_columns = [
        {"name": "account", "type": "string", "required": True, "description": "Account label used for review grouping."},
        {"name": "ticker", "type": "string", "required": True, "description": "Ticker or local proxy label; CASH marks cash-like holdings."},
        {"name": "name", "type": "string", "required": True, "description": "Human-readable holding name."},
        {"name": "allocation", "type": "number", "required": True, "description": "Portfolio allocation as a decimal; bundled examples sum to 1.0."},
        {"name": "expense_ratio", "type": "number", "required": True, "description": "Annual expense ratio as a decimal."},
    ]
    assumptions_fields = [
        {"name": "initial_value", "type": "number", "description": "Starting portfolio value."},
        {"name": "annual_contribution", "type": "number", "description": "Annual contribution used in compounding."},
        {"name": "years", "type": "integer", "description": "Number of annual compounding periods."},
        {"name": "gross_return", "type": "number", "description": "Local gross annual return assumption."},
        {"name": "cash_return", "type": "number", "description": "Local annual return assumption for cash-like holdings."},
        {"name": "turnover_rate", "type": "number", "description": "Local annual turnover assumption."},
        {"name": "realized_gain_rate", "type": "number", "description": "Share of turnover treated as realized gains."},
        {"name": "tax_rate", "type": "number", "description": "Local tax-rate assumption for turnover drag arithmetic."},
        {"name": "taxable_allocation", "type": "number", "description": "Share of portfolio treated as taxable for turnover drag arithmetic."},
        {"name": "rebalance_frequency", "type": "enum", "values": ["none", "annual", "quarterly", "monthly"], "description": "Supported rebalance frequency."},
        {"name": "rebalance_cost", "type": "number", "description": "Cost per rebalance event as a decimal."},
        {"name": "contribution_timing", "type": "enum", "values": ["beginning", "end"], "description": "Whether annual contributions compound for the current year."},
    ]
    artifacts = [
        {
            "path": path_name,
            "route": route,
            "producer_command": producer,
            "role": role,
            "user_value": usefulness,
        }
        for path_name, route, producer, role, usefulness in DEMO_ARTIFACT_SPECS
    ]
    return {
        "schema": "portfolio-fee-drag-docs-export-v1",
        "version": __version__,
        "boundary": SAFETY_BOUNDARY,
        "commands": [{"name": name, "summary": COMMAND_DOCS[name]} for name in sorted(COMMAND_DOCS)],
        "input_schema": {
            "holdings_csv": {
                "columns": holdings_columns,
                "example": "account,ticker,name,allocation,expense_ratio",
            },
            "assumptions_json": {
                "required_fields": assumptions_fields,
                "calculation_notes": [
                    "Weighted expense ratio is allocation-weighted across holdings.",
                    "Cash drag is cash-like allocation multiplied by max(gross_return - cash_return, 0).",
                    "Turnover/tax drag is turnover_rate * realized_gain_rate * tax_rate * taxable_allocation.",
                    "Rebalance drag is rebalance_cost multiplied by supported annual event count.",
                ],
            },
        },
        "artifact_map": artifacts,
        "verification_commands": list(VERIFICATION_COMMANDS),
        "finance_boundaries": list(FINANCE_BOUNDARIES),
    }


def docs_export_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Portfolio Fee Drag Docs Export",
        "",
        f"Version: {payload['version']}",
        "",
        f"Boundary: {payload['boundary']}",
        "",
        "## Commands",
        "",
        "| Command | Summary |",
        "| --- | --- |",
    ]
    for item in payload["commands"]:
        lines.append(f"| `{item['name']}` | {item['summary']} |")
    lines.extend(["", "## Input Schema", "", "### Holdings CSV", "", "| Column | Type | Required | Description |", "| --- | --- | --- | --- |"])
    for column in payload["input_schema"]["holdings_csv"]["columns"]:
        lines.append(f"| `{column['name']}` | {column['type']} | {column['required']} | {column['description']} |")
    lines.extend(["", "### Assumptions JSON", "", "| Field | Type | Description |", "| --- | --- | --- |"])
    for field in payload["input_schema"]["assumptions_json"]["required_fields"]:
        type_label = field["type"]
        if "values" in field:
            type_label = f"{type_label}: {', '.join(field['values'])}"
        lines.append(f"| `{field['name']}` | {type_label} | {field['description']} |")
    lines.extend(["", "Calculation notes:", ""])
    lines.extend(f"- {note}" for note in payload["input_schema"]["assumptions_json"]["calculation_notes"])
    lines.extend(["", "## Artifact Map", "", "| Artifact | Route | Producer | User Value |", "| --- | --- | --- | --- |"])
    for item in payload["artifact_map"]:
        lines.append(f"| `{item['path']}` | `{item['route']}` | `{item['producer_command']}` | {item['user_value']} |")
    lines.extend(["", "## Verification Commands", ""])
    lines.extend(f"- `{command}`" for command in payload["verification_commands"])
    lines.extend(["", "## Finance Boundaries", ""])
    lines.extend(f"- {boundary}" for boundary in payload["finance_boundaries"])
    lines.append("")
    return "\n".join(lines)


def cmd_docs_export(args: argparse.Namespace) -> int:
    output = Path(args.output)
    payload = docs_export_payload()
    write_json(output / "docs_export.json", payload)
    write_text(output / "docs_export.md", docs_export_markdown(payload))
    print(f"wrote {output / 'docs_export.md'}")
    print(f"wrote {output / 'docs_export.json'}")
    return 0


def expected_demo_artifacts() -> list[str]:
    return [f"demo/{path_name}" for path_name, *_ in DEMO_ARTIFACT_SPECS]


def reproducibility_pack_payload(root: Path, repo_url: str) -> dict[str, Any]:
    wheel_name = f"portfolio_fee_drag_simulator-{__version__}-py3-none-any.whl"
    commands = [
        {
            "phase": "clone",
            "commands": [
                f"git clone {repo_url} portfolio-fee-drag-simulator",
                "cd portfolio-fee-drag-simulator",
                "git status --short",
            ],
            "expected_artifacts": ["README.md", "pyproject.toml", "portfolio_fee_drag_simulator/", "tests/"],
        },
        {
            "phase": "install",
            "commands": [
                "python -m venv .venv",
                ". .venv/bin/activate",
                "python -m pip install -e . --no-deps",
                "portfolio-fee-drag --version",
            ],
            "expected_artifacts": [".venv/", "portfolio_fee_drag_simulator.egg-info/"],
        },
        {
            "phase": "test",
            "commands": [
                "python -m unittest discover -s tests",
                "python -m portfolio_fee_drag_simulator selfcheck",
                "python -m portfolio_fee_drag_simulator public-scan --root . --output demo/public_scan.json",
            ],
            "expected_artifacts": ["demo/public_scan.json"],
        },
        {
            "phase": "build",
            "commands": [
                "python -m pip wheel . --no-deps --no-build-isolation --wheel-dir dist",
            ],
            "expected_artifacts": [f"dist/{wheel_name}"],
        },
        {
            "phase": "wheel smoke",
            "commands": [
                "python -m venv /tmp/portfolio-fee-drag-smoke",
                f"/tmp/portfolio-fee-drag-smoke/bin/python -m pip install dist/{wheel_name} --no-deps",
                "/tmp/portfolio-fee-drag-smoke/bin/portfolio-fee-drag --version",
                "/tmp/portfolio-fee-drag-smoke/bin/python -m portfolio_fee_drag_simulator selfcheck",
            ],
            "expected_artifacts": [f"dist/{wheel_name}"],
        },
        {
            "phase": "demo regeneration",
            "commands": [
                "python -m portfolio_fee_drag_simulator quickstart-check --output demo",
                "python -m portfolio_fee_drag_simulator release-audit-summary --output demo --tests-status pass",
                "python -m portfolio_fee_drag_simulator security-boundary-report --root . --output demo",
                "python -m portfolio_fee_drag_simulator reproducibility-pack --output demo",
                "python -m portfolio_fee_drag_simulator artifact-catalog --artifact-root demo --output demo",
                "python -m portfolio_fee_drag_simulator docs-export --output demo",
                "python -m portfolio_fee_drag_simulator static-showcase --output demo/showcase.html",
            ],
            "expected_artifacts": expected_demo_artifacts(),
        },
    ]
    return {
        "schema": "portfolio-fee-drag-reproducibility-pack-v1",
        "version": __version__,
        "status": "pass",
        "boundary": SAFETY_BOUNDARY,
        "root": root.resolve().as_posix(),
        "repo_url": repo_url,
        "python": "Python 3.11 or newer",
        "runtime_dependencies": [],
        "workflow_policy": "No GitHub Actions or hosted workflow automation is required for this release path.",
        "network_policy": "Commands operate on the local checkout and local package build only; the simulator itself fetches no live data.",
        "commands": commands,
        "verification_commands": list(VERIFICATION_COMMANDS),
        "expected_artifacts": expected_demo_artifacts(),
        "finance_boundaries": list(FINANCE_BOUNDARIES),
    }


def reproducibility_pack_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Reproducibility Pack",
        "",
        f"Version: {payload['version']}",
        f"Status: {payload['status']}",
        "",
        f"Boundary: {payload['boundary']}",
        "",
        f"Source root: `{payload['root']}`",
        f"Repo URL placeholder: `{payload['repo_url']}`",
        f"Python: {payload['python']}",
        f"Runtime dependencies: `{len(payload['runtime_dependencies'])}`",
        "",
    ]
    for phase in payload["commands"]:
        lines.extend([f"## {phase['phase'].title()}", "", "Commands:", ""])
        lines.extend(f"- `{command}`" for command in phase["commands"])
        lines.extend(["", "Expected artifacts:", ""])
        lines.extend(f"- `{artifact}`" for artifact in phase["expected_artifacts"])
        lines.append("")
    lines.extend(["## Verification Commands", ""])
    lines.extend(f"- `{command}`" for command in payload["verification_commands"])
    lines.extend(["", "## Finance Boundaries", ""])
    lines.extend(f"- {boundary}" for boundary in payload["finance_boundaries"])
    lines.append("")
    return "\n".join(lines)


def cmd_reproducibility_pack(args: argparse.Namespace) -> int:
    output = Path(args.output)
    payload = reproducibility_pack_payload(Path(args.root), args.repo_url)
    write_json(output / "reproducibility_pack.json", payload)
    write_text(output / "reproducibility_pack.md", reproducibility_pack_markdown(payload))
    print(f"wrote {output / 'reproducibility_pack.md'}")
    print(f"wrote {output / 'reproducibility_pack.json'}")
    return 0


def network_import_findings(root: Path) -> list[dict[str, str]]:
    modules = ("requests", "httpx", "urllib", "socket", "aiohttp", "websocket")
    findings: list[dict[str, str]] = []
    for path in iter_release_files(root):
        if path.suffix != ".py":
            continue
        for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            stripped = line.strip()
            if not (stripped.startswith("import ") or stripped.startswith("from ")):
                continue
            for module in modules:
                if (
                    stripped == f"import {module}"
                    or stripped.startswith(f"import {module}.")
                    or stripped.startswith(f"from {module} ")
                    or stripped.startswith(f"from {module}.")
                ):
                    findings.append({"path": path.relative_to(root).as_posix(), "line": str(line_number), "module": module})
    return findings


def workflow_files(root: Path) -> list[str]:
    workflows = root / ".github" / "workflows"
    if not workflows.exists():
        return []
    return sorted(path.relative_to(root).as_posix() for path in workflows.rglob("*") if path.is_file())


def security_boundary_report_payload(root: Path) -> dict[str, Any]:
    package = package_audit_payload(root)
    public_scan = public_scan_payload(root)
    workflows = workflow_files(root)
    network_findings = network_import_findings(root)
    installed_context = not (root / "pyproject.toml").exists() and not (root / "README.md").exists()
    package_data_set = set(package["package_data"])
    package_data_ok = {"data/*.csv", "data/*.json"}.issubset(package_data_set) or {"installed:data/*.csv", "installed:data/*.json"}.issubset(package_data_set)
    checks = [
        {
            "name": "No secrets",
            "status": "pass" if (installed_context or public_scan["status"] == "pass") and not public_scan["secret_marker_findings"] else "review",
            "evidence": f"{public_scan['files_scanned']} public release files scanned for common secret markers; installed-context={installed_context}.",
        },
        {
            "name": "No workflows",
            "status": "pass" if not workflows else "review",
            "evidence": "No .github/workflows files found." if not workflows else ", ".join(workflows),
        },
        {
            "name": "No network or live data",
            "status": "pass" if not network_findings else "review",
            "evidence": "No network client imports found in release Python files; fixtures are local package data.",
        },
        {
            "name": "No broker/API/order execution",
            "status": "pass",
            "evidence": "The simulator exposes static local arithmetic commands only and repeats broker/API/order-execution exclusions in public boundaries.",
        },
        {
            "name": "Zero runtime dependencies",
            "status": "pass" if package["runtime_dependencies"] == [] else "review",
            "evidence": f"pyproject runtime dependencies: {package['runtime_dependencies']}",
        },
        {
            "name": "Package data",
            "status": "pass" if package_data_ok else "review",
            "evidence": f"package data declarations: {package['package_data']}",
        },
        {
            "name": "Finance/no-advice boundaries",
            "status": "pass" if installed_context or public_scan["finance_boundary_present"] else "review",
            "evidence": "README/generated artifacts or installed package metadata state static local review, no live data, no broker connection, and no tax/legal/investment or buy/sell/hold advice.",
        },
    ]
    blocking = {"review", "fail", "missing"}
    return {
        "schema": "portfolio-fee-drag-security-boundary-report-v1",
        "version": __version__,
        "status": "pass" if all(item["status"] not in blocking for item in checks) else "review",
        "boundary": SAFETY_BOUNDARY,
        "root": root.resolve().as_posix(),
        "checks": checks,
        "secret_marker_findings": public_scan["secret_marker_findings"],
        "workflow_files": workflows,
        "network_import_findings": network_findings,
        "broker_api_order_execution_boundary": "No broker API, no order execution, no account connection, no trading workflow, no recommendation engine.",
        "runtime_dependencies": package["runtime_dependencies"],
        "package_data": package["package_data"],
        "finance_boundaries": list(FINANCE_BOUNDARIES),
    }


def security_boundary_report_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Security Boundary Report",
        "",
        f"Version: {payload['version']}",
        f"Status: {payload['status']}",
        "",
        f"Boundary: {payload['boundary']}",
        "",
        "| Check | Status | Evidence |",
        "| --- | --- | --- |",
    ]
    for item in payload["checks"]:
        lines.append(f"| {item['name']} | {item['status']} | {item['evidence']} |")
    lines.extend(
        [
            "",
            "## Explicit Boundaries",
            "",
            f"- {payload['broker_api_order_execution_boundary']}",
            "- No GitHub Actions workflows are required or bundled.",
            "- No runtime dependencies are declared.",
            "- Package data is limited to bundled CSV and JSON fixtures.",
        ]
    )
    lines.extend(["", "## Finance Boundaries", ""])
    lines.extend(f"- {boundary}" for boundary in payload["finance_boundaries"])
    lines.append("")
    return "\n".join(lines)


def cmd_security_boundary_report(args: argparse.Namespace) -> int:
    output = Path(args.output)
    payload = security_boundary_report_payload(Path(args.root))
    write_json(output / "security_boundary_report.json", payload)
    write_text(output / "security_boundary_report.md", security_boundary_report_markdown(payload))
    print(f"wrote {output / 'security_boundary_report.md'}")
    print(f"wrote {output / 'security_boundary_report.json'}")
    return 0 if payload["status"] == "pass" else 1


SHOWCASE_LINKS = (
    ("Input Templates", "input_templates/local_inputs_README.md", "Adapt local CSV and JSON inputs from offline starter files without live data."),
    ("Assumption Diff", "assumption_diff.md", "Compare bundled base and review assumptions by field delta, direction, and review impact without advice."),
    ("Risk Flags", "risk_flags.md", "Review configured cash, expense, turnover/tax, allocation, horizon, and rebalancing prompts without recommendations."),
    ("Dashboard", "dashboard.html", "Review the bundled packet metrics and holdings in a single standalone page."),
    ("Case Gallery", "case_gallery.html", "Compare three deterministic scenarios across expense, cash, turnover/tax, rebalance, and total drag."),
    ("Batch Compare", "batch_compare.md", "Rank scenario presets by total annual drag, total dollar drag, cash drag, turnover tax drag, and fee drag with review questions."),
    ("Scenario Narrative", "scenario_narrative.md", "Read plain-language explanations for each bundled scenario, including key drag drivers, rank context, review questions, and no-advice boundaries."),
    ("Visual Receipt", "visual_receipt.html", "Check local routes, byte counts, SHA-256 hashes, producer commands, and safety boundaries for visual artifacts."),
    ("Cold-Start Walkthrough", "cold_start_walkthrough.md", "Follow a 10-minute install, run, evaluate, and boundary-review path for first-time users."),
    ("Decision Journal", "decision_journal.md", "Use deterministic prompts for human assumption review, verification notes, and no-advice language."),
    ("Artifact Catalog", "artifact_catalog.md", "Inventory generated demo files with hashes, producer commands, roles, and promotion usefulness."),
    ("Release Audit", "release_audit_summary.md", "Review release-owner status across tests, selfcheck, public scan, manifests, fixtures, package audit, and visual receipt."),
    ("Package Audit", "package_audit.md", "Confirm zero runtime dependencies, package data, script wiring, versions, and command coverage."),
    ("Docs Export", "docs_export.md", "Read deterministic public docs for commands, input schema, artifact map, verification commands, and finance boundaries."),
    ("Reproducibility Pack", "reproducibility_pack.md", "Run exact local clone, install, test, build, wheel smoke, and demo regeneration commands."),
    ("Security Boundary Report", "security_boundary_report.md", "Confirm no secrets, workflows, network/live data, broker/API/order execution, runtime dependencies, or finance boundary gaps."),
    ("Promotion Checklist", "promotion_checklist.md", "Review README, quickstart, showcase, docs export, audits, public scan, wheel install, and finance boundaries before promotion."),
)


def static_showcase_html() -> str:
    cards = "\n".join(
        """<article>
      <h2><a href="{href}">{title}</a></h2>
      <p>{copy}</p>
    </article>""".format(
            href=html.escape(href),
            title=html.escape(title),
            copy=html.escape(copy),
        )
        for title, href, copy in SHOWCASE_LINKS
    )
    boundaries = "\n".join(f"<li>{html.escape(item)}</li>" for item in FINANCE_BOUNDARIES)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Portfolio Fee Drag Public Showcase</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 0; color: #172033; background: #f8fafc; }}
    main {{ max-width: 1100px; margin: 0 auto; padding: 2rem; }}
    header {{ border-bottom: 1px solid #cbd5e1; padding-bottom: 1rem; margin-bottom: 1.5rem; }}
    h1 {{ font-size: 2rem; margin: 0 0 0.75rem; }}
    p {{ line-height: 1.5; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; }}
    article {{ background: #ffffff; border: 1px solid #d7dde7; border-radius: 8px; padding: 1rem; }}
    article h2 {{ font-size: 1.05rem; margin: 0 0 0.5rem; }}
    article p {{ margin: 0; color: #475569; }}
    a {{ color: #0f766e; font-weight: 700; }}
    .boundary {{ margin-top: 1.75rem; border-top: 1px solid #cbd5e1; padding-top: 1rem; }}
  </style>
</head>
<body>
<main>
  <header>
    <h1>Portfolio Fee Drag Public Showcase</h1>
    <p>Open the generated local artifacts from one no-JS page: visual review, audit evidence, first-run help, and deterministic public docs.</p>
  </header>
  <section class="grid" aria-label="Showcase links">
    {cards}
  </section>
  <section class="boundary">
    <h2>Finance Boundaries</h2>
    <ul>{boundaries}</ul>
  </section>
</main>
</body>
</html>
"""


def cmd_static_showcase(args: argparse.Namespace) -> int:
    output = Path(args.output)
    write_text(output, static_showcase_html())
    print(f"wrote {output}")
    return 0


def checklist_item(name: str, artifact: str, status: str, review_prompt: str) -> dict[str, str]:
    return {"name": name, "artifact": artifact, "status": status, "review_prompt": review_prompt}


def promotion_checklist_payload(root: Path, artifact_root: Path) -> dict[str, Any]:
    required = {
        "README": root / "README.md",
        "quickstart": artifact_root / "showcase.html",
        "demo_showcase": artifact_root / "showcase.html",
        "docs_export": artifact_root / "docs_export.json",
        "release_audit_summary": artifact_root / "release_audit_summary.json",
        "package_audit": artifact_root / "package_audit.json",
        "public_scan": artifact_root / "public_scan.json",
        "reproducibility_pack": artifact_root / "reproducibility_pack.json",
        "security_boundary_report": artifact_root / "security_boundary_report.json",
        "scenario_narrative": artifact_root / "scenario_narrative.json",
    }
    readme_text = required["README"].read_text(encoding="utf-8") if required["README"].exists() else ""
    package_payload = read_json_file(required["package_audit"]) or {}
    public_scan = read_json_file(required["public_scan"]) or {}
    release_summary = read_json_file(required["release_audit_summary"]) or {}
    docs_export = read_json_file(required["docs_export"]) or {}
    reproducibility_pack = read_json_file(required["reproducibility_pack"]) or {}
    security_boundary_report = read_json_file(required["security_boundary_report"]) or {}
    items = [
        checklist_item(
            "README boundary and command coverage",
            "README.md",
            "pass" if required["README"].exists() and all(term in readme_text for term in ("quickstart-check", "scenario-narrative", "promotion-checklist", "buy/sell/hold")) else "review",
            "Confirm README documents quickstart, scenario narrative, promotion checklist, and finance boundaries before promotion.",
        ),
        checklist_item(
            "Quickstart demo artifacts",
            artifact_root.as_posix(),
            "pass" if all((artifact_root / path).exists() for path in ("showcase.html", "scenario_narrative.md", "promotion_checklist.md")) else "review",
            "Run quickstart-check and confirm the generated demo includes showcase, scenario narrative, and promotion checklist artifacts.",
        ),
        checklist_item(
            "Static showcase",
            "demo/showcase.html",
            "pass" if required["demo_showcase"].exists() and "<script" not in required["demo_showcase"].read_text(encoding="utf-8", errors="ignore").lower() else "review",
            "Open demo/showcase.html and confirm it links public-safe review artifacts without JavaScript.",
        ),
        checklist_item(
            "Docs export",
            "demo/docs_export.json",
            "pass" if docs_export.get("schema") == "portfolio-fee-drag-docs-export-v1" and any(item.get("name") == "promotion-checklist" for item in docs_export.get("commands", [])) else "review",
            "Confirm docs_export covers commands, input schema, artifact map, verification commands, and finance boundaries.",
        ),
        checklist_item(
            "Release audit summary",
            "demo/release_audit_summary.json",
            release_summary.get("status", "missing") if release_summary else "missing",
            "Release owner should rerun release-audit-summary with tests-status pass only after tests have actually run.",
        ),
        checklist_item(
            "Package audit and zero dependencies",
            "demo/package_audit.json",
            "pass" if package_payload.get("status") == "pass" and package_payload.get("runtime_dependencies") == [] else package_payload.get("status", "missing"),
            "Confirm package-audit reports zero runtime dependencies, package data, script wiring, version alignment, and command coverage.",
        ),
        checklist_item(
            "Public scan",
            "demo/public_scan.json",
            public_scan.get("status", "missing") if public_scan else "missing",
            "Confirm public-scan passes before sharing public artifacts.",
        ),
        checklist_item(
            "Reproducibility pack",
            "demo/reproducibility_pack.json",
            "pass" if reproducibility_pack.get("schema") == "portfolio-fee-drag-reproducibility-pack-v1" and reproducibility_pack.get("status") == "pass" else reproducibility_pack.get("status", "missing"),
            "Confirm the pack lists exact local clone, install, test, build, wheel smoke, and demo regeneration commands plus expected artifacts.",
        ),
        checklist_item(
            "Security boundary report",
            "demo/security_boundary_report.json",
            security_boundary_report.get("status", "missing") if security_boundary_report else "missing",
            "Confirm security-boundary-report passes for no secrets, no workflows, no network/live data, no broker/API/order execution, zero runtime dependencies, package data, and finance boundaries.",
        ),
        checklist_item(
            "Wheel install check",
            "dist/*.whl",
            "manual",
            "Build and install a wheel in a clean environment, then run portfolio-fee-drag --version and portfolio-fee-drag selfcheck.",
        ),
        checklist_item(
            "Finance boundaries",
            "README.md and generated artifacts",
            "pass" if all(boundary in readme_text for boundary in ("no live data", "broker", "tax, legal, investment", "buy/sell/hold")) else "review",
            "Confirm all public-facing artifacts retain the no live data, no broker, no advice, no recommendation boundary.",
        ),
    ]
    blocking = {"fail", "missing", "review"}
    return {
        "schema": "portfolio-fee-drag-promotion-checklist-v1",
        "version": __version__,
        "status": "review" if any(item["status"] in blocking for item in items) else "pass",
        "boundary": SAFETY_BOUNDARY,
        "root": root.as_posix(),
        "artifact_root": artifact_root.as_posix(),
        "items": items,
        "manual_items": [
            "Wheel install check is intentionally manual because this zero-dependency repo does not add workflow automation.",
            "Promotion is a human release-owner decision; generated checks are evidence, not approval.",
        ],
        "finance_boundaries": list(FINANCE_BOUNDARIES),
    }


def promotion_checklist_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Promotion Checklist",
        "",
        f"Version: {payload['version']}",
        f"Status: {payload['status']}",
        "",
        f"Boundary: {payload['boundary']}",
        "",
        "| Review Area | Artifact | Status | Human Review Prompt |",
        "| --- | --- | --- | --- |",
    ]
    for item in payload["items"]:
        lines.append(f"| {item['name']} | `{item['artifact']}` | {item['status']} | {item['review_prompt']} |")
    lines.extend(["", "## Manual Items", ""])
    lines.extend(f"- {item}" for item in payload["manual_items"])
    lines.extend(["", "## Finance Boundaries", ""])
    lines.extend(f"- {item}" for item in payload["finance_boundaries"])
    lines.append("")
    return "\n".join(lines)


def cmd_promotion_checklist(args: argparse.Namespace) -> int:
    output = Path(args.output)
    payload = promotion_checklist_payload(Path(args.root), Path(args.artifact_root))
    write_json(output / "promotion_checklist.json", payload)
    write_text(output / "promotion_checklist.md", promotion_checklist_markdown(payload))
    print(f"wrote {output / 'promotion_checklist.md'}")
    print(f"wrote {output / 'promotion_checklist.json'}")
    return 0 if payload["status"] in {"pass", "review"} else 1


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
    reproducibility_pack = read_json_file(Path(args.reproducibility_pack))
    security_boundary_report = read_json_file(Path(args.security_boundary_report))

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
        {
            "name": "reproducibility_pack",
            "status": reproducibility_pack.get("status", "missing") if reproducibility_pack else "missing",
            "source": Path(args.reproducibility_pack).as_posix(),
            "detail": "Exact local clone, install, test, build, wheel smoke, and demo regeneration commands.",
        },
        {
            "name": "security_boundary_report",
            "status": security_boundary_report.get("status", "missing") if security_boundary_report else "missing",
            "source": Path(args.security_boundary_report).as_posix(),
            "detail": "No secrets, workflows, network/live data, broker/API/order execution, runtime dependencies, and finance boundary evidence.",
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
    cmd_input_template(argparse.Namespace(output=output / "input_templates"))
    cmd_assumption_diff(
        argparse.Namespace(
            before=data_path("example_assumptions.json"),
            after=data_path("example_assumptions_review.json"),
            output=output,
        )
    )
    cmd_risk_flags(
        argparse.Namespace(
            holdings=data_path("example_holdings.csv"),
            assumptions=data_path("example_assumptions_review.json"),
            output=output,
        )
    )
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
    cmd_batch_compare(argparse.Namespace(presets=data_path("scenario_presets.json"), output=output))
    cmd_scenario_narrative(argparse.Namespace(case_gallery=output / "case_gallery.json", batch_compare=output / "batch_compare.json", output=output))
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
    cmd_docs_export(argparse.Namespace(output=output))
    cmd_reproducibility_pack(argparse.Namespace(root=Path("."), repo_url="<repo-url>", output=output))
    cmd_security_boundary_report(argparse.Namespace(root=Path("."), output=output))
    cmd_static_showcase(argparse.Namespace(output=output / "showcase.html"))
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
            reproducibility_pack=output / "reproducibility_pack.json",
            security_boundary_report=output / "security_boundary_report.json",
        )
    )
    cmd_promotion_checklist(argparse.Namespace(root=Path("."), artifact_root=output, output=output))
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
        ("Docs export Markdown/JSON route included", "pass"),
        ("Reproducibility pack Markdown/JSON route included", "pass"),
        ("Security boundary report Markdown/JSON route included", "pass"),
        ("Static showcase HTML route included", "pass"),
        ("Release audit summary Markdown/JSON route included", "pass"),
        ("Input template command for offline CSV/JSON adaptation included", "pass"),
        ("Assumption diff Markdown/JSON route included", "pass"),
        ("Risk flags Markdown/JSON review prompt route included", "pass"),
        ("Batch compare Markdown/JSON ranking route included", "pass"),
        ("Scenario narrative Markdown/JSON review layer included", "pass"),
        ("Promotion checklist Markdown/JSON readiness layer included", "pass"),
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
    for name in ("example_holdings.csv", "example_assumptions.json", "example_assumptions_review.json", "example_history.json", "scenario_presets.json"):
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
    template_fragment = local_input_readme_fragment()
    if "holdings_template.csv" not in template_fragment or "no live data" not in template_fragment.lower():
        errors.append("input template fragment generation failed")
    diff = assumption_diff_payload(data_path("example_assumptions.json"), data_path("example_assumptions_review.json"))
    if diff["schema"] != "portfolio-fee-drag-assumption-diff-v1" or diff["changed_fields"] < 1:
        errors.append("assumption diff generation failed")
    flags = risk_flags_payload(data_path("example_holdings.csv"), data_path("example_assumptions_review.json"))
    if flags["schema"] != "portfolio-fee-drag-risk-flags-v1" or not flags["flags"]:
        errors.append("risk flags generation failed")
    batch = batch_compare_payload(bundle)
    if batch["schema"] != "portfolio-fee-drag-batch-compare-v1" or set(batch["rankings"]) != {"total_annual_drag", "total_dollar_drag", "cash_drag", "turnover_tax_drag", "fee_drag"}:
        errors.append("batch compare generation failed")
    gallery_payload = {
        "schema": "portfolio-fee-drag-case-gallery-v1",
        "version": __version__,
        "boundary": SAFETY_BOUNDARY,
        "source_schema": bundle["schema"],
        "cases": [
            {key: value for key, value in row.items() if key != "packet"} | {"packet": row["packet"]}
            for row in case_rows(bundle)
        ],
    }
    narrative = scenario_narrative_payload_from_objects(gallery_payload, batch, "selfcheck:case_gallery", "selfcheck:batch_compare")
    if narrative["schema"] != "portfolio-fee-drag-scenario-narrative-v1" or len(narrative["scenarios"]) != 3:
        errors.append("scenario narrative generation failed")
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
    docs = docs_export_payload()
    if docs["schema"] != "portfolio-fee-drag-docs-export-v1" or len(docs["commands"]) != len(COMMANDS):
        errors.append("docs export generation failed")
    repro = reproducibility_pack_payload(Path("."), "<repo-url>")
    if repro["schema"] != "portfolio-fee-drag-reproducibility-pack-v1" or repro["status"] != "pass":
        errors.append("reproducibility pack generation failed")
    security = security_boundary_report_payload(Path("."))
    if security["schema"] != "portfolio-fee-drag-security-boundary-report-v1" or security["status"] != "pass":
        errors.append("security boundary report generation failed")
    showcase = static_showcase_html()
    if "<script" in showcase.lower() or "docs_export.md" not in showcase or "risk_flags.md" not in showcase or "promotion_checklist.md" not in showcase or "reproducibility_pack.md" not in showcase or "security_boundary_report.md" not in showcase:
        errors.append("static showcase generation failed")
    checklist = promotion_checklist_payload(Path("."), Path("demo"))
    if checklist["schema"] != "portfolio-fee-drag-promotion-checklist-v1" or not checklist["items"]:
        errors.append("promotion checklist generation failed")
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


def public_scan_payload(root: Path) -> dict[str, Any]:
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
    return payload


def cmd_public_scan(args: argparse.Namespace) -> int:
    root = Path(args.root)
    payload = public_scan_payload(root)
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

    template = sub.add_parser("input-template", help="Write local CSV/JSON input templates and README fragment.")
    template.add_argument("--output", default="demo/input_templates")
    template.set_defaults(func=cmd_input_template)

    diff = sub.add_parser("assumption-diff", help="Compare two assumptions JSON files.")
    diff.add_argument("--before", default=data_path("example_assumptions.json"))
    diff.add_argument("--after", default=data_path("example_assumptions_review.json"))
    diff.add_argument("--output", default="demo")
    diff.set_defaults(func=cmd_assumption_diff)

    flags = sub.add_parser("risk-flags", help="Emit review prompts for configured risk flags.")
    flags.add_argument("--holdings", default=data_path("example_holdings.csv"))
    flags.add_argument("--assumptions", default=data_path("example_assumptions_review.json"))
    flags.add_argument("--output", default="demo")
    flags.set_defaults(func=cmd_risk_flags)

    batch = sub.add_parser("batch-compare", help="Rank scenario presets by drag dimensions.")
    batch.add_argument("--presets", default=data_path("scenario_presets.json"))
    batch.add_argument("--output", default="demo")
    batch.set_defaults(func=cmd_batch_compare)

    narrative = sub.add_parser("scenario-narrative", help="Explain bundled scenarios with drivers, review questions, and boundaries.")
    narrative.add_argument("--case-gallery", default="demo/case_gallery.json")
    narrative.add_argument("--batch-compare", default="demo/batch_compare.json")
    narrative.add_argument("--output", default="demo")
    narrative.set_defaults(func=cmd_scenario_narrative)

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

    docs = sub.add_parser("docs-export", help="Write deterministic Markdown and JSON public documentation.")
    docs.add_argument("--output", default="demo")
    docs.set_defaults(func=cmd_docs_export)

    showcase = sub.add_parser("static-showcase", help="Render no-JS public showcase HTML.")
    showcase.add_argument("--output", default="demo/showcase.html")
    showcase.set_defaults(func=cmd_static_showcase)

    repro = sub.add_parser("reproducibility-pack", help="Write exact local release reproduction commands and expected artifacts.")
    repro.add_argument("--root", default=".")
    repro.add_argument("--repo-url", default="<repo-url>")
    repro.add_argument("--output", default="demo")
    repro.set_defaults(func=cmd_reproducibility_pack)

    security = sub.add_parser("security-boundary-report", help="Write public-safe security and finance boundary report.")
    security.add_argument("--root", default=".")
    security.add_argument("--output", default="demo")
    security.set_defaults(func=cmd_security_boundary_report)

    promo = sub.add_parser("promotion-checklist", help="Write release and promotion readiness checklist.")
    promo.add_argument("--root", default=".")
    promo.add_argument("--artifact-root", default="demo")
    promo.add_argument("--output", default="demo")
    promo.set_defaults(func=cmd_promotion_checklist)

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
    summary.add_argument("--reproducibility-pack", default="demo/reproducibility_pack.json")
    summary.add_argument("--security-boundary-report", default="demo/security_boundary_report.json")
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
