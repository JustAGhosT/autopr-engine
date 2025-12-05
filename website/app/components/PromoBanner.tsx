'use client';

export default function PromoBanner() {
  return (
    <div className="bg-gradient-to-r from-amber-500 to-orange-500 py-3 text-center">
      <div className="mx-auto max-w-7xl px-6">
        <p className="text-sm font-semibold text-white">
          <span className="mr-2">🚧 Alpha Preview:</span>
          AutoPR Engine is currently in alpha. Features may change and some functionality may be limited.
          <a
            href="https://github.com/JustAGhosT/autopr-engine/discussions"
            target="_blank"
            rel="noopener noreferrer"
            className="ml-2 underline hover:no-underline"
          >
            Share feedback →
          </a>
        </p>
      </div>
    </div>
  );
}

