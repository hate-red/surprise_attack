"""Юнит-тесты нормализации текста, единиц измерения и разбора CSV (без БД).

Запуск: python -m unittest discover -s tests -v
"""
import unittest

from app.services.batch_service import CsvFormatError, parse_descriptions
from app.services.nlp.matching import stem_similarity
from app.services.nlp.spelling import SpellChecker, SpellingIssue, apply_corrections
from app.services.nlp.text import format_number, normalize_text, tokenize, word_stem
from app.services.nlp.units import UNITS, convert, match_unit_at, unit_from_okei


class StemmerTest(unittest.TestCase):
    def test_word_forms_share_stem(self):
        for a, b in [('стулья', 'стул'), ('дивана', 'диван'), ('кровати', 'кровать'),
                     ('молотка', 'молоток'), ('перчаток', 'перчатки'), ('мужские', 'мужской')]:
            self.assertEqual(word_stem(a), word_stem(b), (a, b))

    def test_derived_words_match_by_root(self):
        for a, b in [('кожаная', 'кожи'), ('аккумуляторная', 'аккумулятора'),
                     ('сетевая', 'сети'), ('деревянный', 'дерева'), ('зимняя', 'зима')]:
            self.assertGreater(stem_similarity(word_stem(a), word_stem(b)), 0, (a, b))

    def test_different_words_do_not_match(self):
        for a, b in [('стол', 'стул'), ('черный', 'череп'), ('дерево', 'дерн')]:
            self.assertEqual(stem_similarity(word_stem(a), word_stem(b)), 0, (a, b))


class TokenizerTest(unittest.TestCase):
    def test_offsets_preserved_and_abbreviations(self):
        text = normalize_text('Кол-во 5 шт, выс. 45см, «ЛДСП» 15,6')
        tokens = tokenize(text)
        self.assertEqual(len(text), len('Кол-во 5 шт, выс. 45см, «ЛДСП» 15,6'))
        self.assertEqual(tokens[0].norm, 'количество')
        self.assertEqual(text[tokens[0].start:tokens[0].end], 'Кол-во')
        self.assertIn('высота', [t.norm for t in tokens])
        self.assertIn('15.6', [t.norm for t in tokens if t.is_number])

    def test_format_number_uses_decimal_comma(self):
        self.assertEqual(format_number(0.5), '0,5')
        self.assertEqual(format_number(320.0), '320')


class UnitsTest(unittest.TestCase):
    def test_conversion(self):
        self.assertAlmostEqual(convert(32, UNITS['cm'], UNITS['mm']), 320)
        self.assertAlmostEqual(convert(0.5, UNITS['kg'], UNITS['g']), 500)
        self.assertIsNone(convert(3, UNITS['kg'], UNITS['mm']))

    def test_okei_names(self):
        self.assertEqual(unit_from_okei('Миллиметр').key, 'mm')
        self.assertEqual(unit_from_okei('Кубический сантиметр; миллилитр').key, 'ml')
        self.assertEqual(unit_from_okei('Дюйм (25,4 мм)').key, 'inch')

    def test_unit_in_text(self):
        text = '800 Вт, 1500 об/мин, 45см, 2 кв.м, 18 В'
        self.assertEqual(match_unit_at(text, 3).unit.key, 'w')
        self.assertEqual(match_unit_at(text, text.index('об') - 1).unit.key, 'rpm')
        self.assertEqual(match_unit_at(text, text.index('см')).unit.key, 'cm')
        self.assertEqual(match_unit_at(text, text.index('кв') - 1).unit.key, 'm2')
        weak = match_unit_at(text, text.rindex('В') - 1)
        self.assertEqual(weak.unit.key, 'v')
        self.assertTrue(weak.weak)


class SpellingTest(unittest.TestCase):
    def test_suggestions_and_corrected_text(self):
        vocabulary = {'стул': 10, 'стула': 12, 'ученический': 5, 'деревянный': 7}
        checker = SpellChecker(vocabulary, {word_stem(w) for w in vocabulary})
        self.assertEqual(checker.suggest('стулл')[0], 'стул')         # удвоенная буква
        self.assertEqual(checker.suggest('ученичский')[0], 'ученический')
        self.assertIsNone(checker.suggest('китай'))                  # общеупотребительное слово
        text = 'Стулл деревяный'
        issues = checker.check_tokens(tokenize(normalize_text(text)))
        self.assertEqual(apply_corrections(text, issues), 'Стул деревянный')
        self.assertTrue(all(isinstance(i, SpellingIssue) for i in issues))


class CsvTest(unittest.TestCase):
    def test_single_column_with_header_and_commas(self):
        data = ('Описание\n"Стул ученический, деревянный"\n'
                'Молоток масса 0,5 кг, сталь\n\nБрюки\n').encode('utf-8')
        self.assertEqual(parse_descriptions(data), [
            'Стул ученический, деревянный', 'Молоток масса 0,5 кг, сталь', 'Брюки'])

    def test_cp1251_and_semicolon(self):
        data = 'Стол письменный;\nКресло офисное;\n'.encode('cp1251')
        self.assertEqual(parse_descriptions(data), ['Стол письменный', 'Кресло офисное'])

    def test_empty(self):
        with self.assertRaises(CsvFormatError):
            parse_descriptions(b'  \n')


if __name__ == '__main__':
    unittest.main()
