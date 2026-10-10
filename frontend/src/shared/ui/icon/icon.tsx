import { iconPaths, type IconName } from "./icon-paths";

export type { IconName };

type IconProps = {
  name: IconName;
  size?: number;
};

export function Icon({ name, size = 20 }: IconProps) {
  return (
    <svg
      aria-hidden="true"
      className="shrink-0"
      fill="none"
      height={size}
      viewBox="0 0 24 24"
      width={size}
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.8"
    >
      {iconPaths[name]}
    </svg>
  );
}
