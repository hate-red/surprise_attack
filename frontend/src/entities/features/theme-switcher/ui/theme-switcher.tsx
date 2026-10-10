"use client";

import { Button } from "@/shared/ui/button";
import { Icon } from "@/shared/ui/icon/icon";
import { useTheme } from "../model/use-theme";

export function ThemeSwitcher() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";
  const label = isDark ? "Включить светлую тему" : "Включить темную тему";

  return (
    <Button
      aria-label={label}
      className="size-8 rounded-lg border border-border bg-muted text-muted-foreground hover:text-primary"
      onClick={toggleTheme}
      size="none"
      title={label}
      variant="bare"
    >
      <Icon name={isDark ? "sun" : "moon"} size={17} />
    </Button>
  );
}
