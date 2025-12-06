import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Utility function for merging Tailwind CSS classes with proper precedence.
 * Combines clsx for conditional classes and tailwind-merge for deduplication.
 *
 * @example
 * cn("px-4 py-2", "px-6") // => "py-2 px-6"
 * cn("bg-red-500", isActive && "bg-blue-500") // => "bg-blue-500" if isActive
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
