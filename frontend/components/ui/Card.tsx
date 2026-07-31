import { HTMLAttributes } from "react";

export default function Card({ className = "", ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={`ds-card ${className}`} {...props} />;
}
