import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analyzer import analyze, highlight, parse_response


class AnalyzerTests(unittest.TestCase):
    def test_requested_examples(self):
        self.assertEqual(analyze('AI 漫剧赚钱')['label'], '正向')
        self.assertEqual(analyze('AI 漫剧侵权 ')['label'], '负向')
        self.assertEqual(analyze('AI 漫剧教程')['label'], '中性')

    def test_conflict_uses_occurrence_majority(self):
        self.assertEqual(analyze('赚钱推荐收益侵权')['label'], '正向')
        self.assertEqual(analyze('赚钱侵权')['label'], '中性')

    def test_negation_is_not_silently_reinterpreted(self):
        self.assertEqual(analyze('不赚钱')['label'], '正向')

    def test_domain_phrase_and_nested_hit(self):
        result = analyze('AI漫剧版权合规')
        self.assertIn('AI漫剧', result['tokens'])
        self.assertIn('版权', result['tokens'])
        self.assertEqual(result['negative_hits'], ['版权'])

    def test_repetition_counts_as_original_code(self):
        self.assertGreater(analyze('赚钱赚钱赚钱')['confidence'], analyze('赚钱')['confidence'])
        self.assertEqual(analyze('教程')['confidence'], 0)

    def test_jsonp_strict_and_no_code_execution(self):
        self.assertEqual(parse_response('nlp_demo({"s":["赚钱"]});')['s'], ['赚钱'])
        self.assertEqual(parse_response('{"s":[]}')['s'], [])
        for bad in ['evil({"s":[]});', 'nlp_demo({s:[]});', 'nlp_demo({"s":[1]});', '<html>error</html>']:
            with self.assertRaises(ValueError):
                parse_response(bad)

    def test_html_input_escaped(self):
        output = highlight('<script>alert(1)</script>赚钱')
        self.assertNotIn('<script>', output)
        self.assertIn('&lt;script&gt;', output)
        self.assertIn('<mark', output)


if __name__ == '__main__':
    unittest.main()
