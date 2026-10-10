import { cn } from "@/shared/lib/cn";
import { Icon, type IconName } from "@/shared/ui/icon/icon";

type IconBoxProps = {
  name: IconName;
  iconSize: number;
  className?: string;
};

export function IconBox({ name, iconSize, className }: IconBoxProps) {
  return (
    <span className={cn("grid shrink-0 place-items-center", className)}>
      <Icon name={name} size={iconSize} />
    </span>
  );
}
