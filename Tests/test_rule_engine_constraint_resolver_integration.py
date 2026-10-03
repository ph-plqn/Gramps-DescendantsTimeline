import unittest
from datetime import date

from descendants_timeline.inference.birth_before_death_rule import (
    BirthBeforeDeathRule,
)
from descendants_timeline.inference.birth_maximum_lifespan_from_death_rule import (
    BirthMaximumLifespanFromDeathRule,
)
from descendants_timeline.inference.constraint_resolver import (
    ConstraintResolver,
)
from descendants_timeline.inference.rule_context import RuleContext
from descendants_timeline.inference.rule_engine import RuleEngine

from descendants_timeline.model.event import EventSemantic
from descendants_timeline.model.genealogy import RawGenealogyData
from descendants_timeline.model.person import Person, PersonGender
from descendants_timeline.model.person_event_ref import EventRoleSemantic
from descendants_timeline.model.temporal import (
    CertaintyLevel,
    EvidenceStatus,
    SourceQuality,
    TemporalValue,
    ValueOrigin,
)
from descendants_timeline.model.temporal_constraint import (
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

from descendants_timeline.inference.birth_before_marriage_rule import (
    BirthBeforeMarriageRule,
)
from descendants_timeline.inference.birth_before_census_rule import (
    BirthBeforeCensusRule,
)
from descendants_timeline.inference.birth_minimum_age_at_marriage_rule import (
    BirthMinimumAgeAtMarriageRule,
)
from descendants_timeline.inference.birth_maximum_lifespan_from_census_rule import (
    BirthMaximumLifespanFromCensusRule,
)

from descendants_timeline.model.family import Family
from descendants_timeline.model.family_event_ref import FamilyRoleSemantic
from descendants_timeline.inference.temporal_reconciler import (
    TemporalReconciler,
)
from descendants_timeline.inference.reconciled_temporal_domain import (
    ReconciledBoundOrigin,
)
from descendants_timeline.inference.reconciled_temporal_domain import (
    ReconciledBoundOrigin,
    ReconciliationConflictType,
)
from descendants_timeline.inference.temporal_estimator import (
    TemporalEstimator,
)
class RuleEngineConstraintResolverIntegrationTests(unittest.TestCase):

    def make_marriage_census_death_scenario(self):
        person = Person(
            person_id="I001",
            display_name="Joseph TEST",
            gender=PersonGender.MALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=("F001",),
        )

        spouse = Person(
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
                "I001": person,
                "I002": spouse,
            },
            families={
                "F001": family,
            },
            events={},
            root_person_id="I001",
        )

        marriage_date = TemporalValue(
            source_value="15/06/1850",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1850, 6, 15),
            normalized_maximum=date(1850, 6, 15),
            representative_value=date(1850, 6, 15),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        census_date = TemporalValue(
            source_value="01/06/1880",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1880, 6, 1),
            normalized_maximum=date(1880, 6, 1),
            representative_value=date(1880, 6, 1),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        death_date = TemporalValue(
            source_value="10/03/1900",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1900, 3, 10),
            normalized_maximum=date(1900, 3, 10),
            representative_value=date(1900, 3, 10),
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        marriage_evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.FAMILY,
            owner_id="F001",
            event_id="E_MARRIAGE",
            semantic=EventSemantic.MARRIAGE,
            role=FamilyRoleSemantic.FAMILY,
            date=marriage_date,
            principal_owner_type=TemporalOwnerType.FAMILY,
            principal_owner_id="F001",
        )

        census_evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E_CENSUS",
            semantic=EventSemantic.CENSUS,
            role=EventRoleSemantic.PRINCIPAL,
            date=census_date,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        death_evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E_DEATH",
            semantic=EventSemantic.DEATH,
            role=EventRoleSemantic.PRINCIPAL,
            date=death_date,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        context = RuleContext(
            data=data,
            evidences=(
                marriage_evidence,
                census_evidence,
                death_evidence,
            ),
        )

        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        engine = RuleEngine(
            rules=(
                BirthBeforeMarriageRule(),
                BirthBeforeCensusRule(),
                BirthBeforeDeathRule(),
                BirthMinimumAgeAtMarriageRule(),
                BirthMaximumLifespanFromCensusRule(),
                BirthMaximumLifespanFromDeathRule(),
            ),
        )

        constraints = engine.evaluate(
            target,
            context,
        )

        resolution = ConstraintResolver().resolve(
            target=target,
            constraints=constraints,
        )

        return target, constraints, resolution

    def test_birth_domain_from_death_hard_and_soft_rules(self):
        person = Person(
            person_id="I001",
            display_name="Joseph TEST",
            gender=PersonGender.MALE,
            event_refs=(),
            parent_family_ids=(),
            family_ids=(),
        )

        data = RawGenealogyData(
            persons={"I001": person},
            families={},
            events={},
            root_person_id="I001",
        )

        death_date = TemporalValue(
            source_value="17/08/1872-19/08/1872",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1872, 8, 17),
            normalized_maximum=date(1872, 8, 19),
            representative_value=None,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        death_evidence = TemporalEvidence(
            owner_type=EvidenceOwnerType.PERSON,
            owner_id="I001",
            event_id="E001",
            semantic=EventSemantic.DEATH,
            role=EventRoleSemantic.PRINCIPAL,
            date=death_date,
            principal_owner_type=TemporalOwnerType.PERSON,
            principal_owner_id="I001",
        )

        context = RuleContext(
            data=data,
            evidences=(death_evidence,),
        )

        target = TemporalTarget(
            owner_type=TemporalOwnerType.PERSON,
            owner_id="I001",
            semantic=TargetSemantic.BIRTH,
        )

        engine = RuleEngine(
            rules=(
                BirthBeforeDeathRule(),
                BirthMaximumLifespanFromDeathRule(),
            ),
        )

        constraints = engine.evaluate(
            target,
            context,
        )

        resolver = ConstraintResolver()

        resolution = resolver.resolve(
            target=target,
            constraints=constraints,
        )

        self.assertEqual(len(constraints), 2)

        self.assertIsNone(
            resolution.hard_minimum,
        )

        self.assertEqual(
            resolution.hard_maximum.value,
            date(1872, 8, 19),
        )

        self.assertEqual(
            resolution.hard_maximum.strength,
            ConstraintStrength.HARD,
        )

        self.assertEqual(
            resolution.refined_minimum.value,
            date(1747, 8, 17),
        )

        self.assertEqual(
            resolution.refined_minimum.strength,
            ConstraintStrength.SOFT,
        )

        self.assertEqual(
            resolution.refined_maximum.value,
            date(1872, 8, 19),
        )

        self.assertEqual(
            resolution.refined_maximum.strength,
            ConstraintStrength.HARD,
        )

        self.assertIsNone(
            resolution.conflict_type,
        )

        self.assertEqual(
            resolution.conflicting_constraints,
            (),
        )

    def test_birth_domain_from_marriage_census_and_death(self):
       
        target, constraints, resolution = (
            self.make_marriage_census_death_scenario()
        )
        resolver = ConstraintResolver()

        resolution = resolver.resolve(
            target=target,
            constraints=constraints,
        )

        self.assertEqual(
            len(constraints),
            6,
        )

        self.assertIsNone(
            resolution.hard_minimum,
        )

        self.assertEqual(
            resolution.hard_maximum.value,
            date(1850, 6, 15),
        )

        self.assertEqual(
            resolution.hard_maximum.strength,
            ConstraintStrength.HARD,
        )

        self.assertEqual(
            resolution.refined_minimum.value,
            date(1775, 3, 10),
        )

        self.assertEqual(
            resolution.refined_minimum.strength,
            ConstraintStrength.SOFT,
        )

        self.assertEqual(
            resolution.refined_maximum.value,
            date(1838, 6, 15),
        )

        self.assertEqual(
            resolution.refined_maximum.strength,
            ConstraintStrength.SOFT,
        )

        self.assertIsNone(
            resolution.conflict_type,
        )

        self.assertEqual(
            resolution.conflicting_constraints,
            (),
        )

        gramps_birth = TemporalValue.unknown()

        reconciler = TemporalReconciler()

        reconciled = reconciler.reconcile(
            target=target,
            gramps_value=gramps_birth,
            constraint_resolution=resolution,
        )

        self.assertEqual(
            reconciled.principal_minimum.value,
            date(1775, 3, 10),
        )

        self.assertEqual(
            reconciled.principal_minimum.origin,
            ReconciledBoundOrigin.INFERENCE,
        )

        self.assertIs(
            reconciled.principal_minimum.inferred_bound,
            resolution.refined_minimum,
        )

        self.assertEqual(
            reconciled.principal_maximum.value,
            date(1838, 6, 15),
        )

        self.assertEqual(
            reconciled.principal_maximum.origin,
            ReconciledBoundOrigin.INFERENCE,
        )

        self.assertIs(
            reconciled.principal_maximum.inferred_bound,
            resolution.refined_maximum,
        )

        self.assertIsNone(
            reconciled.conflict_type,
        )

        self.assertEqual(
            reconciled.conflicting_bounds,
            (),
        )

    def test_gramps_minimum_remains_sovereign_over_inferred_birth_domain(self):
        target, constraints, resolution = (
            self.make_marriage_census_death_scenario()
        )

        gramps_birth = TemporalValue(
            source_value="après 01/01/1800",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1800, 1, 1),
            normalized_maximum=None,
            representative_value=None,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        reconciled = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_birth,
            constraint_resolution=resolution,
        )

        # L'inférence avait bien calculé :
        # [10/03/1775 ; 15/06/1838].
        self.assertEqual(
            resolution.refined_minimum.value,
            date(1775, 3, 10),
        )

        self.assertEqual(
            resolution.refined_maximum.value,
            date(1838, 6, 15),
        )

        # Mais le minimum déjà présent dans Gramps est souverain.
        self.assertEqual(
            reconciled.principal_minimum.value,
            date(1800, 1, 1),
        )

        self.assertEqual(
            reconciled.principal_minimum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )

        self.assertIsNone(
            reconciled.principal_minimum.inferred_bound,
        )

        # Gramps n'avait aucun maximum :
        # l'inférence peut donc compléter cette borne manquante.
        self.assertEqual(
            reconciled.principal_maximum.value,
            date(1838, 6, 15),
        )

        self.assertEqual(
            reconciled.principal_maximum.origin,
            ReconciledBoundOrigin.INFERENCE,
        )

        self.assertIs(
            reconciled.principal_maximum.inferred_bound,
            resolution.refined_maximum,
        )

        self.assertIsNone(
            reconciled.conflict_type,
        )

        self.assertEqual(
            reconciled.conflicting_bounds,
            (),
        )

    def test_conflicting_inferred_maximum_does_not_override_gramps_minimum(
        self,
    ):
        target, constraints, resolution = (
            self.make_marriage_census_death_scenario()
        )

        gramps_birth = TemporalValue(
            source_value="après 01/01/1850",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1850, 1, 1),
            normalized_maximum=None,
            representative_value=None,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        # L'inférence a réellement produit :
        # [10/03/1775 ; 15/06/1838].
        self.assertEqual(
            resolution.refined_minimum.value,
            date(1775, 3, 10),
        )

        self.assertEqual(
            resolution.refined_maximum.value,
            date(1838, 6, 15),
        )

        reconciled = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_birth,
            constraint_resolution=resolution,
        )

        # Le minimum Gramps reste souverain.
        self.assertEqual(
            reconciled.principal_minimum.value,
            date(1850, 1, 1),
        )

        self.assertEqual(
            reconciled.principal_minimum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )

        self.assertIsNone(
            reconciled.principal_minimum.inferred_bound,
        )

        # Le maximum inféré 1838 est incompatible avec
        # le minimum Gramps 1850 : il ne doit donc pas
        # entrer dans le domaine principal.
        self.assertIsNone(
            reconciled.principal_maximum,
        )

        # Mais cette incompatibilité doit être conservée
        # comme diagnostic Gramps ↔ inférence.
        self.assertEqual(
            reconciled.conflict_type,
            ReconciliationConflictType.GRAMPS_INFERENCE,
        )

        self.assertEqual(
            reconciled.conflicting_bounds,
            (resolution.refined_maximum,),
        )

    def test_non_point_inferred_birth_domain_has_no_representative_value(
        self,
    ):
        target, constraints, resolution = (
            self.make_marriage_census_death_scenario()
        )

        reconciled = TemporalReconciler().reconcile(
            target=target,
            gramps_value=TemporalValue.unknown(),
            constraint_resolution=resolution,
        )

        # La chaîne précédente a réellement produit
        # un domaine fermé mais non ponctuel.
        self.assertEqual(
            reconciled.principal_minimum.value,
            date(1775, 3, 10),
        )

        self.assertEqual(
            reconciled.principal_maximum.value,
            date(1838, 6, 15),
        )

        estimate = TemporalEstimator().estimate(
            reconciled,
        )

        # Un intervalle n'est pas une date.
        # Aucune valeur représentative généalogique
        # ne doit être inventée.
        self.assertIsNone(
            estimate.representative_value,
        )

        self.assertEqual(
            estimate.certainty,
            CertaintyLevel.UNDETERMINED,
        )

    def test_mixed_point_birth_domain_has_representative_value(
        self,
    ):
        target, constraints, resolution = (
            self.make_marriage_census_death_scenario()
        )

        # L'inférence a établi cette borne supérieure
        # grâce à l'âge minimum au mariage.
        self.assertEqual(
            resolution.refined_maximum.value,
            date(1838, 6, 15),
        )

        gramps_birth = TemporalValue(
            source_value="après le 15/06/1838",
            source_calendar="GREGORIAN",
            normalized_minimum=date(1838, 6, 15),
            normalized_maximum=None,
            representative_value=None,
            value_origin=ValueOrigin.GRAMPS,
            source_quality=SourceQuality.NORMAL,
            evidence_status=EvidenceStatus.EVIDENCE_USABLE,
            certainty=CertaintyLevel.CERTAIN,
        )

        reconciled = TemporalReconciler().reconcile(
            target=target,
            gramps_value=gramps_birth,
            constraint_resolution=resolution,
        )

        # La borne inférieure vient de Gramps.
        self.assertEqual(
            reconciled.principal_minimum.value,
            date(1838, 6, 15),
        )

        self.assertEqual(
            reconciled.principal_minimum.origin,
            ReconciledBoundOrigin.GRAMPS,
        )

        # La borne supérieure vient de l'inférence.
        self.assertEqual(
            reconciled.principal_maximum.value,
            date(1838, 6, 15),
        )

        self.assertEqual(
            reconciled.principal_maximum.origin,
            ReconciledBoundOrigin.INFERENCE,
        )

        self.assertIs(
            reconciled.principal_maximum.inferred_bound,
            resolution.refined_maximum,
        )

        # Les deux bornes coïncident :
        # le domaine principal est maintenant ponctuel.
        estimate = TemporalEstimator().estimate(
            reconciled,
        )

        self.assertEqual(
            estimate.representative_value,
            date(1838, 6, 15),
        )

        self.assertEqual(
            estimate.certainty,
            CertaintyLevel.UNDETERMINED,
        )

if __name__ == "__main__":
    unittest.main()