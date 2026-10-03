# Gramps Descendants Timeline

## Model — Classes Métier Python
**Version :** 0.1  
**Statut :** Brouillon
**Document :** `04_Model.md`

---

# Table des matières

1. Objet et principes du document
2. Énumérations
   2.1 EventSemantic
   2.2 EventRoleSemantic
   2.3 FamilyRoleSemantic
   2.4 ValueOrigin
   2.5 EvidenceStatus
   2.6 CertaintyLevel
   2.7 SourceQuality
   2.8 ChildRelation
3. Classes fondamentales
   3.1 TemporalValue
   3.2 Event
   3.3 Person
   3.4 Family
4. Classes d'association
   4.1 PersonEventRef
   4.2 FamilyEventRef
   4.3 ChildRef
5. Conteneur du modèle
   5.1 RawGenealogyData
6. Invariants transversaux

---

# 1. Objet du document

Le présent document décrit les Classes définies dans le Projet

Il répond au besoin de structurer les données manipulées par le modèle en limitant les valeurs possibles d'un attribut. On distingue 4 types de classes :

1. Les énumérations

Elles définissent un ensemble fermé de valeurs reconnues par le greffon.
Elles servent à limiter les valeurs possibles de certains attributs.

2. Les classes métier

Elles représentent les concepts fondamentaux manipulés par le greffon.
Elles regroupent des données cohérentes et garantissent leurs invariants.

3. Les classes d'association

Elles représentent les relations entre les objets métier.

4. La classe du conteneur

Elle réunit et indexe les objets métier.

---

# 2. Énumérations

## 2.1.	EventSemantic

```python
class EventSemantic(Enum):
    """
    Signification d'un évènement reconnue par le greffon.

    Les types d'évènements Gramps sont ouverts et personnalisables.
    Cette énumération contient uniquement les significations nécessaires
    aux algorithmes du greffon.

    UNKNOWN ne signifie pas que l’évènement est inconnu ou mauvais. Il signifie seulement :
    Le greffon ne possède aucune interprétation algorithmique particulière de ce type d’évènement.
    """

    UNKNOWN = "UNKNOWN"
    BIRTH = "BIRTH"
    BAPTISM = "BAPTISM"
    MARRIAGE = "MARRIAGE"
    DIVORCE = "DIVORCE"
    DEATH = "DEATH"
    BURIAL = "BURIAL"
    ...
```

---

## 2.2.	EventRoleSemantic

```python
class EventRoleSemantic(Enum):
    """
    Signification d'un rôle reconnu par le greffon.

    Les types de rôles Gramps sont ouverts et personnalisables.
    Elle ne reproduit pas l'ensemble des rôles Gramps.
    Un rôle inconnu ou personnalisé est conservé dans source_role
    et reçoit la sémantique UNKNOWN.
    """
    	UNKNOWN = "UNKNOWN"
    	PRINCIPAL = "PRINCIPAL"
    	WITNESS = "WITNESS"
    	INFORMANT = "INFORMANT"
```

---

## 2.3.	FamilyRoleSemantic

```python
class FamilyRoleSemantic(Enum):
    """
    Signification d'un rôle reconnu par le greffon.

    Les types de rôles Gramps sont ouverts et personnalisables.
    Cette énumération contient uniquement les significations nécessaires
    aux algorithmes du greffon.
    """
    	UNKNOWN = "UNKNOWN"
    	FAMILY = "FAMILY"
```

---

## 2.4.	ValueOrigin

```python
class ValueOrigin(str, Enum):
    """Origine de la valeur temporelle elle-même."""

    GRAMPS = "GRAMPS"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"
```

---

## 2.5.	EvidenceStatus

```python
class EvidenceStatus(str, Enum):
    """Admissibilité de la valeur comme preuve directe."""

    EVIDENCE_USABLE = "EVIDENCE_USABLE"
    EVIDENCE_UNPROVEN = "EVIDENCE_UNPROVEN"
    EVIDENCE_UNAVAILABLE = "EVIDENCE_UNAVAILABLE"
```

---

## 2.6.	CertaintyLevel

```python
class CertaintyLevel(str, Enum):
    """Niveau qualitatif de certitude, et non probabilité statistique."""

    CERTAIN = "CERTAIN"
    VERY_PROBABLE = "VERY_PROBABLE"
    PROBABLE = "PROBABLE"
    POSSIBLE = "POSSIBLE"
    UNDETERMINED = "UNDETERMINED"
```

---

## 2.7.	SourceQuality

```python
class SourceQuality(str, Enum):
    """Qualité de la source elle-même."""

    NORMAL = "NORMAL"
    CALCULATED = "CALCULATED"
    ESTIMATED = "ESTIMATED"
```

---

## 2.8.	ChildRelation

```python
class ChildRelation(str, Enum):
    """Relation d'un enfant avec un parent, normalisée depuis Gramps."""

    ADOPTED = "ADOPTED"
    NONE = "NONE"
    FOSTER = "FOSTER"
    STEPCHILD = "STEPCHILD"
    UNKNOWN = "UNKNOWN"
    BIRTH = "BIRTH"
    SPONSORED = "SPONSORED"
```

---

# 3. Classes fondamentales

## 3.1. TemporalValue

```python
@dataclass(frozen=True, slots=True)
class TemporalValue:
    """Information temporelle documentée, inférée ou inconnue.

    ``source_value`` conserve la formulation documentaire issue de Gramps.
    ``normalized_minimum`` et ``normalized_maximum`` sont les bornes
    converties dans le référentiel grégorien commun.

    ``representative_value`` est la valeur représentative retenue dans l'intervalle
    normalisé. Elle doit être temporellement justifiée. Elle ne doit pas
    être confondue avec une future ``display_value`` produite uniquement par
    le ``LayoutEngine``.

    Purpose
    -------
    Représente une valeur temporelle utilisée par le moteur d'inférence.

    Responsibilities
    ----------------
    - conserver la valeur documentaire ;
    - conserver la valeur normalisée ;
    - garantir les invariants.

    Does NOT
    --------
    - effectuer des inférences ;
    - calculer une display_value ;
    - dessiner quoi que ce soit.

    See also
    --------
    Specifications : E006,E007,C008,C009
    Architecture   : A005,§14.2
    Algorithms     : §24
    """

    source_value: str | None
    source_calendar: str | None
    normalized_minimum: date | None
    normalized_maximum: date | None
    representative_value: date | None
    value_origin: ValueOrigin
    source_quality: SourceQuality
    evidence_status: EvidenceStatus
    certainty: CertaintyLevel

    def __post_init__(self) -> None:
        minimum = self.normalized_minimum
        maximum = self.normalized_maximum
        representative = self.representative_value

        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValueError(
                "normalized_minimum ne peut pas être postérieur "
                "à normalized_maximum."
            )

        if representative is not None:
            if minimum is not None and representative < minimum:
                raise ValueError(
                    "representative_value ne peut pas précéder "
                    "normalized_minimum."
                )
            if maximum is not None and representative > maximum:
                raise ValueError(
                    "representative_value ne peut pas suivre "
                    "normalized_maximum."
                )

        if self.value_origin is ValueOrigin.GRAMPS and self.source_value is None:
            raise ValueError(
                "Une valeur d'origine GRAMPS doit conserver source_value."
            )

        if self.value_origin is ValueOrigin.INFERRED and self.source_value is not None:
            raise ValueError(
                "Une valeur INFERRED ne doit pas prétendre provenir "
                "directement d'une source Gramps."
            )

        if self.value_origin is ValueOrigin.UNKNOWN:
            if any(
                value is not None
                for value in (
                    self.source_value,
                    self.source_calendar,
                    self.normalized_minimum,
                    self.normalized_maximum,
                    self.representative_value,
                )
            ):
                raise ValueError(
                    "Une valeur UNKNOWN ne doit contenir aucune valeur temporelle."
                )
            if self.evidence_status is not EvidenceStatus.EVIDENCE_UNAVAILABLE:
                raise ValueError(
                    "Une valeur UNKNOWN doit avoir "
                    "evidence_status=EVIDENCE_UNAVAILABLE."
                )

        if self.evidence_status is EvidenceStatus.EVIDENCE_UNAVAILABLE:
            if any(
                value is not None
                for value in (
                    self.normalized_minimum,
                    self.normalized_maximum,
                    self.representative_value,
                )
            ):
                raise ValueError(
                    "EVIDENCE_UNAVAILABLE est incompatible avec des bornes "
                    "ou une valeur représentative."
                )

        if self.evidence_status is EvidenceStatus.EVIDENCE_USABLE:
            if (
                self.normalized_minimum is None
                and self.normalized_maximum is None
                and self.representative_value is None
            ):
                raise ValueError(
                    "Une preuve utilisable doit fournir au moins une information "
                    "temporelle normalisée."
                )
        if (
            self.source_quality is Source.Quality.CALCULATED
            and self.evidence_status is EvidenceStatus.EVIDENCE_USABLE
            ):
                raise ValueError(
                    "Une date CALCULATED ne peut pas être utilisée comme preuve directe."
                )

    @property
    def has_closed_interval(self) -> bool:
        return (
            self.normalized_minimum is not None
            and self.normalized_maximum is not None
        )

    @property
    def is_exact(self) -> bool:
        return (
            self.has_closed_interval
            and self.normalized_minimum == self.normalized_maximum
        )

    @property
    def is_usable_as_evidence(self) -> bool:
        return self.evidence_status is EvidenceStatus.EVIDENCE_USABLE

    @classmethod
    def unknown(cls) -> "TemporalValue":
        return cls(
            source_value=None,
            source_calendar=None,
            normalized_minimum=None,
            normalized_maximum=None,
            representative_value=None,
            value_origin=ValueOrigin.UNKNOWN,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_UNAVAILABLE,
            certainty=CertaintyLevel.UNDETERMINED,
        )
```

---

## 3.2.	Event

```python
@dataclass(frozen=True, slots=True)
class Event:
    """
    Purpose
    -------
    Représente un évènement généalogique extrait des données sources.

    Responsibilities
    ----------------
    - identifier l'évènement ;
    - conserver son type documentaire ;
    - exposer la signification reconnue par le greffon ;
    - conserver sa valeur temporelle ;
    - garantir ses invariants.

    Does NOT
    --------
    - connaître les personnes ou les familles associées ;
    - conserver le rôle d'une personne dans l'évènement ;
    - accéder à Gramps ;
    - effectuer une inférence temporelle ;
    - convertir les calendriers ;
    - conserver ou interpréter un lieu ;
    - déterminer une position sur la timeline.
    """

    event_id: str
    source_type: str
    semantic: EventSemantic
    date: TemporalValue

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise ValueError("event_id must be a non-empty string")

        if not isinstance(self.source_type, str) or not self.source_type.strip():
            raise ValueError("source_type must be a non-empty string")

        if not isinstance(self.semantic, EventSemantic):
            raise TypeError("semantic must be an EventSemantic")

        if not isinstance(self.date, TemporalValue):
            raise TypeError("date must be a TemporalValue")
```

---

## 3.3.	Person

Cette classe sera définie dans une version ultérieure.

---

## 3.4.	Family

Cette classe sera définie dans une version ultérieure.

---

# 4. Classes d'association

## 4.1.	PersonEventRef

```python
@dataclass(frozen=True, slots=True)
class PersonEventRef:
    """
    Décrit la participation d'une personne à un évènement.
    """

    event_id: str
    semantic_role: EventRoleSemantic
    source_role: str

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise ValueError("event_id must be a non-empty string")

        if not isinstance(self.semantic_role, EventRoleSemantic):
            raise TypeError(
                "semantic_role must be an EventRoleSemantic"
            )

        if not isinstance(self.source_role, str) or not self.source_role.strip():
            raise ValueError("source_role must be a non-empty string")
```

---

## 4.2.	FamilyEventRef

```python
@dataclass(frozen=True, slots=True)
class FamilyEventRef:
    """
    Décrit le rattachement d’une famille à l’évènement.
    """

    event_id: str
    semantic_role: FamilyRoleSemantic
    source_role: str

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise ValueError("event_id must be a non-empty string")

        if not isinstance(self.semantic_role, FamilyRoleSemantic):
            raise TypeError(
                "semantic_role must be an FamilyRoleSemantic"
            )

        if not isinstance(self.source_role, str) or not self.source_role.strip():
            raise ValueError("source_role must be a non-empty string")
```

---

## 4.3.	ChildRef

```python
@dataclass(frozen=True, slots=True)
class ChildRef:
    """Décrit la relation d'un enfant avec les deux parents d'une famille.

    Responsibilities
    ----------------
    - référencer une personne existante ;
    - conserver séparément la relation avec parent1 ;
    - conserver séparément la relation avec parent2 ;
    - garantir ses invariants.

    Does NOT
    --------
    - contenir l'objet Person lui-même ;
    - décider si l'enfant appartient au DFS ;
    - interpréter ou corriger les relations saisies dans Gramps ;
    - accéder à Gramps ;
    - modifier la personne ou la famille référencée.
    """

    person_id: str
    relation_to_parent1: ChildRelation
    relation_to_parent2: ChildRelation

    def __post_init__(self) -> None:
        if not isinstance(self.person_id, str) or not self.person_id.strip():
            raise ValueError("person_id must be a non-empty string")

        if not isinstance(self.relation_to_parent1, ChildRelation):
            raise TypeError("relation_to_parent1 must be a ChildRelation")

        if not isinstance(self.relation_to_parent2, ChildRelation):
            raise TypeError("relation_to_parent2 must be a ChildRelation")
```

---

# 5. Conteneur

# 5.1. RawGenealogyData

```python
@dataclass(frozen=True, slots=True)
class RawGenealogyData:
    """Photographie immuable du sous-ensemble généalogique utile.
    
Responsibilities
    ----------------
    créer des dictionnaires dont les clés sont
    - person_id
    - family_id
    - event_id

RawGenealogyData
│
├── persons
│   ├── "I0707" → Person(...)
│   ├── "I0712" → Person(...)
│   └── "I0720" → Person(...)
│
├── families
│   ├── "F0088" → Family(...)
│   └── "F0095" → Family(...)
│
└── events
    ├── "E0123" → Event(...)
    └── "E0147" → Event(...)


    Does NOT
    --------
    - modifier des données ;
    - construire un DFS ;
    - accéder à Gramps ;
    - modifier la personne ou la famille référencée.
"""

    persons: Mapping[str, Person]
    families: Mapping[str, Family]
    events: Mapping[str, Event]
    root_person_id: str

    def __post_init__(self) -> None:
        persons = self._copy_persons(self.persons)
        families = self._copy_families(self.families)
        events = self._copy_events(self.events)

        if not isinstance(self.root_person_id, str) or not self.root_person_id.strip():
            raise ValueError("root_person_id must be a non-empty string")

        if self.root_person_id not in persons:
            raise ValueError("root_person_id must reference a person present in persons")

        self._validate_person_references(persons, families, events)
        self._validate_family_references(persons, families, events)

        object.__setattr__(self, "persons", MappingProxyType(persons))
        object.__setattr__(self, "families", MappingProxyType(families))
        object.__setattr__(self, "events", MappingProxyType(events))

    @staticmethod
    def _copy_persons(values: Mapping[str, Person]) -> dict[str, Person]:
        if not isinstance(values, Mapping):
            raise TypeError("persons must be a mapping")
        copied = dict(values)
        for key, person in copied.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("persons keys must be non-empty strings")
            if not isinstance(person, Person):
                raise TypeError("persons must contain only Person objects")
            if key != person.person_id:
                raise ValueError("persons key must match Person.person_id")
        return copied

    @staticmethod
    def _copy_families(values: Mapping[str, Family]) -> dict[str, Family]:
        if not isinstance(values, Mapping):
            raise TypeError("families must be a mapping")
        copied = dict(values)
        for key, family in copied.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("families keys must be non-empty strings")
            if not isinstance(family, Family):
                raise TypeError("families must contain only Family objects")
            if key != family.family_id:
                raise ValueError("families key must match Family.family_id")
        return copied

    @staticmethod
    def _copy_events(values: Mapping[str, Event]) -> dict[str, Event]:
        if not isinstance(values, Mapping):
            raise TypeError("events must be a mapping")
        copied = dict(values)
        for key, event in copied.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("events keys must be non-empty strings")
            if not isinstance(event, Event):
                raise TypeError("events must contain only Event objects")
            if key != event.event_id:
                raise ValueError("events key must match Event.event_id")
        return copied

    @staticmethod
    def _validate_person_references(
        persons: Mapping[str, Person],
        families: Mapping[str, Family],
        events: Mapping[str, Event],
    ) -> None:
        for person in persons.values():
            for ref in person.event_refs:
                if ref.event_id not in events:
                    raise ValueError(
                        f"Person {person.person_id} references missing event {ref.event_id}"
                    )
            for family_id in person.parent_family_ids:
                if family_id not in families:
                    raise ValueError(
                        f"Person {person.person_id} references missing parent family {family_id}"
                    )
            for family_id in person.family_ids:
                if family_id not in families:
                    raise ValueError(
                        f"Person {person.person_id} references missing family {family_id}"
                    )

    @staticmethod
    def _validate_family_references(
        persons: Mapping[str, Person],
        families: Mapping[str, Family],
        events: Mapping[str, Event],
    ) -> None:
        for family in families.values():
            if family.parent1_id is not None and family.parent1_id not in persons:
                raise ValueError(
                    f"Family {family.family_id} references missing parent1 {family.parent1_id}"
                )
            if family.parent2_id is not None and family.parent2_id not in persons:
                raise ValueError(
                    f"Family {family.family_id} references missing parent2 {family.parent2_id}"
                )
            for ref in family.event_refs:
                if ref.event_id not in events:
                    raise ValueError(
                        f"Family {family.family_id} references missing event {ref.event_id}"
                    )
            for child_ref in family.child_refs:
                if child_ref.person_id not in persons:
                    raise ValueError(
                        f"Family {family.family_id} references missing child {child_ref.person_id}"
                    )
```

---

# 6. Invariants transversaux

- les identifiants sont obligatoires et non vides ;
- les objets sont immuables ;
- les collections ordonnées sont des tuples ;
- toutes les collections dont l’ordre est défini par Gramps sont conservées dans
  cet ordre par le modèle. Le greffon ne trie, ne réordonne et ne renumérote pas
  implicitement ces données. Une incohérence temporelle entre l’ordre Gramps et
  les dates des éléments est conservée et peut être signalée par un diagnostic,
  mais elle n’est jamais corrigée automatiquement.
- aucune classe du modèle n'accède directement à Gramps ;
- les références doivent désigner un objet présent dans RawGenealogyData ;
- les types et rôles documentaires Gramps restent ouverts ;
- les sémantiques du greffon sont fermées.
- toutes les dates manipulées par le modèle sont normalisées
  en calendrier grégorien avant d'être stockées.
- Les objets du modèle ne se modifient jamais après leur création.
  Toute modification produit un nouvel objet.
- Le modèle conserve séparément la relation de l’enfant avec chacun des deux
  parents. Le DFS biologique inclut uniquement Naissance. Le DFS étendu inclut
  Naissance, Adopté et Parrainé. Les autres relations sont conservées mais
  exclues du parcours.
- Cas particulier de ChildRelation.UNKNOWN : Dans ChildRelation, UNKNOWN représente
  une information généalogique explicite provenant de Gramps : la relation de l'enfant
  avec le parent est déclarée inconnue. Cette valeur ne doit pas être assimilée au
  mécanisme UNKNOWN utilisé dans certaines autres énumérations pour représenter une
  valeur non interprétée par le greffon.

---





 