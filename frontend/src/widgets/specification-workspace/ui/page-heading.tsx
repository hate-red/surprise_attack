import { Button } from "@/shared/ui/button";
import { Icon } from "@/shared/ui/icon/icon";

type PageHeadingProps = {
  onSaveDraft: () => void;
  onCreateNew: () => void;
};

export function PageHeading({ onSaveDraft, onCreateNew }: PageHeadingProps) {
  return (
    <div className="mb-6 flex items-end justify-between max-md:mb-[18px] max-md:block">
      <div>
        <div className="mb-2 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-primary">
          <span className="h-px w-5 bg-primary" />
          Умное создание спецификации
        </div>
        <h1 className="text-[28px] font-bold tracking-[-0.035em] text-foreground max-md:text-[23px] max-md:leading-[1.2]">
          Новая спецификация товара
        </h1>
        <p className="mt-1.5 text-[13px] text-muted-foreground max-md:max-w-[330px] max-md:text-[11px] max-md:leading-[1.6]">
          Опишите товар свободным текстом — система выделит и унифицирует характеристики
        </p>
      </div>
      <div className="flex items-center gap-2 max-md:mt-4">
        <Button className="max-md:flex-1" onClick={onSaveDraft} variant="outline">
          Сохранить черновик
        </Button>
        <Button className="max-md:flex-1" onClick={onCreateNew}>
          <Icon name="plus" size={16} />
          Новая СТЕ
        </Button>
      </div>
    </div>
  );
}
