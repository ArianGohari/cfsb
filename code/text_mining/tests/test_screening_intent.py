from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from litmine import engine, rules


class ScreeningIntentTests(unittest.TestCase):
    def assess(self, text, profile='clock_cancer', task='fulltext_eligibility'):
        return rules.screen(task, dict(text=text, profile=profile))

    def test_reported_investigation_allows_uncertain_result(self):
        for profile in ('clock_cancer', 'task4_caco2_sarscov2'):
            for text in (
                'We investigated whether the output changed.',
                'We tested if the output could change.',
                'We measured whether the output was not stable.',
                'We observed that the output might change.',
                'We demonstrated that no output changed.',
                'We showed that the output was unlikely to change.',
                'In this study, we investigated whether the output changed.',
                'WE TESTED WHETHER THE OUTPUT CHANGED',
            ):
                with self.subTest(profile=profile, text=text):
                    result = self.assess(text, profile)
                    self.assertEqual(result['criteria_evidence'], {'I2': text})
                    self.assertEqual(result['decision'], 'unclear')
                    self.assertIsNone(result['evidence_quote'])

    def test_unperformed_or_qualified_investigation_abstains(self):
        for profile in ('clock_cancer', 'task4_caco2_sarscov2'):
            for text in (
                'We did not investigate whether the output changed.',
                'We never tested whether the output changed.',
                "We didn't investigate whether the output changed.",
                'We didn’t investigate whether the output changed.',
                'We failed to test whether the output changed.',
                'We might investigate whether the output changed.',
                'If we investigated whether the output changed, we would know.',
                'We investigated whether the output changed if resources allowed.',
                'We investigated whether the output changed, had we received approval.',
                'We investigated whether the output changed but did not finish.',
                'We investigated whether the output changed and might test again.',
                'We investigated whether the output changed?',
                'Suppose we investigated whether the output changed.',
                'It is not true that we investigated whether the output changed.',
                'We plan to test the output in this study.',
                'Our experiments are planned for next year.',
                'Our experiments will test the output.',
                'In this study, we intend to measure the output.',
                'In this study, we aim to measure the output.',
                'Our experiments are hypothetical.',
                'Our experiments might measure the output.',
                'A mechanistic model could test the output.',
                'We measured output but did not finish.',
                'The output may change.',
            ):
                with self.subTest(profile=profile, text=text):
                    self.assertNotIn('I2', self.assess(text, profile)['criteria_evidence'])

    def test_independent_cases_through_final_validation(self):
        for profile, topic, criteria in (
            ('clock_cancer', 'Circadian clock and cancer.', engine.TOPIC_CRITERIA),
            ('task4_caco2_sarscov2', 'Caco2 and SARS-CoV-2.', engine.TASK4_CRITERIA),
        ):
            for sentence, expected in (
                ('We investigated whether A affects B.', 'include'),
                ('We tested if A might affect B.', 'include'),
                ('We did not investigate whether A affects B.', 'unclear'),
                ('In this study, we may investigate whether A affects B.', 'unclear'),
                ('Our experiments will test whether A affects B.', 'unclear'),
                ('If we investigated A, we would measure B.', 'unclear'),
                ('In this study, we hypothesize that A affects B.', 'unclear'),
                ('We investigated whether A affects B using the procedure described in [7].', 'include'),
                ('The cited authors wrote, "We investigated whether A affects B" [7].', 'unclear'),
                ('Earlier work suggested that A might affect B [7]. We investigated whether A affects B.', 'include'),
            ):
                with self.subTest(profile=profile, sentence=sentence):
                    text = topic + '\n' + sentence
                    response = self.assess(text, profile)
                    assessment = engine.validate_screen(response, text, criteria, 'fulltext_eligibility')
                    final = engine.validate_fulltext_decision(response, {'text': text}, criteria, [assessment])
                    self.assertEqual(final['decision'], expected)
                    self.assertEqual('I2' in response['criteria_evidence'], expected == 'include')

    def test_existing_safe_evidence_and_review_exclusion(self):
        for text in ('We measured the output.', 'Our experiments measured the output.',
                     'In this study, the output was measured.', 'A mechanistic model was used.'):
            with self.subTest(text=text):
                self.assertEqual(self.assess(text)['criteria_evidence'], {'I2': text})
        result = self.assess('We investigated whether the output changed. This article is a review.')
        self.assertEqual(result['decision'], 'exclude')
        self.assertEqual(result['criteria_evidence'], {'E3': 'This article is a review.'})

    def test_legacy_and_title_abstract_do_not_gain_i2(self):
        text = 'We investigated whether the output changed.'
        self.assertEqual(self.assess(text, 'legacy_clock')['criteria_evidence'], {})
        self.assertEqual(rules.screen('fulltext_eligibility', {'text': text})['criteria_evidence'], {})
        for profile in rules.PROFILES:
            with self.subTest(profile=profile):
                self.assertEqual(self.assess(text, profile, 'title_abstract')['criteria_evidence'], {})

    def test_evidence_stays_sentence_local(self):
        first = 'We investigated whether the output might change.'
        text = 'We plan to test the output. ' + first + ' We tested whether it changed.'
        self.assertEqual(self.assess(text)['criteria_evidence'], {'I2': first})

    def test_uncertain_screening_evidence_does_not_create_relations(self):
        for text in ('We investigated whether Alpha binds Beta.',
                     'We showed that Alpha might bind Beta.',
                     'We observed that Alpha does not bind Beta.'):
            entities = [dict(entity_id=name, name=name, kind='Protein') for name in ('Alpha', 'Beta')]
            mentions = [dict(entity_id=m.group(), text=m.group(), start=m.start(), end=m.end())
                        for m in re.finditer(r'\b(?:Alpha|Beta)\b', text)]
            data = dict(text=text, entities=entities, mentions=mentions)
            with self.subTest(text=text):
                self.assertIn('I2', self.assess(text)['criteria_evidence'])
                self.assertEqual(rules.extract(data)['candidates'], [])
                self.assertEqual(rules.extract_assertions(data)['candidates'], [])


if __name__ == '__main__':
    unittest.main()
