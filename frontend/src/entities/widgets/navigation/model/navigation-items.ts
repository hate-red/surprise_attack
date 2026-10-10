import type { IconName } from "@/shared/ui/icon/icon";

export type NavigationItem = {
  id: string;
  label: string;
  shortLabel: string;
  icon: IconName;
};

export const navigationItems: NavigationItem[] = [
  { id: "new", label: "Новая спецификация", shortLabel: "Новая", icon: "sparkles" },
  { id: "mine", label: "Мои спецификации", shortLabel: "Мои СТЕ", icon: "catalog" },
  { id: "history", label: "История анализа", shortLabel: "История", icon: "history" },
];

export const defaultNavigationId = navigationItems[0].id;
