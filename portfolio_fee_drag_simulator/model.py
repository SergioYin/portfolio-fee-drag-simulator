from __future__ import annotations

from dataclasses import dataclass
import csv
import json
from pathlib import Path
from typing import Any, Iterable


SAFETY_BOUNDARY = (
    "Static local assumptions only; no live data, broker API, orders, "
    "predictions, portfolio optimization, tax/legal/investment advice, "
    "or buy/sell/hold recommendations."
)


@dataclass(frozen=True)
class Holding:
    account: str
    ticker: str
    name: str
    allocation: float
    expense_ratio: float


@dataclass(frozen=True)
class Assumptions:
    initial_value: float
    annual_contribution: float
    years: int
    gross_return: float
    cash_return: float = 0.0
    turnover_rate: float = 0.0
    realized_gain_rate: float = 0.0
    tax_rate: float = 0.0
    taxable_allocation: float = 0.0
    rebalance_frequency: str = "annual"
    rebalance_cost: float = 0.0
    contribution_timing: str = "beginning"


def money(value: float) -> str:
    return f"${value:,.2f}"


def pct(value: float) -> str:
    return f"{value * 100:.3f}%"


def load_holdings(path: str | Path) -> list[Holding]:
    with Path(path).open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return parse_holdings(rows)


def parse_holdings(rows: Iterable[dict[str, str]]) -> list[Holding]:
    holdings: list[Holding] = []
    for index, row in enumerate(rows, start=2):
        try:
            holdings.append(
                Holding(
                    account=row.get("account", "").strip(),
                    ticker=row.get("ticker", "").strip().upper(),
                    name=row.get("name", "").strip(),
                    allocation=float(row.get("allocation", "")),
                    expense_ratio=float(row.get("expense_ratio", "")),
                )
            )
        except ValueError as exc:
            raise ValueError(f"invalid numeric value on CSV line {index}") from exc
    return holdings


def load_assumptions(path: str | Path) -> Assumptions:
    with Path(path).open(encoding="utf-8") as fh:
        data = json.load(fh)
    return parse_assumptions(data)


def parse_assumptions(data: dict[str, Any]) -> Assumptions:
    assumptions = Assumptions(
        initial_value=float(data["initial_value"]),
        annual_contribution=float(data.get("annual_contribution", 0)),
        years=int(data["years"]),
        gross_return=float(data["gross_return"]),
        cash_return=float(data.get("cash_return", data.get("cash_yield", 0.0))),
        turnover_rate=float(data.get("turnover_rate", 0.0)),
        realized_gain_rate=float(data.get("realized_gain_rate", 0.0)),
        tax_rate=float(data.get("tax_rate", 0.0)),
        taxable_allocation=float(data.get("taxable_allocation", 0.0)),
        rebalance_frequency=str(data.get("rebalance_frequency", "annual")).strip().lower(),
        rebalance_cost=float(data.get("rebalance_cost", 0.0)),
        contribution_timing=str(data.get("contribution_timing", "beginning")).strip().lower(),
    )
    warnings = validate_assumptions(assumptions)
    if warnings:
        raise ValueError("; ".join(warnings))
    return assumptions


def validate_rate(name: str, value: float, warnings: list[str], upper: float = 1.0) -> None:
    if value < 0:
        warnings.append(f"{name} must be non-negative")
    if value > upper:
        warnings.append(f"{name} exceeds {upper:.0%}")


def validate_assumptions(assumptions: Assumptions) -> list[str]:
    warnings: list[str] = []
    if assumptions.initial_value < 0:
        warnings.append("initial_value must be non-negative")
    if assumptions.annual_contribution < 0:
        warnings.append("annual_contribution must be non-negative")
    if assumptions.years < 0:
        warnings.append("years must be non-negative")
    for name in (
        "cash_return",
        "turnover_rate",
        "realized_gain_rate",
        "tax_rate",
        "taxable_allocation",
        "rebalance_cost",
    ):
        validate_rate(name, getattr(assumptions, name), warnings)
    if assumptions.rebalance_frequency not in {"none", "annual", "quarterly", "monthly"}:
        warnings.append("rebalance_frequency must be one of none, annual, quarterly, monthly")
    if assumptions.contribution_timing not in {"beginning", "end"}:
        warnings.append("contribution_timing must be beginning or end")
    return warnings


def validate_holdings(holdings: list[Holding]) -> list[str]:
    warnings: list[str] = []
    if not holdings:
        return ["ledger has no holdings"]
    allocation = sum(item.allocation for item in holdings)
    if abs(allocation - 1.0) > 0.0001:
        warnings.append(f"allocation sum is {allocation:.6f}, expected 1.000000")
    for item in holdings:
        if not item.ticker:
            warnings.append("holding has a blank ticker")
        if item.allocation < 0:
            warnings.append(f"{item.ticker or '(blank)'} has negative allocation")
        if item.expense_ratio < 0:
            warnings.append(f"{item.ticker or '(blank)'} has negative expense ratio")
        if item.expense_ratio > 0.03:
            warnings.append(f"{item.ticker} expense ratio exceeds 3%")
    return warnings


def weighted_expense_ratio(holdings: list[Holding]) -> float:
    total = sum(item.allocation for item in holdings)
    if total == 0:
        return 0.0
    return sum(item.allocation * item.expense_ratio for item in holdings) / total


def cash_allocation(holdings: list[Holding]) -> float:
    cash_markers = ("CASH", "MMF", "MONEY MARKET", "TREASURY BILL", "T-BILL")
    return sum(
        item.allocation
        for item in holdings
        if item.ticker == "CASH" or any(marker in item.name.upper() for marker in cash_markers)
    )


def rebalance_events_per_year(frequency: str) -> int:
    return {"none": 0, "annual": 1, "quarterly": 4, "monthly": 12}[frequency]


def future_value(
    initial_value: float,
    annual_contribution: float,
    years: int,
    rate: float,
    contribution_timing: str = "beginning",
) -> float:
    value = initial_value
    for _ in range(years):
        if contribution_timing == "beginning":
            value = (value + annual_contribution) * (1 + rate)
        else:
            value = value * (1 + rate) + annual_contribution
    return value


def build_packet(holdings: list[Holding], assumptions: Assumptions) -> dict[str, Any]:
    warnings = validate_holdings(holdings)
    warnings.extend(validate_assumptions(assumptions))
    weighted_fee = weighted_expense_ratio(holdings)
    cash_weight = cash_allocation(holdings)
    cash_drag = max(assumptions.gross_return - assumptions.cash_return, 0.0) * cash_weight
    turnover_tax_drag = (
        assumptions.turnover_rate
        * assumptions.realized_gain_rate
        * assumptions.tax_rate
        * assumptions.taxable_allocation
    )
    rebalance_drag = assumptions.rebalance_cost * rebalance_events_per_year(assumptions.rebalance_frequency)
    total_drag_rate = weighted_fee + cash_drag + turnover_tax_drag + rebalance_drag
    gross_value = future_value(
        assumptions.initial_value,
        assumptions.annual_contribution,
        assumptions.years,
        assumptions.gross_return,
        assumptions.contribution_timing,
    )
    net_return = assumptions.gross_return - total_drag_rate
    net_value = future_value(
        assumptions.initial_value,
        assumptions.annual_contribution,
        assumptions.years,
        net_return,
        assumptions.contribution_timing,
    )
    total_drag = gross_value - net_value
    return {
        "schema": "portfolio-fee-drag-packet-v2",
        "safety_boundary": SAFETY_BOUNDARY,
        "assumptions": {
            "initial_value": round(assumptions.initial_value, 2),
            "annual_contribution": round(assumptions.annual_contribution, 2),
            "years": assumptions.years,
            "gross_return": assumptions.gross_return,
            "cash_return": assumptions.cash_return,
            "turnover_rate": assumptions.turnover_rate,
            "realized_gain_rate": assumptions.realized_gain_rate,
            "tax_rate": assumptions.tax_rate,
            "taxable_allocation": assumptions.taxable_allocation,
            "rebalance_frequency": assumptions.rebalance_frequency,
            "rebalance_cost": assumptions.rebalance_cost,
            "contribution_timing": assumptions.contribution_timing,
        },
        "summary": {
            "weighted_expense_ratio": round(weighted_fee, 8),
            "cash_allocation": round(cash_weight, 8),
            "cash_drag_rate": round(cash_drag, 8),
            "turnover_tax_drag_rate": round(turnover_tax_drag, 8),
            "rebalance_drag_rate": round(rebalance_drag, 8),
            "total_annual_drag_rate": round(total_drag_rate, 8),
            "gross_future_value": round(gross_value, 2),
            "net_future_value": round(net_value, 2),
            "fee_drag": round(total_drag, 2),
            "total_drag": round(total_drag, 2),
            "net_return_after_expenses": round(net_return, 8),
            "net_return_after_all_drags": round(net_return, 8),
        },
        "holdings": [
            {
                "account": item.account,
                "ticker": item.ticker,
                "name": item.name,
                "allocation": item.allocation,
                "expense_ratio": item.expense_ratio,
                "weighted_fee": round(item.allocation * item.expense_ratio, 8),
            }
            for item in holdings
        ],
        "warnings": warnings,
    }


def packet_markdown(packet: dict[str, Any]) -> str:
    summary = packet["summary"]
    assumptions = packet["assumptions"]
    lines = [
        "# Portfolio Fee Drag Packet",
        "",
        f"Boundary: {packet['safety_boundary']}",
        "",
        "## Summary",
        "",
        f"- Initial value: {money(assumptions['initial_value'])}",
        f"- Annual contribution: {money(assumptions['annual_contribution'])}",
        f"- Years: {assumptions['years']}",
        f"- Gross return assumption: {pct(assumptions['gross_return'])}",
        f"- Contribution timing: {assumptions['contribution_timing']}",
        f"- Weighted expense ratio: {pct(summary['weighted_expense_ratio'])}",
        f"- Cash allocation: {pct(summary['cash_allocation'])}",
        f"- Cash drag rate: {pct(summary['cash_drag_rate'])}",
        f"- Turnover/tax drag rate: {pct(summary['turnover_tax_drag_rate'])}",
        f"- Rebalance drag rate: {pct(summary['rebalance_drag_rate'])}",
        f"- Total annual drag rate: {pct(summary['total_annual_drag_rate'])}",
        f"- Gross future value: {money(summary['gross_future_value'])}",
        f"- Net future value: {money(summary['net_future_value'])}",
        f"- Estimated total drag: {money(summary['total_drag'])}",
        "",
        "## Assumption Detail",
        "",
        f"- Cash return assumption: {pct(assumptions['cash_return'])}",
        f"- Turnover rate: {pct(assumptions['turnover_rate'])}",
        f"- Realized gain rate on turnover: {pct(assumptions['realized_gain_rate'])}",
        f"- Tax rate on realized gains: {pct(assumptions['tax_rate'])}",
        f"- Taxable allocation: {pct(assumptions['taxable_allocation'])}",
        f"- Rebalance frequency: {assumptions['rebalance_frequency']}",
        f"- Rebalance cost per event: {pct(assumptions['rebalance_cost'])}",
        "",
        "## Holdings",
        "",
        "| Account | Ticker | Allocation | Expense Ratio | Weighted Fee |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for item in packet["holdings"]:
        lines.append(
            "| {account} | {ticker} | {allocation} | {expense_ratio} | {weighted_fee} |".format(
                account=item["account"],
                ticker=item["ticker"],
                allocation=pct(item["allocation"]),
                expense_ratio=pct(item["expense_ratio"]),
                weighted_fee=pct(item["weighted_fee"]),
            )
        )
    lines.extend(["", "## Review Notes", ""])
    if packet["warnings"]:
        lines.extend(f"- {warning}" for warning in packet["warnings"])
    else:
        lines.append("- No ledger warnings.")
    lines.append("")
    return "\n".join(lines)


def sensitivity_rows(packet: dict[str, Any], fee_steps: list[float], return_steps: list[float]) -> list[dict[str, Any]]:
    assumptions = packet["assumptions"]
    base_drag = (
        packet["summary"].get("cash_drag_rate", 0.0)
        + packet["summary"].get("turnover_tax_drag_rate", 0.0)
        + packet["summary"].get("rebalance_drag_rate", 0.0)
    )
    rows: list[dict[str, Any]] = []
    for gross_return in return_steps:
        gross_value = future_value(
            assumptions["initial_value"],
            assumptions["annual_contribution"],
            assumptions["years"],
            gross_return,
            assumptions.get("contribution_timing", "beginning"),
        )
        for fee in fee_steps:
            total_drag_rate = fee + base_drag
            net_value = future_value(
                assumptions["initial_value"],
                assumptions["annual_contribution"],
                assumptions["years"],
                gross_return - total_drag_rate,
                assumptions.get("contribution_timing", "beginning"),
            )
            rows.append(
                {
                    "gross_return": gross_return,
                    "expense_ratio": fee,
                    "other_drag_rate": round(base_drag, 8),
                    "total_drag_rate": round(total_drag_rate, 8),
                    "fee_drag": round(gross_value - net_value, 2),
                    "net_future_value": round(net_value, 2),
                }
            )
    return rows
