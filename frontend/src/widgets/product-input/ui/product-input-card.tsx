"use client";

import { useState } from "react";
import {
  Sparkles,
  AlertTriangle,
  Info,
  FileText,
  ArrowRight,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Textarea } from "@/shared/ui/textarea";
import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";

export function ProductInputCard() {
  const [inputText, setInputText] = useState(
    "Светильник светодиодный офисный, встраиваемый, 36Вт, 220В, 4000К, корпус аллюминий, белый, IP20.",
  );

  return (
    <div className="flex flex-col gap-6">
      {/* Форма ввода с акцентом */}
      <Card className="border-border/60 shadow-md ring-1 ring-blue-500/20 bg-gradient-to-b from-blue-50/30 to-transparent dark:from-blue-950/10 dark:to-transparent">
        <CardHeader className="pb-3 flex flex-row items-center justify-between space-y-0">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400">
              <FileText className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-base font-semibold">
                Описание товара
              </CardTitle>
              <p className="text-xs text-muted-foreground mt-0.5">
                В свободной форме или из ТЗ
              </p>
            </div>
          </div>
          <Badge
            variant="default"
            className="bg-blue-600 hover:bg-blue-700 text-white text-xs"
          >
            Шаг 1
          </Badge>
        </CardHeader>
        <CardContent className="space-y-4 pt-2">
          <div className="relative">
            <Textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Введите наименование и характеристики товара..."
              // Увеличили высоту до min-h-[220px] и сделали рамку заметнее
              className="min-h-[220px] text-sm resize-none pr-4 pb-8 border-blue-200 dark:border-blue-900/50 focus-visible:ring-blue-500  backdrop-blur-sm shadow-inner "
            />
            <div className="absolute bottom-3 left-3 text-[11px] text-muted-foreground font-medium">
              Символов: {inputText.length} / 2 000
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-1">
            <span className="text-xs text-muted-foreground flex items-center gap-1.5">
              <Info className="h-3.5 w-3.5 text-blue-500 shrink-0" />
              Нейросеть автоматически исправит опечатки
            </span>
            <Button className="w-full sm:w-auto  px-6 h-11">
              <Sparkles className="mr-2 h-4 w-4" />
              Начать анализ
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Блок проверки данных */}
      <Card className="border-amber-200/60 bg-amber-50/20 dark:bg-amber-950/10 shadow-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-600" />
              <CardTitle className="text-sm font-semibold">
                Проверка данных
              </CardTitle>
            </div>
            <Badge
              variant="outline"
              className="bg-red-50 text-red-700 border-red-200 text-[10px]"
            >
              Нужно действие
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Обнаружено 1 несоответствие и 1 автоисправление
          </p>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="p-3 rounded-lg bg-white dark:bg-slate-900 border border-red-100 dark:border-red-900/50 space-y-2">
            <p className="text-xs font-semibold text-red-600 dark:text-red-400">
              ⚠️ Напряжение противоречит категории
            </p>
            <p className="text-[11px] text-muted-foreground leading-relaxed">
              Значение «220V» не используется для выбранной категории
              встраиваемых светильников. Проверьте тип питания.
            </p>
            <div className="flex items-center gap-2 pt-1">
              <select className="flex-1 text-xs bg-slate-50 dark:bg-slate-800 border rounded px-2 py-1.5 outline-none">
                <option>220 В — сетевое питание</option>
              </select>
              <Button size="sm" className="h-7 text-xs bg-[#1e293b] text-white">
                Применить
              </Button>
            </div>
          </div>

          <div className="p-3 rounded-lg bg-white dark:bg-slate-900 border border-amber-100 dark:border-amber-900/50 space-y-1">
            <p className="text-xs font-semibold text-amber-700 dark:text-amber-400 flex items-center gap-1.5">
              <Info className="h-3.5 w-3.5" /> Исправлена опечатка
            </p>
            <p className="text-[11px] text-muted-foreground">
              «аллюминий» → «алюминий». Изменение применено автоматически.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
