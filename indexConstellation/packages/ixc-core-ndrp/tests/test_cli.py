import io
import json
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout

import ndrpy


VALID_ENTRY = {
    "role": "user",
    "content": "Example content",
    "intent": "instruction",
    "mode": "instruction",
    "context": "Example context",
    "reasoning_expanded": None,
    "metadata": {"source_id": "demo", "lfsl_enabled": False},
    "meaning_preserved": True,
    "density_goal": "medium",
    "entropy_class": "low",
}


class CLITests(unittest.TestCase):
    def test_cli_reports_clean_dataset(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "dataset.json"
            with data_path.open("w", encoding="utf-8") as f:
                json.dump([VALID_ENTRY], f)

            buf = io.StringIO()
            with redirect_stdout(buf):
                exit_code = ndrpy.main(["validate", str(data_path)])

            output = buf.getvalue()
            self.assertEqual(exit_code, 0)
            self.assertIn("Hygiene Score: 100", output)
            self.assertIn("Rating: clean", output)
            self.assertIn("No issues detected", output)

    def test_cli_writes_redacted_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "dataset.json"
            report_path = Path(tmpdir) / "report.json"
            with data_path.open("w", encoding="utf-8") as f:
                json.dump([VALID_ENTRY], f)

            buf = io.StringIO()
            with redirect_stdout(buf):
                exit_code = ndrpy.main(
                    ["validate", str(data_path), "--redact", "--output", str(report_path)]
                )

            self.assertEqual(exit_code, 0)
            with report_path.open("r", encoding="utf-8") as f:
                report = json.load(f)

            self.assertTrue(report["redacted"])
            self.assertEqual(report["aggregation"]["hygiene_score"], 100)
            self.assertEqual(report["validator_results"], [])
            self.assertEqual(report["payload"][0]["content"], "[REDACTED]")

    def test_cli_exits_with_errors_on_invalid_entry(self):
        invalid_entry = dict(VALID_ENTRY)
        invalid_entry.pop("intent")

        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir) / "dataset.json"
            with data_path.open("w", encoding="utf-8") as f:
                json.dump([invalid_entry], f)

            buf = io.StringIO()
            with redirect_stdout(buf):
                exit_code = ndrpy.main(["validate", str(data_path)])

            output = buf.getvalue()
            self.assertEqual(exit_code, 1)
            self.assertIn("Hygiene Score: 90", output)
            self.assertIn("Findings: 1", output)


if __name__ == "__main__":
    unittest.main()
