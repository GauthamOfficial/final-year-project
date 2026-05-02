"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Native-select-backed Select primitive. Same import path as the shadcn Radix
 * variant — drop-in replaceable later when the project takes the dependency on
 * `@radix-ui/react-select`.
 */
interface SelectProps {
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  children: React.ReactNode;
  className?: string;
  placeholder?: string;
}

export function Select({
  value,
  defaultValue,
  onValueChange,
  children,
  className,
  placeholder,
}: SelectProps) {
  return (
    <select
      value={value ?? defaultValue ?? ""}
      onChange={(e) => onValueChange?.(e.target.value)}
      className={cn(
        "flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
    >
      {placeholder !== undefined && (
        <option value="" disabled>
          {placeholder}
        </option>
      )}
      {children}
    </select>
  );
}

interface SelectItemProps {
  value: string;
  children: React.ReactNode;
}

export function SelectItem({ value, children }: SelectItemProps) {
  return <option value={value}>{children}</option>;
}
