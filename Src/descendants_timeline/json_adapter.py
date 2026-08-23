"""Adaptateur de test pour les exports JSON de Gramps.

Important
---------
L'export JSON de Gramps utilisé ici est un fichier JSON Lines (NDJSON) :
chaque ligne contient un objet JSON complet (Event, Person ou Family).
Ce module ne dépend pas de l'API interne de Gramps.

Son rôle est uniquement de traduire un export Gramps vers le modèle
normalisé du greffon, afin de permettre des tests d'intégration réalistes.

Ce module est provisoire : le futur ``GrampsDataAdapter`` lira directement
les objets Gramps en mémoire.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from descendants_timeline.model.child_ref import ChildRef, ChildRelation
from descendants_timeline.model.event import Event, EventSemantic
from descendants_timeline.model.family import Family
from descendants_timeline.model.family_event_ref import (
    FamilyEventRef,
    FamilyRoleSemantic,
)
from descendants_timeline.model.genealogy import RawGenealogyData
from descendants_timeline.model.person import Person, PersonGender
from descendants_timeline.model.person_event_ref import (
    EventRoleSemantic,
    PersonEventRef,
)
from descendants_timeline.model.temporal import (
    CertaintyLevel,
    EvidenceStatus,
    SourceQuality,
    TemporalValue,
    ValueOrigin,
)


class JsonGrampsAdapter:
    """Traduit un export JSON Gramps en ``RawGenealogyData``."""

    EVENT_SEMANTICS = {
        1: EventSemantic.MARRIAGE,
        7: EventSemantic.DIVORCE,
        12: EventSemantic.BIRTH,
        13: EventSemantic.DEATH,
        15: EventSemantic.BAPTISM,
        19: EventSemantic.BURIAL,
    }

    EVENT_TYPE_LABELS = {
        1: "Marriage",
        7: "Divorce",
        12: "Birth",
        13: "Death",
        15: "Baptism",
        19: "Burial",
    }

    PERSON_EVENT_ROLES = {
        1: EventRoleSemantic.PRINCIPAL,
        7: EventRoleSemantic.WITNESS,
        9: EventRoleSemantic.INFORMANT,
    }

    EVENT_ROLE_LABELS = {
        1: "Principal",
        7: "Witness",
        8: "Family",
        9: "Informant",
    }

    CHILD_RELATIONS = {
        0: ChildRelation.NONE,
        1: ChildRelation.BIRTH,
        2: ChildRelation.ADOPTED,
        3: ChildRelation.STEPCHILD,
        4: ChildRelation.SPONSORED,
        5: ChildRelation.FOSTER,
        6: ChildRelation.UNKNOWN,
    }

    GENDERS = {
        0: PersonGender.FEMALE,
        1: PersonGender.MALE,
        2: PersonGender.UNKNOWN,
        3: PersonGender.OTHER,
    }

    CALENDAR_LABELS = {
        0: "Gregorian",
        1: "Julian",
        2: "Hebrew",
        3: "French Republican",
        4: "Persian",
        5: "Islamic",
        6: "Swedish",
    }

    SOURCE_QUALITIES = {
        0: SourceQuality.NORMAL,
        1: SourceQuality.ESTIMATED,
        2: SourceQuality.CALCULATED,
    }

    def load(
        self,
        path: str | Path,
        root_person_id: str,
    ) -> RawGenealogyData:
        """Charge un export JSON Gramps et construit ``RawGenealogyData``."""

        records = list(self._iter_records(path))

        person_records = [
            record for record in records if record.get("_class") == "Person"
        ]
        family_records = [
            record for record in records if record.get("_class") == "Family"
        ]
        event_records = [
            record for record in records if record.get("_class") == "Event"
        ]

        person_handle_to_id = self._build_handle_index(
            person_records,
            expected_prefix="I",
            object_name="Person",
        )
        family_handle_to_id = self._build_handle_index(
            family_records,
            expected_prefix="F",
            object_name="Family",
        )
        event_handle_to_id = self._build_handle_index(
            event_records,
            expected_prefix="E",
            object_name="Event",
        )

        events = {
            event["gramps_id"]: self._convert_event(event)
            for event in event_records
        }

        persons = {
            person["gramps_id"]: self._convert_person(
                person,
                family_handle_to_id=family_handle_to_id,
                event_handle_to_id=event_handle_to_id,
            )
            for person in person_records
        }

        families = {
            family["gramps_id"]: self._convert_family(
                family,
                person_handle_to_id=person_handle_to_id,
                event_handle_to_id=event_handle_to_id,
            )
            for family in family_records
        }

        return RawGenealogyData(
            persons=persons,
            families=families,
            events=events,
            root_person_id=root_person_id,
        )

    @staticmethod
    def _iter_records(path: str | Path) -> Iterable[dict[str, Any]]:
        """Lit le JSON Gramps ligne par ligne.

        Cela évite de charger tout le texte du fichier en une seule chaîne,
        même si les objets normalisés seront ensuite conservés en mémoire.
        """

        file_path = Path(path)

        if not file_path.is_file():
            raise FileNotFoundError(file_path)

        with file_path.open("r", encoding="utf-8-sig") as stream:
            for line_number, raw_line in enumerate(stream, start=1):
                line = raw_line.strip()

                if not line:
                    continue

                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Invalid Gramps JSON on line {line_number}: {exc.msg}"
                    ) from exc

                if not isinstance(value, dict):
                    raise TypeError(
                        f"Gramps JSON line {line_number} must contain an object"
                    )

                yield value

    @staticmethod
    def _build_handle_index(
        records: list[dict[str, Any]],
        expected_prefix: str,
        object_name: str,
    ) -> dict[str, str]:
        """Construit l'index temporaire ``handle -> gramps_id``."""

        index: dict[str, str] = {}

        for record in records:
            handle = record.get("handle")
            gramps_id = record.get("gramps_id")

            if not isinstance(handle, str) or not handle:
                raise ValueError(f"{object_name} without a valid handle")

            if not isinstance(gramps_id, str) or not gramps_id:
                raise ValueError(f"{object_name} without a valid gramps_id")

            if not gramps_id.startswith(expected_prefix):
                raise ValueError(
                    f"Unexpected {object_name} gramps_id: {gramps_id}"
                )

            if handle in index:
                raise ValueError(f"Duplicate Gramps handle: {handle}")

            index[handle] = gramps_id

        return index

    def _convert_person(
        self,
        record: dict[str, Any],
        *,
        family_handle_to_id: dict[str, str],
        event_handle_to_id: dict[str, str],
    ) -> Person:
        person_id = self._required_string(record, "gramps_id", "Person")

        gender_code = record.get("gender")
        try:
            gender = self.GENDERS[gender_code]
        except KeyError as exc:
            raise ValueError(
                f"Person {person_id}: unsupported gender code {gender_code!r}"
            ) from exc

        event_refs = tuple(
            self._convert_person_event_ref(
                ref,
                person_id=person_id,
                event_handle_to_id=event_handle_to_id,
            )
            for ref in record.get("event_ref_list", [])
        )

        parent_family_ids = tuple(
            self._resolve_handle(
                family_handle_to_id,
                handle,
                context=f"Person {person_id} parent family",
            )
            for handle in record.get("parent_family_list", [])
        )

        family_ids = tuple(
            self._resolve_handle(
                family_handle_to_id,
                handle,
                context=f"Person {person_id} family",
            )
            for handle in record.get("family_list", [])
        )

        return Person(
            person_id=person_id,
            display_name=self._display_name(record, fallback=person_id),
            gender=gender,
            event_refs=event_refs,
            parent_family_ids=parent_family_ids,
            family_ids=family_ids,
        )

    def _convert_family(
        self,
        record: dict[str, Any],
        *,
        person_handle_to_id: dict[str, str],
        event_handle_to_id: dict[str, str],
    ) -> Family:
        family_id = self._required_string(record, "gramps_id", "Family")

        father_handle = record.get("father_handle")
        mother_handle = record.get("mother_handle")

        parent1_id = (
            self._resolve_handle(
                person_handle_to_id,
                father_handle,
                context=f"Family {family_id} parent1",
            )
            if father_handle
            else None
        )

        parent2_id = (
            self._resolve_handle(
                person_handle_to_id,
                mother_handle,
                context=f"Family {family_id} parent2",
            )
            if mother_handle
            else None
        )

        event_refs = tuple(
            self._convert_family_event_ref(
                ref,
                family_id=family_id,
                event_handle_to_id=event_handle_to_id,
            )
            for ref in record.get("event_ref_list", [])
        )

        child_refs = tuple(
            self._convert_child_ref(
                ref,
                family_id=family_id,
                person_handle_to_id=person_handle_to_id,
            )
            for ref in record.get("child_ref_list", [])
        )

        return Family(
            family_id=family_id,
            parent1_id=parent1_id,
            parent2_id=parent2_id,
            event_refs=event_refs,
            child_refs=child_refs,
        )

    def _convert_event(self, record: dict[str, Any]) -> Event:
        event_id = self._required_string(record, "gramps_id", "Event")

        type_data = record.get("type")
        if not isinstance(type_data, dict):
            raise ValueError(f"Event {event_id}: missing type")

        type_code = type_data.get("value")
        custom_label = type_data.get("string", "")

        semantic = self.EVENT_SEMANTICS.get(
            type_code,
            EventSemantic.UNKNOWN,
        )

        if isinstance(custom_label, str) and custom_label.strip():
            source_type = custom_label.strip()
        else:
            source_type = self.EVENT_TYPE_LABELS.get(
                type_code,
                f"EventType({type_code})",
            )

        return Event(
            event_id=event_id,
            source_type=source_type,
            semantic=semantic,
            date=self._convert_date(record.get("date"), event_id=event_id),
        )

    def _convert_person_event_ref(
        self,
        ref: dict[str, Any],
        *,
        person_id: str,
        event_handle_to_id: dict[str, str],
    ) -> PersonEventRef:
        event_id = self._resolve_handle(
            event_handle_to_id,
            ref.get("ref"),
            context=f"Person {person_id} event",
        )

        role = ref.get("role")
        if not isinstance(role, dict):
            raise ValueError(f"Person {person_id}: event reference without role")

        role_code = role.get("value")
        custom_role = role.get("string", "")

        semantic_role = self.PERSON_EVENT_ROLES.get(
            role_code,
            EventRoleSemantic.UNKNOWN,
        )

        source_role = self._source_role_label(role_code, custom_role)

        return PersonEventRef(
            event_id=event_id,
            semantic_role=semantic_role,
            source_role=source_role,
        )

    def _convert_family_event_ref(
        self,
        ref: dict[str, Any],
        *,
        family_id: str,
        event_handle_to_id: dict[str, str],
    ) -> FamilyEventRef:
        event_id = self._resolve_handle(
            event_handle_to_id,
            ref.get("ref"),
            context=f"Family {family_id} event",
        )

        role = ref.get("role")
        if not isinstance(role, dict):
            raise ValueError(f"Family {family_id}: event reference without role")

        role_code = role.get("value")
        custom_role = role.get("string", "")

        semantic_role = (
            FamilyRoleSemantic.FAMILY
            if role_code == 8
            else FamilyRoleSemantic.UNKNOWN
        )

        return FamilyEventRef(
            event_id=event_id,
            semantic_role=semantic_role,
            source_role=self._source_role_label(role_code, custom_role),
        )

    def _convert_child_ref(
        self,
        ref: dict[str, Any],
        *,
        family_id: str,
        person_handle_to_id: dict[str, str],
    ) -> ChildRef:
        person_id = self._resolve_handle(
            person_handle_to_id,
            ref.get("ref"),
            context=f"Family {family_id} child",
        )

        return ChildRef(
            person_id=person_id,
            relation_to_parent1=self._convert_child_relation(
                ref.get("frel"),
                context=f"Family {family_id} child {person_id} parent1",
            ),
            relation_to_parent2=self._convert_child_relation(
                ref.get("mrel"),
                context=f"Family {family_id} child {person_id} parent2",
            ),
        )

    def _convert_child_relation(
        self,
        value: Any,
        *,
        context: str,
    ) -> ChildRelation:
        if not isinstance(value, dict):
            raise ValueError(f"{context}: missing ChildRef relation")

        code = value.get("value")

        if code == 7:
            # UNKNOWN est une vraie valeur métier dans ChildRelation :
            # on ne peut donc pas l'utiliser comme repli pour CUSTOM.
            custom_member = getattr(ChildRelation, "CUSTOM", None)
            if custom_member is None:
                raise ValueError(
                    f"{context}: custom ChildRef relation encountered, "
                    "but ChildRelation.CUSTOM is not yet defined"
                )
            return custom_member

        try:
            return self.CHILD_RELATIONS[code]
        except KeyError as exc:
            raise ValueError(
                f"{context}: unsupported ChildRef relation code {code!r}"
            ) from exc

    def _convert_date(
        self,
        value: Any,
        *,
        event_id: str,
    ) -> TemporalValue:
        if not isinstance(value, dict):
            return TemporalValue.unknown()

        dateval = value.get("dateval")
        if not isinstance(dateval, list) or len(dateval) < 3:
            return TemporalValue.unknown()

        day, month, year = dateval[:3]

        if not any((day, month, year)) and not value.get("text"):
            return TemporalValue.unknown()

        calendar_code = value.get("calendar", 0)
        modifier = value.get("modifier", 0)
        quality_code = value.get("quality", 0)

        try:
            source_quality = self.SOURCE_QUALITIES[quality_code]
        except KeyError as exc:
            raise ValueError(
                f"Event {event_id}: unsupported date quality code {quality_code!r}"
            ) from exc

        source_calendar = self.CALENDAR_LABELS.get(
            calendar_code,
            f"Calendar({calendar_code})",
        )
        source_value = self._source_date_value(
            day=day,
            month=month,
            year=year,
            text=value.get("text", ""),
            modifier=modifier,
        )

        # Première version volontairement conservatrice :
        # seules les dates normales, complètes et grégoriennes sont
        # normalisées. Les autres restent présentes comme valeurs Gramps,
        # mais ne sont pas encore utilisables comme preuve temporelle
        # normalisée. Elles seront prises en charge progressivement.
        can_normalize_exactly = (
            calendar_code == 0
            and modifier == 0
            and isinstance(day, int)
            and isinstance(month, int)
            and isinstance(year, int)
            and day > 0
            and month > 0
            and year > 0
        )

        normalized_value: date | None = None
        if can_normalize_exactly:
            try:
                normalized_value = date(year, month, day)
            except ValueError as exc:
                raise ValueError(
                    f"Event {event_id}: invalid Gregorian date "
                    f"{day:02d}/{month:02d}/{year}"
                ) from exc

        if normalized_value is None:
            return TemporalValue(
                source_value=source_value,
                source_calendar=source_calendar,
                normalized_minimum=None,
                normalized_maximum=None,
                representative_value=None,
                value_origin=ValueOrigin.GRAMPS,
                source_quality=source_quality,
                evidence_status=EvidenceStatus.EVIDENCE_UNAVAILABLE,
                certainty=CertaintyLevel.UNDETERMINED,
            )

        if source_quality is SourceQuality.NORMAL:
            evidence_status = EvidenceStatus.EVIDENCE_USABLE
            certainty = CertaintyLevel.CERTAIN
        else:
            # ESTIMATED et CALCULATED restent volontairement non prouvées
            # dans cette première version de l'adaptateur.
            evidence_status = EvidenceStatus.EVIDENCE_UNPROVEN
            certainty = CertaintyLevel.UNDETERMINED

        return TemporalValue(
            source_value=source_value,
            source_calendar=source_calendar,
            normalized_minimum=normalized_value,
            normalized_maximum=normalized_value,
            representative_value=normalized_value,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=source_quality,
            evidence_status=evidence_status,
            certainty=certainty,
        )

    @staticmethod
    def _source_date_value(
        *,
        day: Any,
        month: Any,
        year: Any,
        text: Any,
        modifier: Any,
    ) -> str:
        if isinstance(text, str) and text.strip():
            return text.strip()

        raw = f"{day!s}/{month!s}/{year!s}"

        modifier_labels = {
            0: "",
            1: "BEFORE ",
            2: "AFTER ",
            3: "ABOUT ",
            4: "RANGE ",
            5: "SPAN ",
            6: "TEXTONLY ",
            7: "FROM ",
            8: "TO ",
        }

        return f"{modifier_labels.get(modifier, f'MODIFIER({modifier}) ')}{raw}"

    @staticmethod
    def _display_name(record: dict[str, Any], *, fallback: str) -> str:
        name = record.get("primary_name")
        if not isinstance(name, dict):
            return fallback

        first_name = name.get("first_name", "")
        if not isinstance(first_name, str):
            first_name = ""

        surnames: list[str] = []
        for item in name.get("surname_list", []):
            if not isinstance(item, dict):
                continue
            surname = item.get("surname", "")
            if isinstance(surname, str) and surname.strip():
                surnames.append(surname.strip())

        parts = [part for part in [first_name.strip(), " ".join(surnames)] if part]
        return " ".join(parts) if parts else fallback

    @classmethod
    def _source_role_label(cls, code: Any, custom_role: Any) -> str:
        if isinstance(custom_role, str) and custom_role.strip():
            return custom_role.strip()

        return cls.EVENT_ROLE_LABELS.get(code, f"EventRole({code})")

    @staticmethod
    def _resolve_handle(
        index: dict[str, str],
        handle: Any,
        *,
        context: str,
    ) -> str:
        if not isinstance(handle, str) or not handle:
            raise ValueError(f"{context}: missing handle")

        try:
            return index[handle]
        except KeyError as exc:
            raise ValueError(
                f"{context}: unresolved Gramps handle {handle}"
            ) from exc

    @staticmethod
    def _required_string(
        record: dict[str, Any],
        key: str,
        object_name: str,
    ) -> str:
        value = record.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{object_name}: missing {key}")
        return value.strip()
