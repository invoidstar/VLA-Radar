"""Offline safety tests for bounded P1 external evidence checks (no network)."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "maintenance" / "probe_p1_sources.py"
spec = importlib.util.spec_from_file_location("p1_probe", SCRIPT)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class ProbeTests(unittest.TestCase):
    def test_source_allowlist_rejects_unexpected_hosts(self):
        with self.assertRaisesRegex(ValueError, "allowlist"):
            probe.read_public_json("https://example.org/private")
        with self.assertRaisesRegex(ValueError, "allowlist"):
            probe.read_public_json("http://api.openalex.org/works")

    def test_robodojo_artifact_preserves_exact_raw_bytes(self):
        content = b'{"models":[{"name":"test"}]}'
        with tempfile.TemporaryDirectory() as folder:
            with mock.patch.object(probe, "read_public_json", return_value=(json.loads(content), content)):
                outcome = probe.probe_robodojo(Path(folder))
            self.assertEqual(outcome["status"], "fetched-unverified")
            self.assertEqual((Path(folder)/outcome["artifact"]).read_bytes(), content)
            self.assertTrue(outcome["immutable"])
            self.assertEqual(len(outcome["sha256"]), 64)

    def test_provider_errors_do_not_claim_success(self):
        with tempfile.TemporaryDirectory() as folder:
            with mock.patch.object(probe, "openalex_query", side_effect=TimeoutError("timeout")):
                with mock.patch.object(probe, "semantic_query", side_effect=ValueError("invalid")):
                    with mock.patch.object(probe, "probe_robodojo", return_value={"status": "blocked"}):
                        probe.execute(Path(folder), "2026-09-20", "2026-11-14")
            doc = json.loads((Path(folder)/"probe-report.json").read_text(encoding="utf-8"))
            self.assertEqual(len(doc["academicIndex"]), 6)
            self.assertTrue(all(row["status"] == "blocked" for row in doc["academicIndex"]))
            self.assertFalse(doc["checkpointAdvanced"])
            self.assertFalse(doc["publicationOrRankingUpdated"])

    def test_date_window_must_be_bounded(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "bounded"):
                probe.execute(Path(folder), "2026-01-01", "2026-11-14")


if __name__ == "__main__":
    unittest.main()
