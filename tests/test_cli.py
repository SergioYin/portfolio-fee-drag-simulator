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
            self.assertTrue((out / "input_templates" / "holdings_template.csv").exists())
            self.assertTrue((out / "input_templates" / "assumptions_template.json").exists())
            self.assertTrue((out / "input_templates" / "local_inputs_README.md").exists())
            self.assertTrue((out / "assumption_diff.md").exists())
            self.assertTrue((out / "assumption_diff.json").exists())
            self.assertTrue((out / "risk_flags.md").exists())
            self.assertTrue((out / "risk_flags.json").exists())
            self.assertTrue((out / "scenario_presets.json").exists())
            self.assertTrue((out / "case_gallery.md").exists())
            self.assertTrue((out / "case_gallery.json").exists())
            self.assertTrue((out / "case_gallery.html").exists())
            self.assertTrue((out / "batch_compare.md").exists())
            self.assertTrue((out / "batch_compare.json").exists())
            self.assertTrue((out / "scenario_narrative.md").exists())
            self.assertTrue((out / "scenario_narrative.json").exists())
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
            self.assertTrue((out / "docs_export.md").exists())
            self.assertTrue((out / "docs_export.json").exists())
            self.assertTrue((out / "reproducibility_pack.md").exists())
            self.assertTrue((out / "reproducibility_pack.json").exists())
            self.assertTrue((out / "security_boundary_report.md").exists())
            self.assertTrue((out / "security_boundary_report.json").exists())
            self.assertTrue((out / "promotion_checklist.md").exists())
            self.assertTrue((out / "promotion_checklist.json").exists())
            self.assertTrue((out / "showcase.html").exists())
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
            batch = json.loads((out / "batch_compare.json").read_text())
            self.assertEqual(batch["schema"], "portfolio-fee-drag-batch-compare-v1")
            self.assertEqual(set(batch["rankings"]), {"total_annual_drag", "total_dollar_drag", "cash_drag", "turnover_tax_drag", "fee_drag"})
            self.assertIn("not recommendations", (out / "batch_compare.md").read_text())
            narrative = json.loads((out / "scenario_narrative.json").read_text())
            self.assertEqual(narrative["schema"], "portfolio-fee-drag-scenario-narrative-v1")
            self.assertEqual(len(narrative["scenarios"]), 3)
            self.assertIn("not tax, legal, investment, or buy/sell/hold advice", narrative["review_note"])
            self.assertIn("Questions for human review", (out / "scenario_narrative.md").read_text())
            template_readme = (out / "input_templates" / "local_inputs_README.md").read_text()
            self.assertIn("without live data", template_readme)
            self.assertIn("not tax, legal, investment, or buy/sell/hold advice", template_readme)
            diff = json.loads((out / "assumption_diff.json").read_text())
            self.assertEqual(diff["schema"], "portfolio-fee-drag-assumption-diff-v1")
            self.assertGreater(diff["changed_fields"], 0)
            self.assertTrue(any(item["field"] == "years" and item["direction"] == "higher" for item in diff["field_deltas"]))
            self.assertIn("no tax, legal, investment, or buy/sell/hold advice", diff["review_note"])
            flags = json.loads((out / "risk_flags.json").read_text())
            self.assertEqual(flags["schema"], "portfolio-fee-drag-risk-flags-v1")
            self.assertEqual(flags["status"], "review")
            self.assertIn("long_horizon", {item["name"] for item in flags["flags"]})
            self.assertIn("not recommendations", (out / "risk_flags.md").read_text())
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
            self.assertIn("assumption_diff.md", catalog_paths)
            self.assertIn("assumption_diff.json", catalog_paths)
            self.assertIn("risk_flags.md", catalog_paths)
            self.assertIn("risk_flags.json", catalog_paths)
            self.assertIn("docs_export.md", catalog_paths)
            self.assertIn("docs_export.json", catalog_paths)
            self.assertIn("reproducibility_pack.md", catalog_paths)
            self.assertIn("reproducibility_pack.json", catalog_paths)
            self.assertIn("security_boundary_report.md", catalog_paths)
            self.assertIn("security_boundary_report.json", catalog_paths)
            self.assertIn("showcase.html", catalog_paths)
            self.assertIn("input_templates/local_inputs_README.md", catalog_paths)
            self.assertIn("batch_compare.md", catalog_paths)
            self.assertIn("batch_compare.json", catalog_paths)
            self.assertIn("scenario_narrative.md", catalog_paths)
            self.assertIn("scenario_narrative.json", catalog_paths)
            self.assertIn("promotion_checklist.md", catalog_paths)
            self.assertIn("promotion_checklist.json", catalog_paths)
            self.assertTrue(all("promotion_usefulness" in item for item in catalog["artifacts"]))
            docs = json.loads((out / "docs_export.json").read_text())
            self.assertEqual(docs["schema"], "portfolio-fee-drag-docs-export-v1")
            self.assertEqual({item["name"] for item in docs["commands"]}, set(COMMANDS))
            self.assertIn("artifact_map", docs)
            self.assertIn("finance_boundaries", docs)
            repro = json.loads((out / "reproducibility_pack.json").read_text())
            self.assertEqual(repro["schema"], "portfolio-fee-drag-reproducibility-pack-v1")
            self.assertEqual(repro["status"], "pass")
            self.assertTrue(any(item["phase"] == "wheel smoke" for item in repro["commands"]))
            self.assertIn("demo/security_boundary_report.json", repro["expected_artifacts"])
            security = json.loads((out / "security_boundary_report.json").read_text())
            self.assertEqual(security["schema"], "portfolio-fee-drag-security-boundary-report-v1")
            self.assertEqual(security["status"], "pass")
            self.assertEqual(security["runtime_dependencies"], [])
            self.assertEqual(security["workflow_files"], [])
            self.assertIn("data/*.json", security["package_data"])
            showcase = (out / "showcase.html").read_text()
            self.assertIn("dashboard.html", showcase)
            self.assertIn("case_gallery.html", showcase)
            self.assertIn("visual_receipt.html", showcase)
            self.assertIn("cold_start_walkthrough.md", showcase)
            self.assertIn("decision_journal.md", showcase)
            self.assertIn("artifact_catalog.md", showcase)
            self.assertIn("release_audit_summary.md", showcase)
            self.assertIn("package_audit.md", showcase)
            self.assertIn("docs_export.md", showcase)
            self.assertIn("reproducibility_pack.md", showcase)
            self.assertIn("security_boundary_report.md", showcase)
            self.assertIn("input_templates/local_inputs_README.md", showcase)
            self.assertIn("assumption_diff.md", showcase)
            self.assertIn("risk_flags.md", showcase)
            self.assertIn("batch_compare.md", showcase)
            self.assertIn("scenario_narrative.md", showcase)
            self.assertIn("promotion_checklist.md", showcase)
            self.assertNotIn("<script", showcase.lower())
            checklist = json.loads((out / "promotion_checklist.json").read_text())
            self.assertEqual(checklist["schema"], "portfolio-fee-drag-promotion-checklist-v1")
            self.assertTrue(any(item["name"] == "Wheel install check" for item in checklist["items"]))
            self.assertTrue(any(item["name"] == "Reproducibility pack" for item in checklist["items"]))
            self.assertTrue(any(item["name"] == "Security boundary report" for item in checklist["items"]))
            self.assertTrue(any("No live market data" in item for item in checklist["finance_boundaries"]))
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

    def test_docs_export_and_static_showcase_commands_export_public_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "demo"
            self.assertEqual(main(["docs-export", "--output", str(out)]), 0)
            docs = json.loads((out / "docs_export.json").read_text())
            self.assertEqual(docs["schema"], "portfolio-fee-drag-docs-export-v1")
            self.assertEqual(docs["version"], "1.0.0")
            self.assertEqual([item["name"] for item in docs["commands"]], sorted(COMMANDS))
            self.assertEqual(docs["input_schema"]["holdings_csv"]["columns"][0]["name"], "account")
            self.assertTrue(any(item["path"] == "showcase.html" for item in docs["artifact_map"]))
            self.assertTrue(any(item["path"] == "assumption_diff.md" for item in docs["artifact_map"]))
            self.assertTrue(any(item["path"] == "risk_flags.md" for item in docs["artifact_map"]))
            self.assertTrue(any(item["path"] == "batch_compare.md" for item in docs["artifact_map"]))
            self.assertTrue(any(item["path"] == "scenario_narrative.md" for item in docs["artifact_map"]))
            self.assertTrue(any(item["path"] == "promotion_checklist.md" for item in docs["artifact_map"]))
            self.assertTrue(any(item["path"] == "reproducibility_pack.md" for item in docs["artifact_map"]))
            self.assertTrue(any(item["path"] == "security_boundary_report.md" for item in docs["artifact_map"]))
            self.assertIn("python -m unittest discover -s tests", docs["verification_commands"])
            self.assertIn("python -m portfolio_fee_drag_simulator security-boundary-report --root . --output demo", docs["verification_commands"])
            self.assertTrue(any("No live market data" in item for item in docs["finance_boundaries"]))

            self.assertEqual(main(["static-showcase", "--output", str(out / "showcase.html")]), 0)
            showcase = (out / "showcase.html").read_text()
            self.assertIn("<title>Portfolio Fee Drag Public Showcase</title>", showcase)
            self.assertIn("dashboard.html", showcase)
            self.assertIn("docs_export.md", showcase)
            self.assertIn("assumption_diff.md", showcase)
            self.assertIn("risk_flags.md", showcase)
            self.assertIn("batch_compare.md", showcase)
            self.assertIn("scenario_narrative.md", showcase)
            self.assertIn("promotion_checklist.md", showcase)
            self.assertIn("reproducibility_pack.md", showcase)
            self.assertIn("security_boundary_report.md", showcase)
            self.assertNotIn("<script", showcase.lower())

    def test_reproducibility_pack_and_security_boundary_report_commands_export_hardening_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "demo"
            self.assertEqual(main(["reproducibility-pack", "--root", ".", "--output", str(out)]), 0)
            repro = json.loads((out / "reproducibility_pack.json").read_text())
            self.assertEqual(repro["schema"], "portfolio-fee-drag-reproducibility-pack-v1")
            self.assertEqual(repro["status"], "pass")
            self.assertTrue(any(item["phase"] == "build" for item in repro["commands"]))
            self.assertTrue(any("quickstart-check" in command for item in repro["commands"] for command in item["commands"]))
            self.assertIn("demo/reproducibility_pack.md", repro["expected_artifacts"])

            self.assertEqual(main(["security-boundary-report", "--root", ".", "--output", str(out)]), 0)
            security = json.loads((out / "security_boundary_report.json").read_text())
            self.assertEqual(security["schema"], "portfolio-fee-drag-security-boundary-report-v1")
            self.assertEqual(security["status"], "pass")
            self.assertEqual(security["secret_marker_findings"], [])
            self.assertEqual(security["workflow_files"], [])
            self.assertEqual(security["network_import_findings"], [])
            self.assertEqual(security["runtime_dependencies"], [])
            self.assertIn("data/*.csv", security["package_data"])

    def test_assumption_diff_and_risk_flags_commands_export_review_prompts(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "demo"
            self.assertEqual(main(["assumption-diff", "--output", str(out)]), 0)
            diff = json.loads((out / "assumption_diff.json").read_text())
            self.assertEqual(diff["schema"], "portfolio-fee-drag-assumption-diff-v1")
            fields = {item["field"]: item for item in diff["field_deltas"]}
            self.assertEqual(fields["years"]["direction"], "higher")
            self.assertIn("Review", (out / "assumption_diff.md").read_text())

            holdings = Path(tmp) / "holdings.csv"
            holdings.write_text(
                "account,ticker,name,allocation,expense_ratio\n"
                "Taxable,CASH,Treasury Money Market,0.30,0.001\n"
                "Taxable,ACTIVE,Active Fund,0.50,0.012\n"
                "Taxable,CORE,Core Fund,0.25,0.002\n",
                encoding="utf-8",
            )
            self.assertEqual(main(["risk-flags", "--holdings", str(holdings), "--output", str(out)]), 0)
            flags = json.loads((out / "risk_flags.json").read_text())
            self.assertEqual(flags["schema"], "portfolio-fee-drag-risk-flags-v1")
            names = {item["name"] for item in flags["flags"]}
            self.assertTrue(
                {
                    "high_cash_allocation",
                    "high_expense_ratio",
                    "high_turnover_tax_drag",
                    "allocation_mismatch",
                    "long_horizon",
                    "frequent_rebalancing",
                }.issubset(names)
            )
            self.assertIn("not recommendations", flags["review_note"])

    def test_input_template_and_batch_compare_commands_export_public_safe_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "demo"
            self.assertEqual(main(["input-template", "--output", str(out / "input_templates")]), 0)
            self.assertTrue((out / "input_templates" / "holdings_template.csv").exists())
            assumptions = json.loads((out / "input_templates" / "assumptions_template.json").read_text())
            self.assertIn("No live data", assumptions["template_note"])
            readme = (out / "input_templates" / "local_inputs_README.md").read_text()
            self.assertIn("Do not paste secrets", readme)

            self.assertEqual(main(["batch-compare", "--output", str(out)]), 0)
            payload = json.loads((out / "batch_compare.json").read_text())
            self.assertEqual(payload["schema"], "portfolio-fee-drag-batch-compare-v1")
            self.assertEqual(len(payload["cases"]), 3)
            self.assertEqual(payload["rankings"]["total_annual_drag"][0]["rank"], 1)
            self.assertTrue(payload["next_action_review_questions"])
            markdown = (out / "batch_compare.md").read_text()
            self.assertIn("These questions are for human review only and are not recommendations.", markdown)

            self.assertEqual(main(["case-gallery", "--output", str(out)]), 0)
            self.assertEqual(main(["scenario-narrative", "--case-gallery", str(out / "case_gallery.json"), "--batch-compare", str(out / "batch_compare.json"), "--output", str(out)]), 0)
            narrative = json.loads((out / "scenario_narrative.json").read_text())
            self.assertEqual(narrative["schema"], "portfolio-fee-drag-scenario-narrative-v1")
            self.assertTrue(all(item["key_drag_drivers"] for item in narrative["scenarios"]))
            self.assertIn("No-advice boundary", (out / "scenario_narrative.md").read_text())

    def test_promotion_checklist_command_exports_release_readiness_prompts(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "demo"
            self.assertEqual(main(["quickstart-check", "--output", str(out)]), 0)
            self.assertEqual(main(["promotion-checklist", "--artifact-root", str(out), "--output", str(out)]), 0)
            payload = json.loads((out / "promotion_checklist.json").read_text())
            self.assertEqual(payload["schema"], "portfolio-fee-drag-promotion-checklist-v1")
            names = {item["name"] for item in payload["items"]}
            self.assertTrue(
                {
                    "README boundary and command coverage",
                    "Quickstart demo artifacts",
                    "Static showcase",
                    "Docs export",
                    "Release audit summary",
                    "Package audit and zero dependencies",
                    "Public scan",
                    "Reproducibility pack",
                    "Security boundary report",
                    "Wheel install check",
                    "Finance boundaries",
                }.issubset(names)
            )
            markdown = (out / "promotion_checklist.md").read_text()
            self.assertIn("Wheel install", markdown)
            self.assertIn("Reproducibility pack", markdown)
            self.assertIn("Security boundary report", markdown)
            self.assertIn("No live market data", markdown)

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
                    "--reproducibility-pack",
                    str(out / "reproducibility_pack.json"),
                    "--security-boundary-report",
                    str(out / "security_boundary_report.json"),
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
