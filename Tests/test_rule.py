import unittest

from descendants_timeline.inference.rule import Rule
from descendants_timeline.model.temporal_constraint import ConstraintStrength


class RuleTests(unittest.TestCase):

    def test_rule_cannot_be_instantiated_directly(self):
        with self.assertRaises(TypeError):
            Rule()

    def test_incomplete_rule_cannot_be_instantiated(self):
        class IncompleteRule(Rule):
            rule_id = "INCOMPLETE"
            strength = ConstraintStrength.HARD

            def is_applicable(self, target, context):
                return True

        with self.assertRaises(TypeError):
            IncompleteRule()
    def test_rule_without_is_applicable_cannot_be_instantiated(self):
        class IncompleteRule(Rule):
            rule_id = "INCOMPLETE"
            strength = ConstraintStrength.HARD

            def evaluate(self, target, context):
                return ()

        with self.assertRaises(TypeError):
            IncompleteRule()

    def test_complete_rule_can_be_instantiated(self):
        class CompleteRule(Rule):
            rule_id = "COMPLETE"
            strength = ConstraintStrength.HARD

            def is_applicable(self, target, context):
                return True

            def evaluate(self, target, context):
                return ()

        rule = CompleteRule()

        self.assertEqual(rule.rule_id, "COMPLETE")
        self.assertIs(rule.strength, ConstraintStrength.HARD)

if __name__ == "__main__":
    unittest.main()