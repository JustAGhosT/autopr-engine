import Link from "next/link";
import AlphaBadge from "../components/AlphaBadge";

export default function Download() {
  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-zinc-50 to-white dark:from-black dark:to-zinc-950">
      <header className="border-b border-zinc-200 dark:border-zinc-800">
        <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <Link
            href="/"
            className="flex items-center text-2xl font-bold text-zinc-900 dark:text-zinc-50"
          >
            AutoPR Engine
            <AlphaBadge />
          </Link>
          <div className="flex gap-6">
            <Link
              href="/installation"
              className="text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-50"
            >
              Installation
            </Link>
            <Link
              href="/integration"
              className="text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-50"
            >
              Integration
            </Link>
            <Link
              href="/download"
              className="font-semibold text-zinc-900 dark:text-zinc-50"
            >
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
          </div>
        </nav>
      </header>

      <main className="flex-1">
        <section className="mx-auto max-w-4xl px-6 py-24">
          <h1 className="mb-6 text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
            Download AutoPR Engine
          </h1>
          <p className="mb-12 text-xl text-zinc-600 dark:text-zinc-400">
            Choose your preferred download method and platform.
          </p>

          <div className="space-y-6">
            {/* GitHub Releases */}
            <div className="rounded-lg border border-zinc-200 p-6 dark:border-zinc-800">
              <h2 className="mb-4 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
                GitHub Releases
              </h2>
              <p className="mb-4 text-zinc-600 dark:text-zinc-400">
                Download the latest stable release from GitHub:
              </p>
              <a
                href="https://github.com/JustAGhosT/autopr-engine/releases/latest"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block rounded-lg bg-zinc-900 px-6 py-3 font-semibold text-white transition-colors hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
              >
                View Releases →
              </a>
            </div>

            {/* PyPI */}
            <div className="rounded-lg border border-zinc-200 p-6 dark:border-zinc-800">
              <h2 className="mb-4 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
                PyPI Package
              </h2>
              <p className="mb-4 text-zinc-600 dark:text-zinc-400">
                Install from Python Package Index:
              </p>
              <div className="rounded-lg bg-zinc-900 p-4 font-mono text-sm text-zinc-50 dark:bg-zinc-800">
                <code>pip install autopr-engine</code>
              </div>
              <a
                href="https://pypi.org/project/autopr-engine/"
                target="_blank"
                rel="noopener noreferrer"
                className="mt-4 inline-block text-blue-600 hover:underline dark:text-blue-400"
              >
                View on PyPI →
              </a>
            </div>

            {/* Docker Hub */}
            <div className="rounded-lg border border-zinc-200 p-6 dark:border-zinc-800">
              <h2 className="mb-4 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
                Docker Image
              </h2>
              <p className="mb-4 text-zinc-600 dark:text-zinc-400">
                Pull from GitHub Container Registry:
              </p>
              <div className="rounded-lg bg-zinc-900 p-4 font-mono text-sm text-zinc-50 dark:bg-zinc-800">
                <code>docker pull ghcr.io/justaghost/autopr-engine:latest</code>
              </div>
              <a
                href="https://github.com/JustAGhosT/autopr-engine/pkgs/container/autopr-engine"
                target="_blank"
                rel="noopener noreferrer"
                className="mt-4 inline-block text-blue-600 hover:underline dark:text-blue-400"
              >
                View Container Registry →
              </a>
            </div>

            {/* Source Code */}
            <div className="rounded-lg border border-zinc-200 p-6 dark:border-zinc-800">
              <h2 className="mb-4 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
                Source Code
              </h2>
              <p className="mb-4 text-zinc-600 dark:text-zinc-400">
                Clone the repository to build from source:
              </p>
              <div className="rounded-lg bg-zinc-900 p-4 font-mono text-sm text-zinc-50 dark:bg-zinc-800">
                <code>git clone https://github.com/JustAGhosT/autopr-engine.git</code>
              </div>
            </div>
          </div>

          <div className="mt-12 rounded-lg bg-zinc-100 p-6 dark:bg-zinc-900">
            <h3 className="mb-2 text-lg font-semibold text-zinc-900 dark:text-zinc-50">
              System Requirements
            </h3>
            <ul className="list-disc space-y-1 pl-6 text-zinc-600 dark:text-zinc-400">
              <li>Python 3.8+ (for Python installation)</li>
              <li>Docker (for containerized deployment)</li>
              <li>Git (for source code installation)</li>
              <li>GitHub account with appropriate permissions</li>
            </ul>
          </div>
        </section>
      </main>

      <footer className="border-t border-zinc-200 dark:border-zinc-800">
        <div className="mx-auto max-w-7xl px-6 py-8 text-center text-zinc-600 dark:text-zinc-400">
          <p>&copy; {new Date().getFullYear()} AutoPR Engine. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

