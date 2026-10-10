export type KtruStep = {
  code: string;
  title: string;
  categoriesCount: string;
};

export const ktruSteps: KtruStep[] = [
  { code: "26", title: "Оборудование компьютерное", categoriesCount: "1 842 категории" },
  { code: "26.20", title: "Компьютеры и периферия", categoriesCount: "216 категорий" },
  { code: "26.20.11", title: "Портативные компьютеры", categoriesCount: "12 категорий" },
];

export const recommendedKtru = {
  code: "26.20.11.110-00000023",
  description: "Компьютеры портативные массой не более 10 кг",
  match: 94,
};
