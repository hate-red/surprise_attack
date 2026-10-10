import { characteristicGridClass } from "./characteristic-grid";

export function CharacteristicTableHead() {
  return (
    <div
      className={`${characteristicGridClass} bg-background px-5 py-2.5 text-[9px] font-bold uppercase tracking-[0.07em] text-muted-foreground max-md:min-w-[680px]`}
    >
      <span>Характеристика</span>
      <span>Из описания</span>
      <span>Нормализовано</span>
      <span>Ед. измерения</span>
      <span />
    </div>
  );
}
