"use client";

import Image from "next/image";
import { useEffect, useState } from "react";
import { useTheme } from "next-themes";

type ThemeLogoProps = {
  alt?: string;
  className?: string;
  height: number;
  width: number;
};

export default function ThemeLogo({
  alt = "HaqDesk AI",
  className,
  height,
  width,
}: ThemeLogoProps) {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const src =
    mounted && resolvedTheme === "dark"
      ? "/images/Haqdesk_AI_Dark.png"
      : "/images/Haqdesk_AI_Light.png";

  return (
    <Image
      src={src}
      alt={alt}
      width={width}
      height={height}
      className={className}
    />
  );
}
