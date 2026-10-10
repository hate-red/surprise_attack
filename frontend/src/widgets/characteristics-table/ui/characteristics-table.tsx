import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/shared/ui/card";
import { Badge } from "@/shared/ui/badge";

export function CharacteristicsTable() {
  return (
    <Card className="border-border/60 shadow-sm">
      <CardHeader className="pb-3 flex flex-row items-center justify-between space-y-0 border-b">
        <div>
          <CardTitle className="text-base font-semibold">
            Унифицированные характеристики
          </CardTitle>
          <CardDescription className="text-xs mt-0.5">
            Результат извлечения и стандартизации значений
          </CardDescription>
        </div>
        <Badge
          variant="secondary"
          className="bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
        >
          5 найдено
        </Badge>
      </CardHeader>
      <CardContent className="p-0">
        <div className="w-full overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-slate-900/50 text-muted-foreground border-b border-border/60 font-medium">
              <tr>
                <th className="py-2.5 px-4">ИСХОДНЫЙ ТЕКСТ</th>
                <th className="py-2.5 px-4">ХАРАКТЕРИСТИКА</th>
                <th className="py-2.5 px-4">СТАНДАРТНОЕ ЗНАЧЕНИЕ</th>
                <th className="py-2.5 px-4 text-right">СТАТУС</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/40">
              <tr>
                <td className="py-3 px-4 font-mono text-slate-600 dark:text-slate-400">
                  "светодиодный"
                </td>
                <td className="py-3 px-4 font-medium">Тип источника света</td>
                <td className="py-3 px-4">Светодиодный (LED)</td>
                <td className="py-3 px-4 text-right">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-200/50">
                    Сопоставлено
                  </span>
                </td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-mono text-slate-600 dark:text-slate-400">
                  "36Вт"
                </td>
                <td className="py-3 px-4 font-medium">Мощность</td>
                <td className="py-3 px-4">36 Вт</td>
                <td className="py-3 px-4 text-right">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-200/50">
                    Сопоставлено
                  </span>
                </td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-mono text-slate-600 dark:text-slate-400">
                  "220V"
                </td>
                <td className="py-3 px-4 font-medium">
                  Номинальное напряжение
                </td>
                <td className="py-3 px-4">220 В</td>
                <td className="py-3 px-4 text-right">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-400 border border-red-200/50">
                    Требует проверки
                  </span>
                </td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-mono text-slate-600 dark:text-slate-400">
                  "аллюминий"
                </td>
                <td className="py-3 px-4 font-medium">Материал корпуса</td>
                <td className="py-3 px-4">Алюминий</td>
                <td className="py-3 px-4 text-right">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400 border border-amber-200/50">
                    Исправлена опечатка
                  </span>
                </td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-mono text-slate-600 dark:text-slate-400">
                  "IP20"
                </td>
                <td className="py-3 px-4 font-medium">Степень защиты</td>
                <td className="py-3 px-4">IP20</td>
                <td className="py-3 px-4 text-right">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-200/50">
                    Сопоставлено
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
