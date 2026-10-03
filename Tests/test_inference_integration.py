import unittest
from datetime import date

from descendants_timeline.inference.birth_before_death_rule import (
    BirthBeforeDeathRule,
)
from descendants_timeline.inference.baptism_before_death_rule import (
    BaptismBeforeDeathRule,
)
from descendants_timeline.inference.marriage_before_death_rule import (
    MarriageBeforeDeathRule,
)
from descendants_timeline.inference.rule_engine import RuleEngine
from descendants_timeline.inference.rule_context import RuleContext
from descendants_timeline.inference.constraint_resolver import (
    ConstraintResolver,
)

from descendants_timeline.model.event import EventSemantic
from descendants_timeline.model.family import Family
from descendants_timeline.model.family_event_ref import FamilyRoleSemantic
from descendants_timeline.model.genealogy import RawGenealogyData
from descendants_timeline.model.person import Person, PersonGender
from descendants_timeline.model.person_event_ref import EventRoleSemantic
from descendants_timeline.model.temporal import (
    TemporalValue,
    ValueOrigin,
    SourceQuality,
    EvidenceStatus,
    CertaintyLevel,
)
from descendants_timeline.model.temporal_constraint import (
    ConstraintOperator,
    ConstraintStrength,
)
from descendants_timeline.model.temporal_evidence import (
    EvidenceOwnerType,
    TemporalEvidence,
)
from descendants_timeline.model.temporal_target import (
    TemporalOwnerType,
    TemporalTarget,
    TargetSemantic,
)
from descendants_timeline.inference.divorce_before_death_rule import (
    DivorceBeforeDeathRule,
)
from descendants_timeline.inference.census_before_death_rule import (
    CensusBeforeDeathRule,
)
from descendants_timeline.inference.death_before_burial_rule import (
    DeathBeforeBurialRule,
)

from descendants_timeline.inference.birth_before_baptism_rule import (
    BirthBeforeBaptismRule,
)
from descendants_timeline.inference.birth_before_marriage_rule import (
    BirthBeforeMarriageRule,
)
from descendants_timeline.inference.birth_before_divorce_rule import (
    BirthBeforeDivorceRule,
)
from descendants_timeline.inference.birth_before_census_rule import (
    BirthBeforeCensusRule,
)
from descendants_timeline.inference.birth_before_burial_rule import (
    BirthBeforeBurialRule,
)
from descendants_timeline.inference.marriage_after_birth_rule import (
    MarriageAfterBirthRule,
)
from descendants_timeline.inference.marriage_before_divorce_rule import (
    MarriageBeforeDivorceRule,
)
from descendants_timeline.inference.marriage_before_spouse_death_rule import (
    MarriageBeforeSpouseDeathRule,
)
from descendants_timeline.inference.marriage_before_spouse_burial_rule import (
    MarriageBeforeSpouseBurialRule,
)
from descendants_timeline.inference.constraint_resolver import (
    ConstraintResolver,
)
from descendants_timeline.inference.divorce_after_marriage_rule import (
    DivorceAfterMarriageRule,
)
from descendants_timeline.inference.divorce_before_spouse_death_rule import (
    DivorceBeforeSpouseDeathRule,
)
from descendants_timeline.inference.divorce_before_spouse_burial_rule import (
    DivorceBeforeSpouseBurialRule,
)

class InferenceIntegrationTests(unittest.TestCase):

    def make_point_date(self, value: date) -> TemporalValue:
        return TemporalValue(
            source_value=value.isoformat(),
            source_calendar="GREGORIAN",
            normalized_minimum=value,
            normalized_maximum=value,
            representative_value=value,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

    def test_birth_baptism_marriage_refine_death_minimum(self):
        person1 = Person(
            person_id="I001",
            display_name="Joseph TEST",
            gender=PersonGender.MALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F001",),
        )

        person2 = Person(
            person_id="I002",
            display_name="Marie TEST",
            gender=PersonGender.FEMALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F001",),
        )

        family = Family(
            family_id="F001",
            parent1_id="I001",
            parent2_id="I002",
            event_refs=(),
            child_refs=(),
        )

        data = RawGenealogyData(
            persons={
                "I001": person1,
                "I002": person2,
            },
            families={
                "F001": family,
            },
            events={},
            root_person_id="I001",
        )

        birth_evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E001",
            semantic=EventSemantic.BIRTH,
            role=EventRoleSemantic.PRINCIPAL,
            date=self.make_point_date(date(1800, 1, 1)),
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        baptism_evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E002",
            semantic=EventSemantic.BAPTISM,
            role=EventRoleSemantic.PRINCIPAL,
            date=self.make_point_date(date(1801, 1, 1)),
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        marriage_evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.FAMILY,
            owner_id="F001",
            event_id="E003",
            semantic=EventSemantic.MARRIAGE,
            role=FamilyRoleSemantic.FAMILY,
            date=self.make_point_date(date(1825, 1, 1)),
            principal_owner_type=TemporalOwnerType.FAMILY,
            principal_owner_id="F001",
        )

        context = RuleContext(
            data=data,
            evidences=(
                birth_evidence,
                baptism_evidence,
                marriage_evidence,
            ),
        )

        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.DEATH,
        )

        engine = RuleEngine(
            rules=(
                BirthBeforeDeathRule(),
                BaptismBeforeDeathRule(),
                MarriageBeforeDeathRule(),
            )
        )

        constraints = engine.evaluate(
            target=target,
            context=context,
        )

        # Première vérification :
        # les trois raisonnements doivent exister.
        self.assertEqual(len(constraints), 3)

        self.assertEqual(
            tuple(
                constraint.rule_id
                for constraint in constraints
            ),
            (
                "BIRTH_BEFORE_DEATH",
                "BAPTISM_BEFORE_DEATH",
                "MARRIAGE_BEFORE_DEATH",
            ),
        )

        self.assertEqual(
            tuple(
                constraint.bound
                for constraint in constraints
            ),
            (
                date(1800, 1, 1),
                date(1801, 1, 1),
                date(1825, 1, 1),
            ),
        )

        self.assertTrue(
            all(
                constraint.operator
                is ConstraintOperator.AFTER_OR_EQUAL
                for constraint in constraints
            )
        )

        self.assertTrue(
            all(
                constraint.strength
                is ConstraintStrength.HARD
                for constraint in constraints
            )
        )

        # Deuxième vérification :
        # le Resolver doit sélectionner la borne
        # inférieure la plus restrictive.
        resolver = ConstraintResolver()

        resolution = resolver.resolve(
            target=target,
            constraints=constraints,
        )

        self.assertIsNotNone(resolution.hard_minimum)

        self.assertEqual(
            resolution.hard_minimum.value,
            date(1825, 1, 1),
        )

        self.assertIsNotNone(resolution.refined_minimum)

        self.assertEqual(
            resolution.refined_minimum.value,
            date(1825, 1, 1),
        )

        self.assertIsNone(resolution.hard_maximum)
        self.assertIsNone(resolution.refined_maximum)
        self.assertIsNone(resolution.conflict_type)

        # La justification déterminante doit être
        # celle du mariage de 1825.
        self.assertEqual(
            len(resolution.refined_minimum.constraints),
            1,
        )

        self.assertEqual(
            resolution.refined_minimum.constraints[0].rule_id,
            "MARRIAGE_BEFORE_DEATH",
        )

    def test_multiple_evidences_create_closed_death_domain(self):
        person1 = Person(
            person_id="I001",
            display_name="Joseph TEST",
            gender=PersonGender.MALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F001",),
        )

        person2 = Person(
            person_id="I002",
            display_name="Marie TEST",
            gender=PersonGender.FEMALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F001",),
        )

        family = Family(
            family_id="F001",
            parent1_id="I001",
            parent2_id="I002",
            event_refs=(),
            child_refs=(),
        )

        data = RawGenealogyData(
            persons={
                "I001": person1,
                "I002": person2,
            },
            families={
                "F001": family,
            },
            events={},
            root_person_id="I001",
        )

        birth_evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E001",
            semantic=EventSemantic.BIRTH,
            role=EventRoleSemantic.PRINCIPAL,
            date=self.make_point_date(date(1800, 1, 1)),
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        baptism_evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E002",
            semantic=EventSemantic.BAPTISM,
            role=EventRoleSemantic.PRINCIPAL,
            date=self.make_point_date(date(1801, 1, 1)),
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        marriage_evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.FAMILY,
            owner_id="F001",
            event_id="E003",
            semantic=EventSemantic.MARRIAGE,
            role=FamilyRoleSemantic.FAMILY,
            date=self.make_point_date(date(1825, 1, 1)),
            principal_owner_type=TemporalOwnerType.FAMILY,
            principal_owner_id="F001",
        )

        divorce_evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.FAMILY,
            owner_id="F001",
            event_id="E004",
            semantic=EventSemantic.DIVORCE,
            role=FamilyRoleSemantic.FAMILY,
            date=self.make_point_date(date(1840, 1, 1)),
            principal_owner_type=TemporalOwnerType.FAMILY,
            principal_owner_id="F001",
        )

        census_evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E005",
            semantic=EventSemantic.CENSUS,
            role=EventRoleSemantic.PRINCIPAL,
            date=self.make_point_date(date(1846, 1, 1)),
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        # L'inhumation n'est volontairement PAS une date ponctuelle.
        # Elle est connue entre 1850 et 1852.
        burial_date = TemporalValue(
            source_value="between 1850 and 1852",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1850, 1, 1),
            normalized_maximum=date(1852, 1, 1),
            representative_value=None,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        burial_evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E006",
            semantic=EventSemantic.BURIAL,
            role=EventRoleSemantic.PRINCIPAL,
            date=burial_date,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        context = RuleContext(
            data=data,
            evidences=(
                birth_evidence,
                baptism_evidence,
                marriage_evidence,
                divorce_evidence,
                census_evidence,
                burial_evidence,
            ),
        )

        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.DEATH,
        )

        engine = RuleEngine(
            rules=(
                BirthBeforeDeathRule(),
                BaptismBeforeDeathRule(),
                MarriageBeforeDeathRule(),
                DivorceBeforeDeathRule(),
                CensusBeforeDeathRule(),
                DeathBeforeBurialRule(),
            )
        )

        constraints = engine.evaluate(
            target=target,
            context=context,
        )

        # ---------------------------------------------------------
        # 1. Vérification du raisonnement produit par les Rules
        # ---------------------------------------------------------

        self.assertEqual(len(constraints), 6)

        self.assertEqual(
            tuple(constraint.rule_id for constraint in constraints),
            (
                "BIRTH_BEFORE_DEATH",
                "BAPTISM_BEFORE_DEATH",
                "MARRIAGE_BEFORE_DEATH",
                "DIVORCE_BEFORE_DEATH",
                "CENSUS_BEFORE_DEATH",
                "DEATH_BEFORE_BURIAL",
            ),
        )

        self.assertEqual(
            tuple(constraint.bound for constraint in constraints),
            (
                date(1800, 1, 1),
                date(1801, 1, 1),
                date(1825, 1, 1),
                date(1840, 1, 1),
                date(1846, 1, 1),
                date(1852, 1, 1),
            ),
        )

        # Les cinq premières contraintes sont des bornes inférieures.
        self.assertTrue(
            all(
                constraint.operator
                is ConstraintOperator.AFTER_OR_EQUAL
                for constraint in constraints[:5]
            )
        )

        # L'inhumation fournit au contraire une borne supérieure.
        self.assertIs(
            constraints[5].operator,
            ConstraintOperator.BEFORE_OR_EQUAL,
        )

        self.assertTrue(
            all(
                constraint.strength is ConstraintStrength.HARD
                for constraint in constraints
            )
        )

        # ---------------------------------------------------------
        # 2. Résolution de toutes les contraintes
        # ---------------------------------------------------------

        resolver = ConstraintResolver()

        resolution = resolver.resolve(
            target=target,
            constraints=constraints,
        )

        self.assertIsNone(resolution.conflict_type)

        self.assertIsNotNone(resolution.hard_minimum)
        self.assertIsNotNone(resolution.hard_maximum)

        self.assertEqual(
            resolution.hard_minimum.value,
            date(1846, 1, 1),
        )

        self.assertEqual(
            resolution.hard_maximum.value,
            date(1852, 1, 1),
        )

        # Comme nous n'avons ici que des contraintes HARD,
        # le domaine raffiné doit être identique.
        self.assertIsNotNone(resolution.refined_minimum)
        self.assertIsNotNone(resolution.refined_maximum)

        self.assertEqual(
            resolution.refined_minimum.value,
            date(1846, 1, 1),
        )

        self.assertEqual(
            resolution.refined_maximum.value,
            date(1852, 1, 1),
        )

        # ---------------------------------------------------------
        # 3. Vérification des justifications déterminantes
        # ---------------------------------------------------------

        self.assertEqual(
            len(resolution.refined_minimum.constraints),
            1,
        )

        self.assertEqual(
            resolution.refined_minimum.constraints[0].rule_id,
            "CENSUS_BEFORE_DEATH",
        )

        self.assertEqual(
            len(resolution.refined_maximum.constraints),
            1,
        )

        self.assertEqual(
            resolution.refined_maximum.constraints[0].rule_id,
            "DEATH_BEFORE_BURIAL",
        )
    def test_multiple_evidences_refine_birth_maximum(self):
        person1 = Person(
            person_id="I001",
            display_name="Joseph TEST",
            gender=PersonGender.MALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F001",),
        )

        person2 = Person(
            person_id="I002",
            display_name="Marie TEST",
            gender=PersonGender.FEMALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F001",),
        )

        family = Family(
            family_id="F001",
            parent1_id="I001",
            parent2_id="I002",
            event_refs=(),
            child_refs=(),
        )

        data = RawGenealogyData(
            persons={
                "I001": person1,
                "I002": person2,
            },
            families={
                "F001": family,
            },
            events={},
            root_person_id="I001",
        )

        baptism_evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E001",
            semantic=EventSemantic.BAPTISM,
            role=EventRoleSemantic.PRINCIPAL,
            date=self.make_point_date(date(1820, 1, 1)),
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        marriage_evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.FAMILY,
            owner_id="F001",
            event_id="E002",
            semantic=EventSemantic.MARRIAGE,
            role=FamilyRoleSemantic.FAMILY,
            date=self.make_point_date(date(1840, 1, 1)),
            principal_owner_type=TemporalOwnerType.FAMILY,
            principal_owner_id="F001",
        )

        divorce_evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.FAMILY,
            owner_id="F001",
            event_id="E003",
            semantic=EventSemantic.DIVORCE,
            role=FamilyRoleSemantic.FAMILY,
            date=self.make_point_date(date(1850, 1, 1)),
            principal_owner_type=TemporalOwnerType.FAMILY,
            principal_owner_id="F001",
        )

        census_evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E004",
            semantic=EventSemantic.CENSUS,
            role=EventRoleSemantic.PRINCIPAL,
            date=self.make_point_date(date(1831, 1, 1)),
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        death_evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E005",
            semantic=EventSemantic.DEATH,
            role=EventRoleSemantic.PRINCIPAL,
            date=self.make_point_date(date(1870, 1, 1)),
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        burial_evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E006",
            semantic=EventSemantic.BURIAL,
            role=EventRoleSemantic.PRINCIPAL,
            date=self.make_point_date(date(1871, 1, 1)),
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        context = RuleContext(
            data=data,
            evidences=(
                baptism_evidence,
                marriage_evidence,
                divorce_evidence,
                census_evidence,
                death_evidence,
                burial_evidence,
            ),
        )

        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        engine = RuleEngine(
            rules=(
                BirthBeforeBaptismRule(),
                BirthBeforeMarriageRule(),
                BirthBeforeDivorceRule(),
                BirthBeforeCensusRule(),
                BirthBeforeDeathRule(),
                BirthBeforeBurialRule(),
            )
        )

        constraints = engine.evaluate(
            target=target,
            context=context,
        )

        # Les six raisonnements doivent être présents.
        self.assertEqual(len(constraints), 6)

        self.assertEqual(
            tuple(constraint.rule_id for constraint in constraints),
            (
                "BIRTH_BEFORE_BAPTISM",
                "BIRTH_BEFORE_MARRIAGE",
                "BIRTH_BEFORE_DIVORCE",
                "BIRTH_BEFORE_CENSUS",
                "BIRTH_BEFORE_DEATH",
                "BIRTH_BEFORE_BURIAL",
            ),
        )

        self.assertEqual(
            tuple(constraint.bound for constraint in constraints),
            (
                date(1820, 1, 1),
                date(1840, 1, 1),
                date(1850, 1, 1),
                date(1831, 1, 1),
                date(1870, 1, 1),
                date(1871, 1, 1),
            ),
        )

        self.assertTrue(
            all(
                constraint.operator
                is ConstraintOperator.BEFORE_OR_EQUAL
                for constraint in constraints
            )
        )

        self.assertTrue(
            all(
                constraint.strength
                is ConstraintStrength.HARD
                for constraint in constraints
            )
        )

        resolver = ConstraintResolver()

        resolution = resolver.resolve(
            target=target,
            constraints=constraints,
        )

        # Aucune borne inférieure n'est produite dans ce scénario.
        self.assertIsNone(resolution.hard_minimum)
        self.assertIsNone(resolution.refined_minimum)

        # Parmi toutes les bornes supérieures HARD,
        # la plus restrictive est la plus ancienne : 1820.
        self.assertIsNotNone(resolution.hard_maximum)

        self.assertEqual(
            resolution.hard_maximum.value,
            date(1820, 1, 1),
        )

        self.assertIsNotNone(resolution.refined_maximum)

        self.assertEqual(
            resolution.refined_maximum.value,
            date(1820, 1, 1),
        )

        self.assertIsNone(resolution.conflict_type)

        # Et nous conservons la justification de la borne gagnante.
        self.assertEqual(
            len(resolution.refined_maximum.constraints),
            1,
        )

        self.assertEqual(
            resolution.refined_maximum.constraints[0].rule_id,
            "BIRTH_BEFORE_BAPTISM",
        )

    def test_multiple_evidences_build_marriage_constraints(self):
        person1 = Person(
            person_id="I001",
            display_name="Joseph TEST",
            gender=PersonGender.MALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F001",),
        )

        person2 = Person(
            person_id="I002",
            display_name="Marie TEST",
            gender=PersonGender.FEMALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F001",),
        )

        family = Family(
            family_id="F001",
            parent1_id="I001",
            parent2_id="I002",
            event_refs=(),
            child_refs=(),
        )

        data = RawGenealogyData(
            persons={
                "I001": person1,
                "I002": person2,
            },
            families={
                "F001": family,
            },
            events={},
            root_person_id="I001",
        )

        birth1 = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E001",
            semantic=EventSemantic.BIRTH,
            role=EventRoleSemantic.PRINCIPAL,
            date=self.make_point_date(date(1800, 1, 1)),
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        birth2 = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I002",
            event_id="E002",
            semantic=EventSemantic.BIRTH,
            role=EventRoleSemantic.PRINCIPAL,
            date=self.make_point_date(date(1805, 1, 1)),
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I002",
        )

        divorce = TemporalEvidence(
            owner_type=EvidenceOwnerType.FAMILY,
            owner_id="F001",
            event_id="E003",
            semantic=EventSemantic.DIVORCE,
            role=FamilyRoleSemantic.FAMILY,
            date=self.make_point_date(date(1850, 1, 1)),
            principal_owner_type=TemporalOwnerType.FAMILY,
            principal_owner_id="F001",
        )

        death1 = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E004",
            semantic=EventSemantic.DEATH,
            role=EventRoleSemantic.PRINCIPAL,
            date=self.make_point_date(date(1870, 1, 1)),
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        death2 = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I002",
            event_id="E005",
            semantic=EventSemantic.DEATH,
            role=EventRoleSemantic.PRINCIPAL,
            date=self.make_point_date(date(1880, 1, 1)),
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I002",
        )

        burial1 = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E006",
            semantic=EventSemantic.BURIAL,
            role=EventRoleSemantic.PRINCIPAL,
            date=self.make_point_date(date(1871, 1, 1)),
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        burial2 = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I002",
            event_id="E007",
            semantic=EventSemantic.BURIAL,
            role=EventRoleSemantic.PRINCIPAL,
            date=self.make_point_date(date(1881, 1, 1)),
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I002",
        )

        context = RuleContext(
            data=data,
            evidences=(
                birth1,
                birth2,
                divorce,
                death1,
                death2,
                burial1,
                burial2,
            ),
        )

        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F001",
            semantic=TargetSemantic.MARRIAGE,
        )

        engine = RuleEngine(
            rules=(
                MarriageAfterBirthRule(),
                MarriageBeforeDivorceRule(),
                MarriageBeforeSpouseDeathRule(),
                MarriageBeforeSpouseBurialRule(),
            )
        )

        constraints = engine.evaluate(
            target=target,
            context=context,
        )

        self.assertEqual(len(constraints), 7)

        self.assertEqual(
            tuple(constraint.rule_id for constraint in constraints),
            (
                "MARRIAGE_AFTER_BIRTH",
                "MARRIAGE_AFTER_BIRTH",
                "MARRIAGE_BEFORE_DIVORCE",
                "MARRIAGE_BEFORE_SPOUSE_DEATH",
                "MARRIAGE_BEFORE_SPOUSE_DEATH",
                "MARRIAGE_BEFORE_SPOUSE_BURIAL",
                "MARRIAGE_BEFORE_SPOUSE_BURIAL",
            ),
        )

        self.assertEqual(
            tuple(constraint.bound for constraint in constraints),
            (
                date(1800, 1, 1),
                date(1805, 1, 1),
                date(1850, 1, 1),
                date(1870, 1, 1),
                date(1880, 1, 1),
                date(1871, 1, 1),
                date(1881, 1, 1),
            ),
        )
        resolver = ConstraintResolver()

        resolution = resolver.resolve(
            target=target,
            constraints=constraints,
        )

        self.assertIsNone(resolution.conflict_type)

        self.assertIsNotNone(resolution.refined_minimum)
        self.assertIsNotNone(resolution.refined_maximum)

        self.assertEqual(
            resolution.refined_minimum.value,
            date(1805, 1, 1),
        )

        self.assertEqual(
            resolution.refined_maximum.value,
            date(1850, 1, 1),
        )

        self.assertEqual(
            resolution.refined_minimum.constraints[0].rule_id,
            "MARRIAGE_AFTER_BIRTH",
        )

        self.assertEqual(
            resolution.refined_maximum.constraints[0].rule_id,
            "MARRIAGE_BEFORE_DIVORCE",
        )
    def test_multiple_evidences_build_divorce_domain(self):
        person1 = Person(
            person_id="I001",
            display_name="Joseph TEST",
            gender=PersonGender.MALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F001",),
        )

        person2 = Person(
            person_id="I002",
            display_name="Marie TEST",
            gender=PersonGender.FEMALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F001",),
        )

        family = Family(
            family_id="F001",
            parent1_id="I001",
            parent2_id="I002",
            event_refs=(),
            child_refs=(),
        )

        data = RawGenealogyData(
            persons={
                "I001": person1,
                "I002": person2,
            },
            families={
                "F001": family,
            },
            events={},
            root_person_id="I001",
        )

        marriage = TemporalEvidence(
            owner_type=EvidenceOwnerType.FAMILY,
            owner_id="F001",
            event_id="E001",
            semantic=EventSemantic.MARRIAGE,
            role=FamilyRoleSemantic.FAMILY,
            date=self.make_point_date(date(1825, 1, 1)),
            principal_owner_type=TemporalOwnerType.FAMILY,
            principal_owner_id="F001",
        )

        death1 = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E002",
            semantic=EventSemantic.DEATH,
            role=EventRoleSemantic.PRINCIPAL,
            date=self.make_point_date(date(1870, 1, 1)),
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        death2 = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I002",
            event_id="E003",
            semantic=EventSemantic.DEATH,
            role=EventRoleSemantic.PRINCIPAL,
            date=self.make_point_date(date(1880, 1, 1)),
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I002",
        )

        burial1 = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E004",
            semantic=EventSemantic.BURIAL,
            role=EventRoleSemantic.PRINCIPAL,
            date=self.make_point_date(date(1871, 1, 1)),
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        burial2 = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I002",
            event_id="E005",
            semantic=EventSemantic.BURIAL,
            role=EventRoleSemantic.PRINCIPAL,
            date=self.make_point_date(date(1881, 1, 1)),
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I002",
        )

        context = RuleContext(
            data=data,
            evidences=(
                marriage,
                death1,
                death2,
                burial1,
                burial2,
            ),
        )

        target = TemporalTarget(
            owner_type=TemporalOwnerType.FAMILY,
            owner_id="F001",
            semantic=TargetSemantic.DIVORCE,
        )

        engine = RuleEngine(
            rules=(
                DivorceAfterMarriageRule(),
                DivorceBeforeSpouseDeathRule(),
                DivorceBeforeSpouseBurialRule(),
            )
        )

        constraints = engine.evaluate(
            target=target,
            context=context,
        )

        self.assertEqual(len(constraints), 5)

        self.assertEqual(
            tuple(constraint.rule_id for constraint in constraints),
            (
                "DIVORCE_AFTER_MARRIAGE",
                "DIVORCE_BEFORE_SPOUSE_DEATH",
                "DIVORCE_BEFORE_SPOUSE_DEATH",
                "DIVORCE_BEFORE_SPOUSE_BURIAL",
                "DIVORCE_BEFORE_SPOUSE_BURIAL",
            ),
        )

        self.assertEqual(
            tuple(constraint.bound for constraint in constraints),
            (
                date(1825, 1, 1),
                date(1870, 1, 1),
                date(1880, 1, 1),
                date(1871, 1, 1),
                date(1881, 1, 1),
            ),
        )

        resolver = ConstraintResolver()

        resolution = resolver.resolve(
            target=target,
            constraints=constraints,
        )

        self.assertIsNone(resolution.conflict_type)

        self.assertIsNotNone(resolution.refined_minimum)
        self.assertIsNotNone(resolution.refined_maximum)

        self.assertEqual(
            resolution.refined_minimum.value,
            date(1825, 1, 1),
        )

        self.assertEqual(
            resolution.refined_maximum.value,
            date(1870, 1, 1),
        )

        self.assertEqual(
            resolution.refined_minimum.constraints[0].rule_id,
            "DIVORCE_AFTER_MARRIAGE",
        )

        self.assertEqual(
            resolution.refined_maximum.constraints[0].rule_id,
            "DIVORCE_BEFORE_SPOUSE_DEATH",
        )

if __name__ == "__main__":
    unittest.main()