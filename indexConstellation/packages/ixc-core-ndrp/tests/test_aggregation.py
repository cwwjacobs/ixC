import unittest

from validator.aggregation import (
    DEFAULT_SEVERITY_WEIGHTS,
    UNKNOWN_SEVERITY_WEIGHT,
    aggregate_validator_results,
)


class AggregationTests(unittest.TestCase):
    def test_empty_results_are_clean(self):
        result = aggregate_validator_results([])

        self.assertEqual(result["hygiene_score"], 100)
        self.assertEqual(result["rating"], "clean")
        self.assertEqual(
            result["summary"],
            ["No issues detected", "Data appears ready for use"],
        )
        for severity in DEFAULT_SEVERITY_WEIGHTS:
            self.assertEqual(result["severity_counts"].get(severity, 0), 0)

    def test_mixed_severities_compute_penalty(self):
        results = [
            {"severity": "high"},
            {"severity": "medium"},
            {"severity": "low"},
        ]

        aggregated = aggregate_validator_results(results)

        self.assertEqual(aggregated["hygiene_score"], 86)  # 10 + 3 + 1 penalty
        self.assertEqual(aggregated["rating"], "needs_attention")
        self.assertEqual(
            aggregated["summary"],
            ["High-severity issues detected", "Data suitable for internal use only"],
        )
        self.assertEqual(aggregated["severity_counts"]["high"], 1)
        self.assertEqual(aggregated["severity_counts"]["medium"], 1)
        self.assertEqual(aggregated["severity_counts"]["low"], 1)

    def test_unknown_severity_uses_fallback_weight(self):
        aggregated = aggregate_validator_results([{"severity": "custom"}])

        expected_score = 100 - UNKNOWN_SEVERITY_WEIGHT
        self.assertEqual(aggregated["hygiene_score"], expected_score)
        self.assertEqual(aggregated["severity_counts"]["custom"], 1)
        self.assertEqual(
            aggregated["penalties"]["by_severity"]["custom"],
            UNKNOWN_SEVERITY_WEIGHT,
        )

    def test_multiple_critical_results_clamp_to_unsafe(self):
        aggregated = aggregate_validator_results(["critical"] * 5)

        self.assertEqual(aggregated["rating"], "unsafe")
        self.assertEqual(aggregated["hygiene_score"], 0)
        self.assertEqual(
            aggregated["summary"][0],
            "Critical issues detected",
        )


if __name__ == "__main__":
    unittest.main()
