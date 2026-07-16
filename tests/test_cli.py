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
            self.assertTrue((out / "scenario_presets.json").exists())
            self.assertTrue((out / "case_gallery.md").exists())
            self.assertTrue((out / "case_gallery.json").exists())
            self.assertTrue((out / "case_gallery.html").exists())
            self.assertTrue((out / "visual_receipt.md").exists())
            self.assertTrue((out / "visual_receipt.json").exists())
            self.assertTrue((out / "visual_receipt.html").exists())
            self.assertTrue((out / "cold_start_walkthrough.md").exists())
            self.assertTrue((out / "cold_start_walkthrough.json").exists())
            packet = json.loads((out / "fee_drag_packet.json").read_text())
            self.assertIn("cash_drag_rate", packet["summary"])
            self.assertIn("turnover_tax_drag_rate", packet["summary"])
            self.assertIn("rebalance_drag_rate", packet["summary"])
            gallery = json.loads((out / "case_gallery.json").read_text())
            self.assertEqual(gallery["schema"], "portfolio-fee-drag-case-gallery-v1")
            self.assertEqual([case["slug"] for case in gallery["cases"]], [
                "cash-heavy-waitlist",
                "high-turnover-taxable-fund",
                "low-cost-etf",
            ])
            receipt = json.loads((out / "visual_receipt.json").read_text())
            self.assertEqual(receipt["schema"], "portfolio-fee-drag-visual-receipt-v1")
            self.assertTrue(receipt["complete"])
            self.assertEqual([item["path"] for item in receipt["artifacts"]], [
                "dashboard.html",
                "case_gallery.md",
                "case_gallery.json",
                "case_gallery.html",
            ])
            self.assertTrue(all(item["sha256"] for item in receipt["artifacts"]))
            walkthrough = json.loads((out / "cold_start_walkthrough.json").read_text())
            self.assertEqual(walkthrough["schema"], "portfolio-fee-drag-cold-start-walkthrough-v1")
            self.assertEqual(walkthrough["timebox_minutes"], 10)
            self.assertEqual(len(walkthrough["steps"]), 6)
            scan = json.loads((out / "public_scan.json").read_text())
            self.assertEqual(scan["status"], "pass")

    def test_scenario_presets_command_exports_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "scenario_presets.json"
            code = main(["scenario-presets", "--output", str(output)])
            self.assertEqual(code, 0)
            payload = json.loads(output.read_text())
            self.assertEqual(payload["schema"], "portfolio-fee-drag-scenario-presets-v1")
            self.assertEqual(len(payload["scenarios"]), 3)

    def test_visual_receipt_reports_missing_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "demo"
            code = main(["visual-receipt", "--artifact-root", str(out), "--output", str(out)])
            self.assertEqual(code, 1)
            payload = json.loads((out / "visual_receipt.json").read_text())
            self.assertFalse(payload["complete"])
            self.assertIsNone(payload["artifacts"][0]["sha256"])

    def test_cold_start_walkthrough_command_exports_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "demo"
            code = main(["cold-start-walkthrough", "--output", str(out)])
            self.assertEqual(code, 0)
            payload = json.loads((out / "cold_start_walkthrough.json").read_text())
            self.assertEqual(payload["schema"], "portfolio-fee-drag-cold-start-walkthrough-v1")
            self.assertIn("First-time GitHub user", payload["audience"])

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
