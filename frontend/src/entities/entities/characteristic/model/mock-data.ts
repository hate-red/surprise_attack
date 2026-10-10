import type { Characteristic } from "./types";

export const characteristics: Characteristic[] = [
  { title: "Диагональ экрана", original: "15.6 дюймов", normalized: "15,6", unit: "Дюйм", confidence: 99 },
  { title: "Тип процессора", original: "Intel Core i5", normalized: "Intel Core i5", unit: "—", confidence: 98 },
  { title: "Объем оперативной памяти", original: "16 гб", normalized: "16", unit: "Гигабайт", confidence: 97 },
  { title: "Объем SSD-накопителя", original: "SSD 512 гб", normalized: "512", unit: "Гигабайт", confidence: 96 },
  { title: "Вес", original: "до 1.8 кг", normalized: "≤ 1,8", unit: "Килограмм", confidence: 94 },
  { title: "Цвет корпуса", original: "серебристый", normalized: "Серебристый", unit: "—", confidence: 91 },
];
