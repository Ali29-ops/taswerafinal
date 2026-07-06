import Image from "next/image";
import Link from "next/link";
import { cn } from "@/lib/utils";

interface LogoProps {
  className?: string;
  height?: number;
  href?: string;
}

export function Logo({ className, height = 36, href }: LogoProps) {
  const img = (
    <Image
      src="/taswera-logo.jpg"
      alt="TASWERA"
      width={height}
      height={height}
      className={cn("block shrink-0 rounded-sm object-contain", className)}
      style={{ width: height, height }}
      priority
    />
  );

  if (href) {
    return (
      <Link href={href} className="inline-flex shrink-0 items-center" aria-label="TASWERA home">
        {img}
      </Link>
    );
  }

  return img;
}
