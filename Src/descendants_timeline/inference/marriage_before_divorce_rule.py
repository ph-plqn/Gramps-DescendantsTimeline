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


class MarriageBeforeDivorceRule(Rule):
    rule_id = "MARRIAGE_BEFORE_DIVORCE"
    strength = ConstraintStrength.HARD

    def is_applicable(
        self,
        target: TemporalTarget,
        context: RuleContext,
    ) -> bool:
        return (
            target.owner_type is TemporalOwnerType.FAMILY
            and target.semantic is TargetSemantic.MARRIAGE
        )

    def evaluate(
        self,
        target: TemporalTarget,
        context: RuleContext,
    ) -> tuple[TemporalConstraint, ...]:

        if not self.is_applicable(target, context):
            return ()

        divorce_evidences = tuple(
            evidence
            for evidence in context.evidences
            if (
                evidence.semantic is EventSemantic.DIVORCE
                and evidence.owner_type is EvidenceOwnerType.FAMILY
                and evidence.owner_id == target.owner_id
                and evidence.role is FamilyRoleSemantic.FAMILY
                and evidence.principal_owner_type
                is TemporalOwnerType.FAMILY
                and evidence.principal_owner_id
                == target.owner_id
            )
        )

        constraints = []

        for divorce_evidence in divorce_evidences:
            if divorce_evidence.date.normalized_maximum is None:
                continue

            constraints.append(
                TemporalConstraint(
                    target=target,
                    operator=ConstraintOperator.BEFORE_OR_EQUAL,
                    bound=divorce_evidence.date.normalized_maximum,
                    rule_id=self.rule_id,
                    strength=self.strength,
                    evidences=(divorce_evidence,),
                )
            )

        return tuple(constraints)