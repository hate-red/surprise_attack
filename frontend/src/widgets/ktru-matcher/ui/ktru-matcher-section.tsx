import { Check, AlertTriangle, ArrowRight } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/shared/ui/card";
import { Button } from "@/shared/ui/button";
import { Badge } from "@/shared/ui/badge";

export function KtruMatcherSection() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
      {/* Дерево КТРУ (span-7) */}
      <div className="md:col-span-7">
        <Card className="border-border/60 shadow-sm h-full flex flex-col">
          <CardHeader className="pb-3 border-b">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-semibold">
                Подбор кода КТРУ
              </CardTitle>
              <Badge
                variant="outline"
                className="text-emerald-600 border-emerald-200 bg-emerald-50 dark:bg-emerald-950/30 text-[11px]"
              >
                92% совпадение
              </Badge>
            </div>
            <CardDescription className="text-xs">
              Иерархия сужается по мере распознавания характеристик
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 space-y-3 flex-1 flex flex-col justify-between">
            <div className="text-[11px] text-muted-foreground flex items-center gap-1.5 mb-2">
              <span>Каталог</span> <span className="text-border">›</span>
              <span>Освещение</span> <span className="text-border">›</span>
              <span className="text-foreground font-medium">
                Светодиодные светильники
              </span>
            </div>

            <div className="space-y-2.5">
              {/* Узел 1 */}
              <div className="p-3 rounded-lg border bg-white dark:bg-slate-900 flex items-start gap-3">
                <div className="mt-0.5 bg-slate-800 text-white rounded-full p-0.5 h-4 w-4 flex items-center justify-center shrink-0">
                  <Check className="h-3 w-3" />
                </div>
                <div>
                  <p className="text-[10px] tracking-wider text-muted-foreground uppercase font-semibold">
                    Категория
                  </p>
                  <p className="text-xs font-bold">27.40</p>
                  <p className="text-[11px] text-muted-foreground">
                    Оборудование электрическое осветительное
                  </p>
                </div>
              </div>

              {/* Узел 2 */}
              <div className="p-3 rounded-lg border bg-white dark:bg-slate-900 flex items-start gap-3">
                <div className="mt-0.5 bg-slate-800 text-white rounded-full p-0.5 h-4 w-4 flex items-center justify-center shrink-0">
                  <Check className="h-3 w-3" />
                </div>
                <div>
                  <p className="text-[10px] tracking-wider text-muted-foreground uppercase font-semibold">
                    Подкатегория
                  </p>
                  <p className="text-xs font-bold">27.40.39</p>
                  <p className="text-[11px] text-muted-foreground">
                    Светильники и устройства осветительные прочие
                  </p>
                </div>
              </div>

              {/* Узел 3 */}
              <div className="p-3 rounded-lg border bg-white dark:bg-slate-900 flex items-start gap-3">
                <div className="mt-0.5 bg-slate-800 text-white rounded-full p-0.5 h-4 w-4 flex items-center justify-center shrink-0">
                  <Check className="h-3 w-3" />
                </div>
                <div>
                  <p className="text-[10px] tracking-wider text-muted-foreground uppercase font-semibold">
                    Группа
                  </p>
                  <p className="text-xs font-bold">27.40.39.110</p>
                  <p className="text-[11px] text-muted-foreground">
                    Светильники светодиодные
                  </p>
                </div>
              </div>

              {/* Код КТРУ */}
              <div className="p-3 rounded-lg border-2 border-slate-800 dark:border-slate-300 bg-slate-50 dark:bg-slate-900/80 flex items-start gap-3">
                <div className="mt-0.5 ring-4 ring-slate-200 dark:ring-slate-800 bg-slate-800 text-white rounded-full h-3 w-3 flex items-center justify-center shrink-0" />
                <div className="flex-1 flex items-center justify-between">
                  <div>
                    <p className="text-[10px] tracking-wider text-slate-700 dark:text-slate-300 uppercase font-bold">
                      Код КТРУ
                    </p>
                    <p className="text-xs font-bold text-slate-900 dark:text-slate-100">
                      27.40.39.110-00000004
                    </p>
                    <p className="text-[11px] text-muted-foreground">
                      Светильник светодиодный внутреннего освещения
                    </p>
                  </div>
                  <Badge
                    variant="outline"
                    className="text-[10px] bg-slate-200/50 text-slate-700 dark:text-slate-300 h-5"
                  >
                    Рекомендуемый
                  </Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Требуется уточнение / Радиокнопки (span-5) */}
      <div className="md:col-span-5">
        <Card className="border-border/60 shadow-sm h-full flex flex-col justify-between">
          <CardHeader className="pb-3 border-b">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-600" />
                <CardTitle className="text-sm font-semibold">
                  Требуется уточнение
                </CardTitle>
              </div>
              <Badge
                variant="outline"
                className="text-[10px] bg-amber-50 text-amber-800 border-amber-200"
              >
                Действие оператора
              </Badge>
            </div>
            <CardDescription className="text-xs mt-1">
              Несколько кодов КТРУ соответствуют описанию
            </CardDescription>
          </CardHeader>

          <CardContent className="p-4 space-y-4">
            <div>
              <p className="text-xs font-bold mb-1">
                Укажите материал рассеивателя
              </p>
              <p className="text-[11px] text-muted-foreground">
                Этот параметр разделяет два наиболее вероятных кода.
              </p>
            </div>

            <div className="grid grid-cols-3 gap-2">
              <label className="flex flex-col items-center justify-center p-3 rounded-lg border border-border/80 hover:border-slate-400 cursor-pointer text-center transition bg-white dark:bg-slate-900">
                <input type="radio" name="diffuser" className="mb-2" />
                <span className="text-[11px] font-medium leading-tight">
                  Поликарбонат
                </span>
              </label>

              <label className="flex flex-col items-center justify-center p-3 rounded-lg border border-border/80 hover:border-slate-400 cursor-pointer text-center transition bg-white dark:bg-slate-900">
                <input type="radio" name="diffuser" className="mb-2" />
                <span className="text-[11px] font-medium leading-tight">
                  Стекло
                </span>
              </label>

              <label className="flex flex-col items-center justify-center p-3 rounded-lg border border-border/80 hover:border-slate-400 cursor-pointer text-center transition bg-white dark:bg-slate-900">
                <input type="radio" name="diffuser" className="mb-2" />
                <span className="text-[11px] font-medium leading-tight">
                  Без рассеивателя
                </span>
              </label>
            </div>
          </CardContent>

          <div className="p-4 pt-0">
            <Button className="w-full bg-[#1e293b] hover:bg-[#0f172a] text-white text-xs h-10">
              Уточнить код <ArrowRight className="ml-2 h-3.5 w-3.5" />
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
