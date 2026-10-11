"""Сценарии на реальном справочнике КТРУ (нужна БД с загруженными данными).

Если справочник не загружен, тесты пропускаются.
Запуск: python -m unittest tests.test_scenarios -v
"""
import time
import unittest

from app.database import engine
from app.schemas.positions import CharacteristicOverride, ParseRequest
from app.services.ktru_index import load_index
from app.services.product_service import get_parsing_service


class ScenarioTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        try:
            index = await load_index()
        except Exception as exc:  # БД недоступна
            await engine.dispose()
            self.skipTest(f'БД недоступна: {exc}')
        if not index.positions:
            self.skipTest('Справочник КТРУ не загружен')
        self.service = get_parsing_service()

    async def asyncTearDown(self):
        # каждый тест получает свой event loop — соединения пула к нему не переносятся
        await engine.dispose()

    async def analyze(self, text, request=None):
        started = time.perf_counter()
        result = await self.service.get_validate(text, request)
        self.assertLess(time.perf_counter() - started, 5.0, 'ответ дольше 5 секунд')
        return result

    async def test_scenario_1_need_more_info(self):
        r = await self.analyze('Стул ученический')
        self.assertEqual(r.status, 'need_more_info')
        self.assertIsNone(r.ktru_code)
        self.assertIn('Тип каркаса', [s.name for s in r.suggestions])
        self.assertGreater(r.candidates_total, 1)

    async def test_scenario_2_resolved(self):
        r = await self.analyze('Стул ученический деревянный с регулировкой по высоте')
        self.assertEqual(r.status, 'resolved')
        self.assertEqual(r.ktru_code, '31.01.11.150-00000006')
        counts = [s.count_after for s in r.stages]
        self.assertEqual(counts, sorted(counts, reverse=True), 'этапы должны только сужать множество')

    async def test_user_confirmation_narrows(self):
        request = ParseRequest(overrides=[
            CharacteristicOverride(name='Тип каркаса', value='Деревянный'),
            CharacteristicOverride(name='Регулировка по высоте', value='нет'),
        ])
        r = await self.analyze('Стул ученический', request)
        self.assertEqual(r.status, 'resolved')
        self.assertEqual(r.ktru_code, '31.01.11.150-00000005')

    async def test_scenario_3_unrecognized_characteristic(self):
        r = await self.analyze('Шкаф для одежды металлический, вибростойкость: высокая')
        self.assertIn('unrecognized_characteristic', [m.code for m in r.messages])

    async def test_scenario_4_name_not_found(self):
        r = await self.analyze('абракадабра пупыр')
        self.assertEqual(r.status, 'name_not_found')
        self.assertIsNone(r.ktru_code)
        self.assertEqual(r.candidates, [])

    async def test_units_and_ranges(self):
        r = await self.analyze('молоток столярный масса 0,5 кг длина рукоятки 32 см')
        self.assertEqual(r.ktru_code, '25.73.30.141-00000010')
        handle = next(c for c in r.characteristics if c.name == 'Длина рукоятки')
        self.assertEqual(handle.normalized, '320')
        self.assertEqual(handle.matched_range, '≥ 300 и < 400 Миллиметр')

    async def test_invalid_unit_not_added(self):
        r = await self.analyze('Молоток слесарный длина рукоятки 3 кг')
        handle = next(c for c in r.characteristics if c.name == 'Длина рукоятки')
        self.assertEqual(handle.status, 'unit_mismatch')
        self.assertFalse(handle.in_specification)

    async def test_typos(self):
        r = await self.analyze('Стулл ученичский деревяный')
        self.assertEqual(r.corrected_query, 'Стул ученический деревянный')
        self.assertEqual(r.product.name, 'Стул ученический')


if __name__ == '__main__':
    unittest.main()
