from descendants_timeline.inference.rule import Rule
from descendants_timeline.inference.rule_context import RuleContext

from descendants_timeline.model.temporal_target import (
    TemporalOwnerType,
    TemporalTarget,
    TargetSemantic,
)

from descendants_timeline.model.event import EventSemantic
from descendants_timeline.model.family_event_ref import FamilyRoleSemantic
from descendants_timeline.model.temporal_constraint import (
    ConstraintOperator,
    ConstraintStrength,
    TemporalConstraint,
)
from descendants_timeline.model.temporal_evidence import (
    EvidenceOwnerType,
)

from .date_arithmetic import add_years
from .inference_parameters import MIN_MARRIAGE_AGE_YEARS


class BirthMinimumAgeAtMarriageRule(Rule):
    rule_id = "BIRTH_MINIMUM_AGE_AT_MARRIAGE"
    strength = ConstraintStrength.SOFT

    def is_applicable(
        self,
        target: TemporalTarget,
        context: RuleContext,
    ) -> bool:
        return (
            target.owner_type is TemporalOwnerType.PERSON
            and target.semantic is TargetSemantic.BIRTH
        )

    def evaluate(
        self,
        target: TemporalTarget,
        context: RuleContext,
    ) -> tuple[TemporalConstraint, ...]:

        if not self.is_applicable(target, context):
            return ()

        marriage_evidences = tuple(
            evidence
            for evidence in context.evidences
            if (
                evidence.semantic is EventSemantic.MARRIAGE
                and evidence.owner_type is EvidenceOwnerType.FAMILY
                and evidence.role is FamilyRoleSemantic.FAMILY
                and evidence.principal_owner_type
                is TemporalOwnerType.FAMILY
                and evidence.principal_owner_id == evidence.owner_id
            )
        )

        constraints = []

        for marriage_evidence in marriage_evidences:
            family = context.data.families.get(
                marriage_evidence.owner_id
            )

            if family is None:
                continue

            if target.owner_id not in (
                family.parent1_id,
                family.parent2_id,
            ):
                continue

            marriage_maximum = (
                marriage_evidence.date.normalized_maximum
            )

            if marriage_maximum is None:
                continue

            constraints.append(
                TemporalConstraint(
                    target=target,
                    operator=ConstraintOperator.BEFORE_OR_EQUAL,
                    bound=add_years(
                        marriage_maximum,
                        -MIN_MARRIAGE_AGE_YEARS,
                    ),
                    rule_id=self.rule_id,
                    strength=self.strength,
                    evidences=(marriage_evidence,),
                )
            )

        return tuple(constraints)