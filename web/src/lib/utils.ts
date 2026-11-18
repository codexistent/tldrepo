import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function parseRepo(input: string) {
  if (!input.length) return null;

  if (input.endsWith("/")) {
    input.slice(0, -1);
  }

  const parts: string[] = input.split("/");

  if (parts.length < 2) return null;
  return {
    owner: parts[parts.length - 2],
    repo: parts[parts.length - 1],
  };
}
