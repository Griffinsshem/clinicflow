import { cx } from "@/lib/utils";

const TINTS = [
  "bg-accent-soft text-accent",
  "bg-ochre-soft text-ochre",
  "bg-[#eef1f5] text-[#4a5a6b]", 
  "bg-[#f0eef5] text-[#5a4f6b]", 
  "bg-[#eef3f0] text-[#3f6355]", 
] as const;

function tintFor(name: string): string {
  let total = 0;
  for (let i = 0; i < name.length; i++) total += name.charCodeAt(i);
  return TINTS[total % TINTS.length];
}

function initialsFor(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export function Avatar({
  name,
  size = "md",
  className,
}: {
  name: string;
  size?: "sm" | "md";
  className?: string;
}) {
  return (
    <span
      aria-hidden="true"
      className={cx(
        "inline-flex shrink-0 items-center justify-center rounded-full font-medium",
        size === "sm" ? "h-7 w-7 text-xs" : "h-8 w-8 text-sm",
        tintFor(name),
        className,
      )}
    >
      {initialsFor(name)}
    </span>
  );
}
