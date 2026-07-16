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
            self.assertTrue((out / "fixture_doctor.md").exists())
            self.assertTrue((out / "fixture_doctor.json").exists())
            self.assertTrue((out / "package_audit.md").exists())
            self.assertTrue((out / "package_audit.json").exists())
            self.assertTrue((out / "decision_journal.md").exists())
            self.assertTrue((out / "decision_journal.json").exists())
            self.assertTrue((out / "selfcheck.json").exists())
            self.assertTrue((out / "release_audit_summary.md").exists())
            self.assertTrue((out / "release_audit_summary.json").exists())
            self.assertTrue((out / "artifact_catalog.md").exists())
            self.assertTrue((out / "artifact_catalog.json").exists())
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
            doctor = json.loads((out / "fixture_doctor.json").read_text())
            self.assertEqual(doctor["status"], "pass")
            package = json.loads((out / "package_audit.json").read_text())
            self.assertEqual(package["status"], "pass")
            journal = json.loads((out / "decision_journal.json").read_text())
            self.assertEqual(journal["schema"], "portfolio-fee-drag-decision-journal-v1")
            self.assertEqual(journal["next_review_date"], "")
            self.assertEqual([item["name"] for item in journal["research_note_prompts"]], [
                "assumptions_changed",
                "human_verification",
                "no_advice_boundary",
                "next_review_date",
            ])
            catalog = json.loads((out / "artifact_catalog.json").read_text())
            self.assertEqual(catalog["schema"], "portfolio-fee-drag-artifact-catalog-v1")
            self.assertTrue(catalog["complete"])
            catalog_paths = [item["path"] for item in catalog["artifacts"]]
            self.assertIn("decision_journal.json", catalog_paths)
            self.assertTrue(all("promotion_usefulness" in item for item in catalog["artifacts"]))
            summary = json.loads((out / "release_audit_summary.json").read_text())
            self.assertEqual(summary["status"], "review")
            self.assertEqual(summary["checks"][0]["status"], "not-run")

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

    def test_fixture_doctor_and_package_audit_pass_for_bundled_release_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "demo"
            self.assertEqual(main(["fixture-doctor", "--output", str(out)]), 0)
            doctor = json.loads((out / "fixture_doctor.json").read_text())
            self.assertEqual(doctor["schema"], "portfolio-fee-drag-fixture-doctor-v1")
            self.assertEqual(doctor["status"], "pass")
            self.assertEqual(doctor["issues"], [])

            self.assertEqual(main(["package-audit", "--root", ".", "--output", str(out)]), 0)
            package = json.loads((out / "package_audit.json").read_text())
            self.assertEqual(package["schema"], "portfolio-fee-drag-package-audit-v1")
            self.assertEqual(package["status"], "pass")
            self.assertEqual(package["runtime_dependencies"], [])
            self.assertEqual(set(package["commands"]), set(COMMANDS))

    def test_decision_journal_and_artifact_catalog_commands_export_bundles(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "demo"
            self.assertEqual(main(["quickstart-check", "--output", str(out)]), 0)
            self.assertEqual(main(["decision-journal", "--packet", str(out / "fee_drag_packet.json"), "--gallery", str(out / "case_gallery.json"), "--output", str(out)]), 0)
            journal = json.loads((out / "decision_journal.json").read_text())
            self.assertIn("Human Verification Needed", journal["research_note_prompts"][1]["prompt"])
            self.assertIn("buy/sell/hold", journal["research_note_prompts"][2]["prompt"])

            self.assertEqual(main(["artifact-catalog", "--artifact-root", str(out), "--output", str(out)]), 0)
            catalog = json.loads((out / "artifact_catalog.json").read_text())
            first = catalog["artifacts"][0]
            self.assertEqual(set(first), {"path", "route", "bytes", "sha256", "producer_command", "role", "promotion_usefulness", "exists"})
            self.assertTrue(first["sha256"])

    def test_release_audit_summary_can_pass_after_release_owner_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "demo"
            self.assertEqual(main(["quickstart-check", "--output", str(out)]), 0)
            code = main(
                [
                    "release-audit-summary",
                    "--output",
                    str(out),
                    "--tests-status",
                    "pass",
                    "--selfcheck",
                    str(out / "selfcheck.json"),
                    "--public-scan",
                    str(out / "public_scan.json"),
                    "--manifest",
                    str(out / "release_manifest.json"),
                    "--visual-receipt",
                    str(out / "visual_receipt.json"),
                    "--fixture-doctor",
                    str(out / "fixture_doctor.json"),
                    "--package-audit",
                    str(out / "package_audit.json"),
                ]
            )
            self.assertEqual(code, 0)
            payload = json.loads((out / "release_audit_summary.json").read_text())
            self.assertEqual(payload["schema"], "portfolio-fee-drag-release-audit-summary-v1")
            self.assertEqual(payload["status"], "pass")
            self.assertEqual(payload["release_owner_actions"], [])

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
