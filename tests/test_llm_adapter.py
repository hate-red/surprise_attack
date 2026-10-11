"""LLM (Qwen) -> конвейер: разбор ответа модели и выбор лучшего разбора.

Модель не нужна: её ответы подменяются. Сценарные тесты требуют БД со справочником.
Запуск: python -m unittest tests.test_llm_adapter -v
"""
import asyncio
import json
import os
import time
import unittest

from app.database import engine
from app.schemas.positions import ParseRequest
from app.services import get_evals, llm_adapter
from app.services.ktru_index import load_index
from app.services.llm_adapter import build_description, parse_llm_json
from app.services.product_service import get_parsing_service


class ParseJsonTest(unittest.TestCase):
    def test_plain_fenced_and_wrapped(self):
        self.assertEqual(parse_llm_json('{"a": "1"}'), {'a': '1'})
        self.assertEqual(parse_llm_json('```json\n{"a": "1"}\n```'), {'a': '1'})
        self.assertEqual(parse_llm_json('Вот ответ: {"a": {"b": 2}} — готово'), {'a': {'b': 2}})

    def test_broken_answers(self):
        self.assertEqual(parse_llm_json('{"a": "1",}'), {'a': '1'})       # висячая запятая
        self.assertEqual(parse_llm_json('{"a": "1", "b": "2"'), {'a': '1', 'b': '2'})  # оборвался
        self.assertEqual(parse_llm_json('не знаю'), {})
        self.assertEqual(parse_llm_json(None), {})
        self.assertEqual(parse_llm_json('[1, 2]'), {})


class BuildDescriptionTest(unittest.TestCase):
    def test_pairs_are_separated(self):
        d = build_description('{"name": "Молоток столярный"}', '{"масса": "0,5 кг", "длина рукоятки": "320 мм"}')
        self.assertEqual(d.text, 'Молоток столярный; масса: 0,5 кг; длина рукоятки: 320 мм')

    def test_value_types(self):
        d = build_description(
            {'name': 'Стул ученический'},
            {'регулировка по высоте': False, 'подлокотники': 'есть', 'ростовая группа': 4,
             'цвет': ['белый', 'синий'], 'вес': 1.5, 'модель': 'X-1', 'материал': None})
        self.assertEqual(d.text, 'Стул ученический; без регулировка по высоте; подлокотники; '
                                 'ростовая группа: 4; цвет: белый и синий; вес: 1.5')

    def test_null_name_and_empty(self):
        self.assertEqual(build_description('{"name": null}', '{"тип каркаса": "деревянный"}').text,
                         'тип каркаса: деревянный')
        self.assertIsNone(build_description('{"name": null}', '{}'))
        self.assertIsNone(build_description('мусор', 'мусор'))

    def test_grounding_drops_invented_values(self):
        d = build_description({'name': 'Стул ученический'},
                              {'тип каркаса': 'деревянный', 'регулировка по высоте': 'есть', 'ростовая группа': '4'},
                              source_text='стул ученический деревянный')
        self.assertEqual(d.text, 'Стул ученический; тип каркаса: деревянный')
        d = build_description({'name': 'Кресло руководителя'}, {}, source_text='стул ученический деревянный')
        self.assertIsNone(d)

    def test_grounding_keeps_other_word_forms(self):
        d = build_description({'name': 'Стул'}, {'материал': 'дерево', 'ростовая группа': '4'},
                              source_text='стул из дерева, ростовая группа 4')
        self.assertEqual(d.text, 'Стул; материал: дерево; ростовая группа: 4')


class LlmScenarioTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        try:
            index = await load_index()
        except Exception as exc:  # БД недоступна
            await engine.dispose()
            self.skipTest(f'БД недоступна: {exc}')
        if not index.positions:
            self.skipTest('Справочник КТРУ не загружен')
        self.service = get_parsing_service()
        os.environ['LLM_ENABLED'] = '1'
        llm_adapter._cache.clear()
        llm_adapter._pending.clear()
        llm_adapter._disabled_reason = None
        self._generate = get_evals.generate
        self._timeout = llm_adapter.LLM_TIMEOUT_S

    async def asyncTearDown(self):
        get_evals.generate = self._generate
        llm_adapter.LLM_TIMEOUT_S = self._timeout
        os.environ['LLM_ENABLED'] = '0'
        await engine.dispose()

    def fake(self, name, chars, delay=0.0):
        def generate(_text):
            time.sleep(delay)
            return json.dumps(name, ensure_ascii=False), json.dumps(chars, ensure_ascii=False)
        get_evals.generate = generate

    async def test_invented_values_do_not_resolve_code(self):
        self.fake({'name': 'Стул ученический'},
                  {'тип каркаса': 'деревянный', 'регулировка по высоте': 'есть', 'ростовая группа': '4'})
        r = await self.service.get_validate('стул ученический деревянный', ParseRequest())
        self.assertEqual(r.status, 'need_more_info')
        self.assertIsNone(r.ktru_code)

    async def test_boolean_no_from_llm(self):
        text = 'стул ученический деревянный ростовая группа 4 без регулировки по высоте'
        self.fake({'name': 'Стул ученический'},
                  {'тип каркаса': 'деревянный', 'ростовая группа': 4, 'регулировка по высоте': False})
        r = await self.service.get_validate(text, ParseRequest())
        self.assertEqual(r.ktru_code, '31.01.11.150-00000005')
        self.assertIn('без регулировка по высоте', r.llm_description)

    async def test_noisy_description_uses_llm_text(self):
        text = ('Seventeen Мешок для обуви Seventeen Kids SKDB-UT6-883 Kinderline International Ltd. китай '
                'бренд Seventeen вес 0.00000 кг высота упаковки 20 мм материал полиэстер цвет синий')
        self.fake({'name': 'Мешок для обуви Seventeen Kids', 'model': 'SKDB-UT6-883'},
                  {'бренд': 'Seventeen', 'вес': '0.00000 кг', 'высота упаковки': '20 мм',
                   'материал': 'полиэстер', 'цвет': 'синий'})
        r = await self.service.get_validate(text, ParseRequest())
        self.assertEqual(r.analysis_source, 'llm')
        self.assertEqual(r.query, r.llm_description)
        self.assertEqual(r.original_query, text)
        for c in r.characteristics:  # подсветка относится к разобранному тексту
            if c.start is not None:
                self.assertLessEqual(c.end, len(r.query))

    async def test_model_failure_and_timeout_fall_back_to_text(self):
        def broken(_text):
            raise RuntimeError('llama упала')
        get_evals.generate = broken
        r = await self.service.get_validate('молоток столярный', ParseRequest())
        self.assertEqual(r.analysis_source, 'text')
        self.assertIsNone(r.llm_description)

        llm_adapter.LLM_TIMEOUT_S = 0.2
        self.fake({'name': 'Молоток столярный'}, {}, delay=0.6)
        started = time.perf_counter()
        r = await self.service.get_validate('молоток слесарный', ParseRequest())
        self.assertLess(time.perf_counter() - started, 0.6 + 0.5)
        self.assertIsNone(r.llm_description)
        await asyncio.sleep(0.6)  # ответ модели дошёл и сохранён в кэш для следующего запроса
        r = await self.service.get_validate('молоток слесарный', ParseRequest())
        self.assertEqual(r.llm_description, 'Молоток столярный')


if __name__ == '__main__':
    unittest.main()
