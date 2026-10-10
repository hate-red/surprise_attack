import { Icon } from "@/shared/ui/icon/icon";

export function Toast({ message }: { message: string }) {
  return (
    <div
      className="fixed right-6 top-20 z-50 flex items-center gap-3 rounded-xl bg-secondary px-4 py-3 text-sm font-medium text-white shadow-xl max-md:inset-x-3.5 max-md:top-[72px]"
      role="status"
    >
      <span className="grid size-6 place-items-center rounded-full bg-emerald-500">
        <Icon name="check" size={15} />
      </span>
      {message}
    </div>
  );
}
