import unittest

from descendants_timeline.inference.default_rules import (
    default_rules,
)
from descendants_timeline.inference.rule import Rule


class DefaultRulesTests(unittest.TestCase):

    def test_default_rules_returns_all_rules(self) -> None:
        rules = default_rules()

        self.assertIsInstance(rules, tuple)
        self.assertEqual(len(rules), 24)
        self.assertTrue(
            all(
                isinstance(rule, Rule)
                for rule in rules
            )
        )
    def test_default_rules_have_expected_order(self) -> None:
        rules = default_rules()

        self.assertEqual(
            tuple(rule.rule_id for rule in rules),
            (
                "BIRTH_BEFORE_BAPTISM",
                "BIRTH_BEFORE_BURIAL",
                "BIRTH_BEFORE_CENSUS",
                "BIRTH_BEFORE_DEATH",
                "BIRTH_BEFORE_MARRIAGE",
                "BIRTH_BEFORE_DIVORCE",
                "BIRTH_MAXIMUM_LIFESPAN_FROM_BURIAL",
                "BIRTH_MAXIMUM_LIFESPAN_FROM_CENSUS",
                "BIRTH_MAXIMUM_LIFESPAN_FROM_DEATH",
                "BIRTH_MINIMUM_AGE_AT_MARRIAGE",

                "BAPTISM_BEFORE_DEATH",
                "CENSUS_BEFORE_DEATH",
                "MARRIAGE_BEFORE_DEATH",
                "DIVORCE_BEFORE_DEATH",
                "DEATH_BEFORE_BURIAL",
                "DEATH_MAXIMUM_LIFESPAN_FROM_BIRTH",

                "MARRIAGE_AFTER_BIRTH",
                "MARRIAGE_BEFORE_DIVORCE",
                "MARRIAGE_BEFORE_SPOUSE_BURIAL",
                "MARRIAGE_BEFORE_SPOUSE_DEATH",
                "MARRIAGE_MINIMUM_AGE_FROM_BIRTH",

                "DIVORCE_AFTER_MARRIAGE",
                "DIVORCE_BEFORE_SPOUSE_BURIAL",
                "DIVORCE_BEFORE_SPOUSE_DEATH",
            ),
        )

if __name__ == "__main__":
    unittest.main()