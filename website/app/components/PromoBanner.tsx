'use client';

export default function PromoBanner() {
  return (
    <div className="bg-gradient-to-r from-blue-600 to-purple-600 py-3 text-center">
      <div className="mx-auto max-w-7xl px-6">
        <p className="text-sm font-semibold text-white">
          <span className="mr-2">⚡ Limited Time Only:</span>
          <a
            href="https://app.autopr.io"
            target="_blank"
            rel="noopener noreferrer"
            className="underline hover:no-underline"
          >
            Use our deployed AutoPR instance
          </a>
          <span className="ml-2">→ Try it now!</span>
        </p>
      </div>
    </div>
  );
}

