import Image from "next/image";
import Link from "next/link";
import { cn } from "@/lib/utils";

type LogoSize = "default" | "footer";

/** `white` = monochrome white (for dark footer / jade backgrounds); does not stretch raster. */
type LogoTone = "default" | "white";

/**
 * Official mark from `public/lg-logo.png`.
 * Fixed-height frame + `object-contain` keeps aspect ratio; logo is never stretched.
 */
export function Logo({
  href = "/",
  className,
  invert = false,
  size = "default",
  tone = "default",
}: {
  href?: string | null;
  className?: string;
  invert?: boolean;
  size?: LogoSize;
  tone?: LogoTone;
}) {
  const lightWordmark = tone === "white" || invert;

  const imgClass =
    size === "footer"
      ? "h-9 max-h-9 w-auto max-w-[min(120px,calc(35vw))] shrink-0 sm:h-10 sm:max-h-10 sm:max-w-[min(140px,28vw)]"
      : "h-8 max-h-8 w-auto max-w-[min(110px,32vw)] shrink-0 sm:h-9 sm:max-h-9 sm:max-w-[min(128px,30vw)]";

  const inner = (
    <span
      className={cn(
        "isolate inline-flex shrink-0 items-center justify-start gap-2.5",
        className
      )}
    >
      <Image
        src="/lg-logo.png"
        alt=""
        aria-hidden
        width={800}
        height={200}
        sizes={
          size === "footer"
            ? "(max-width: 640px) 112px, 140px"
            : "(max-width: 640px) 104px, 128px"
        }
        className={cn(
          "object-contain object-left",
          imgClass,
          tone === "white" && "brightness-0 invert",
          invert && tone !== "white" && "drop-shadow-[0_2px_8px_rgba(0,0,0,0.35)]"
        )}
        priority={size !== "footer"}
      />
      <span
        className={cn(
          "display font-medium leading-none tracking-tightest whitespace-nowrap",
          size === "footer" ? "text-lg sm:text-xl" : "text-[1.1rem] sm:text-[1.25rem]",
          lightWordmark ? "text-white" : "text-ink-900",
          invert && tone !== "white" &&
            "drop-shadow-[0_1px_2px_rgba(0,0,0,0.45)]"
        )}
      >
        LankaGuide
      </span>
    </span>
  );

  if (!href) return inner;
  return (
    <Link
      href={href}
      className={cn(
        "group inline-flex shrink-0 items-center outline-none ring-offset-transparent focus-visible:ring-2 focus-visible:ring-offset-2",
        tone === "white"
          ? "focus-visible:ring-saffron-300 ring-offset-jade-900"
          : "focus-visible:ring-jade-500"
      )}
    >
      {inner}
    </Link>
  );
}
