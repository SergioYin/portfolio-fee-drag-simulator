import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from portfolio_fee_drag_simulator.cli import COMMANDS, build_parser, main
from portfolio_fee_drag_simulator.model import build_packet, load_assumptions, load_holdings


class PortfolioFeeDragTests(unittest.TestCase):
    def test_demo_packet_is_deterministic(self):
        holdings = load_holdings("portfolio_fee_drag_simulator/data/example_holdings.csv")
        assumptions = load_assumptions("portfolio_fee_drag_simulator/data/example_assumptions.json")
        packet = build_packet(holdings, assumptions)
        self.assertEqual(packet["summary"]["weighted_expense_ratio"], 0.00047)
        self.assertEqual(packet["summary"]["cash_allocation"], 0.1)
        self.assertEqual(packet["summary"]["cash_drag_rate"], 0.003)
        self.assertEqual(packet["summary"]["turnover_tax_drag_rate"], 0.00441)
        self.assertEqual(packet["summary"]["rebalance_drag_rate"], 0.0002)
        self.assertEqual(packet["summary"]["total_annual_drag_rate"], 0.00808)
        self.assertEqual(packet["summary"]["fee_drag"], 56388.26)
        self.assertEqual(packet["assumptions"]["contribution_timing"], "beginning")

    def test_all_required_commands_are_registered(self):
        choices = build_parser()._subparsers._group_actions[0].choices
        self.assertEqual(set(choices), set(COMMANDS))

    def test_quickstart_writes_demo_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "demo"
            code = main(["quickstart-check", "--output", str(out)])
            self.assertEqual(code, 0)
            self.assertTrue((out / "fee_drag_packet.md").exists())
            self.assertTrue((out / "dashboard.html").exists())
            packet = json.loads((out / "fee_drag_packet.json").read_text())
            self.assertIn("cash_drag_rate", packet["summary"])
            self.assertIn("turnover_tax_drag_rate", packet["summary"])
            self.assertIn("rebalance_drag_rate", packet["summary"])
            scan = json.loads((out / "public_scan.json").read_text())
            self.assertEqual(scan["status"], "pass")

    def test_module_selfcheck(self):
        result = subprocess.run(
            [sys.executable, "-m", "portfolio_fee_drag_simulator", "selfcheck"],
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"status": "pass"', result.stdout)


if __name__ == "__main__":
    unittest.main()
