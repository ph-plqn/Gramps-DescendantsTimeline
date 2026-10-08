from __future__ import annotations

import unittest

from descendants_timeline.layout.diagnostic_placement import (
    DiagnosticPlacement,
)
from descendants_timeline.model.temporal_target import (
    TargetSemantic,
    TemporalOwnerType,
    TemporalTarget,
)


class DiagnosticPlacementTests(unittest.TestCase):
    def test_diagnostic_placement_preserves_target_and_coordinates(self) -> None:
        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I1",
            semantic=TargetSemantic.BIRTH,
        )

        placement = DiagnosticPlacement(
            target=target,
            x=100.0,
            y=20.0,
        )

        self.assertEqual(placement.target, target)
        self.assertEqual(placement.x, 100.0)
        self.assertEqual(placement.y, 20.0)


if __name__ == "__main__":
    unittest.main()
