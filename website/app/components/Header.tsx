'use client';

import Link from "next/link";
import AlphaBadge from "./AlphaBadge";
import ThemeToggle from "./ThemeToggle";

interface HeaderProps {
  currentPage?: 'home' | 'installation' | 'integration' | 'download';
}

export default function Header({ currentPage = 'home' }: HeaderProps) {
  const navLinkClass = (page: string) =>
    currentPage === page
      ? "font-semibold text-zinc-900 dark:text-zinc-50"
      : "text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-50";

  return (
    <header className="border-b border-zinc-200 dark:border-zinc-800">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
        <Link
          href="/"
          className="flex items-center text-2xl font-bold text-zinc-900 dark:text-zinc-50"
        >
          AutoPR Engine
          <AlphaBadge />
        </Link>
        <div className="flex items-center gap-6">
          <Link href="/installation" className={navLinkClass('installation')}>
            Installation
          </Link>
          <Link href="/integration" className={navLinkClass('integration')}>
            Integration
          </Link>
          <Link href="/download" className={navLinkClass('download')}>
            Download
          </Link>
          <a
            href="https://github.com/JustAGhosT/autopr-engine"
            target="_blank"
            rel="noopener noreferrer"
            className="text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-50"
          >
            GitHub
          </a>
          <ThemeToggle />
        </div>
      </nav>
    </header>
  );
}
