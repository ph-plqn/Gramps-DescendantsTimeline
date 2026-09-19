import unittest
from datetime import date

from descendants_timeline.inference.temporal_estimate import (
    TemporalEstimate,
)
from descendants_timeline.model.temporal import CertaintyLevel


class TestTemporalEstimate(unittest.TestCase):

    def test_accepts_date_with_certainty(self):
        estimate = TemporalEstimate(
            representative_value=date(1821, 3, 12),
            certainty=CertaintyLevel.CERTAIN,
        )

        self.assertEqual(
            estimate.representative_value,
            date(1821, 3, 12),
        )
        self.assertEqual(
            estimate.certainty,
            CertaintyLevel.CERTAIN,
        )

    def test_accepts_none_with_undetermined_certainty(self):
        estimate = TemporalEstimate(
            representative_value=None,
            certainty=CertaintyLevel.UNDETERMINED,
        )

        self.assertIsNone(estimate.representative_value)
        self.assertEqual(
            estimate.certainty,
            CertaintyLevel.UNDETERMINED,
        )

    def test_rejects_invalid_representative_value_type(self):
        with self.assertRaises(TypeError):
            TemporalEstimate(
                representative_value="1821-03-12",
                certainty=CertaintyLevel.CERTAIN,
            )

    def test_rejects_certainty_when_representative_value_is_none(self):
        with self.assertRaises(ValueError):
            TemporalEstimate(
                representative_value=None,
                certainty=CertaintyLevel.PROBABLE,
            )

    def test_rejects_invalid_certainty_type(self):
        with self.assertRaises(TypeError):
            TemporalEstimate(
                representative_value=date(1821, 3, 12),
                certainty="CERTAIN",
            )

if __name__ == "__main__":
    unittest.main()