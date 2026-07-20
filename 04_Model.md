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
   2.3 FamilyRoleSemantic - à confirmer
   2.4 ValueOrigin
   2.5 EvidenceStatus
   2.6 CertaintyLevel
3. Classes fondamentales
   3.1 TemporalValue
   3.2 Event
   3.3 Person
   3.4 Family
4. Classes d'association
   4.1 PersonEventRef
   4.2 FamilyEventRef
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

## 2.3.	FamilyRoleSemantic - A confirmer

La nécessité d’une sémantique spécifique pour les rôles portés par
les références d’évènements de famille devra être vérifiée lors de
l’étude du GrampsDataAdapter.

```python
class FamilyRoleSemantic(Enum):
    """
    Signification d'un rôle reconnu par le greffon.

    Les types de rôles Gramps sont ouverts et personnalisables.
    Cette énumération contient uniquement les significations nécessaires
    aux algorithmes du greffon.
    Cette énumération est proposée à titre provisoire et pourra être supprimée
    si le modèle Gramps ne justifie pas son existence.
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
    source_quality: str | None
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
  	    self.source_quality == "CALCULATED"
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
            source_quality=None,
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

# 5. Conteneur

# 5.1. RawGenealogyData

---

# 6. Invariants transversaux

- les identifiants sont obligatoires et non vides ;
- les objets sont immuables ;
- les collections ordonnées sont des tuples ;
- aucune classe du modèle n'accède directement à Gramps ;
- les références doivent désigner un objet présent dans RawGenealogyData ;
- les types et rôles documentaires Gramps restent ouverts ;
- les sémantiques du greffon sont fermées.
- toutes les dates manipulées par le modèle sont normalisées
  en calendrier grégorien avant d'être stockées.
- Les objets du modèle ne se modifient jamais après leur création.
  Toute modification produit un nouvel objet.

---





 