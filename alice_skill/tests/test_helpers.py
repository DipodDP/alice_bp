from django.test import TestCase
from alice_skill.helpers import replace_latin_homoglyphs


class TestHelpers(TestCase):
    def test_replace_latin_homoglyphs(self):
        self.assertEqual(replace_latin_homoglyphs('cyrillic'), 'суrilliс')
        self.assertEqual(replace_latin_homoglyphs('aepocx'), 'аеросх')
        self.assertEqual(replace_latin_homoglyphs('привет'), 'привет')
        self.assertEqual(replace_latin_homoglyphs(''), '')
        self.assertEqual(replace_latin_homoglyphs('hello world'), 'hеllо wоrld')
        self.assertEqual(replace_latin_homoglyphs('a b c d e f'), 'а b с d е f')
