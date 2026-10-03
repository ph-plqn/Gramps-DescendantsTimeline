"""Tests du modèle TemporalTargetIndex."""

import unittest
from datetime import date

from descendants_timeline.model.temporal import (
    CertaintyLevel,
    EvidenceStatus,
    SourceQuality,
    TemporalValue,
    ValueOrigin,
)
from descendants_timeline.model.temporal_target import (
    TargetSemantic,
    TemporalOwnerType,
    TemporalTarget,
)
from descendants_timeline.model.temporal_target_entry import TemporalTargetEntry
from descendants_timeline.model.temporal_target_index import TemporalTargetIndex


class TestTemporalTargetIndex(unittest.TestCase):

    def _birth_target(self, person_id: str = "I001") -> TemporalTarget:
        return TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id=person_id,
            semantic=TargetSemantic.BIRTH,
        )

    def _death_target(self, person_id: str = "I001") -> TemporalTarget:
        return TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id=person_id,
            semantic=TargetSemantic.DEATH,
        )

    def _gramps_exact_value(self) -> TemporalValue:
        value = date(1812, 4, 5)

        return TemporalValue(
            source_value="5 avril 1812",
            source_calendar="GREGORIAN",
            normalized_minimum=value,
            normalized_maximum=value,
            representative_value=value,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

    def _entry(
        self,
        target: TemporalTarget,
        gramps_value: TemporalValue | None = None,
    ) -> TemporalTargetEntry:
        return TemporalTargetEntry(
            target=target,
            gramps_value=(
                gramps_value
                if gramps_value is not None
                else TemporalValue.unknown()
            ),
            anomalies=(),
        )

    def test_valid_index(self) -> None:
        birth_target = self._birth_target()
        death_target = self._death_target()

        birth_entry = self._entry(
            birth_target,
            self._gramps_exact_value(),
        )
        death_entry = self._entry(death_target)

        index = TemporalTargetIndex(
            entries={
                birth_target: birth_entry,
                death_target: death_entry,
            }
        )

        self.assertEqual(len(index.entries), 2)
        self.assertEqual(index.get(birth_target), birth_entry)
        self.assertEqual(index.get(death_target), death_entry)

    def test_empty_index_is_valid(self) -> None:
        index = TemporalTargetIndex(entries={})

        self.assertEqual(len(index.entries), 0)

    def test_entries_must_be_mapping(self) -> None:
        with self.assertRaises(TypeError):
            TemporalTargetIndex(
                entries=[],  # type: ignore[arg-type]
            )

    def test_entry_key_must_be_temporal_target(self) -> None:
        target = self._birth_target()
        entry = self._entry(target)

        with self.assertRaises(TypeError):
            TemporalTargetIndex(
                entries={
                    "I001/BIRTH": entry,  # type: ignore[dict-item]
                }
            )

    def test_entry_value_must_be_temporal_target_entry(self) -> None:
        target = self._birth_target()

        with self.assertRaises(TypeError):
            TemporalTargetIndex(
                entries={
                    target: "entry",  # type: ignore[dict-item]
                }
            )

    def test_key_must_match_entry_target(self) -> None:
        birth_target = self._birth_target()
        death_target = self._death_target()

        with self.assertRaises(ValueError):
            TemporalTargetIndex(
                entries={
                    birth_target: self._entry(death_target),
                }
            )

    def test_get_returns_none_for_absent_target(self) -> None:
        birth_target = self._birth_target()
        death_target = self._death_target()

        index = TemporalTargetIndex(
            entries={
                birth_target: self._entry(birth_target),
            }
        )

        self.assertIsNone(index.get(death_target))

    def test_get_requires_temporal_target(self) -> None:
        index = TemporalTargetIndex(entries={})

        with self.assertRaises(TypeError):
            index.get("I001/BIRTH")  # type: ignore[arg-type]

    def test_entries_are_immutable_snapshot(self) -> None:
        birth_target = self._birth_target()
        death_target = self._death_target()

        source = {
            birth_target: self._entry(birth_target),
        }

        index = TemporalTargetIndex(entries=source)

        # Modifier le dictionnaire d'origine ne modifie pas l'index.
        source[death_target] = self._entry(death_target)

        self.assertEqual(len(source), 2)
        self.assertEqual(len(index.entries), 1)
        self.assertIsNone(index.get(death_target))

        # Le mapping conservé par l'index n'est pas modifiable.
        with self.assertRaises(TypeError):
            index.entries[death_target] = self._entry(death_target)  # type: ignore[index]


if __name__ == "__main__":
    unittest.main()