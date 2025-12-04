import Link from "next/link";

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-zinc-50 to-white dark:from-black dark:to-zinc-950">
      {/* Header */}
      <header className="border-b border-zinc-200 dark:border-zinc-800">
        <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="text-2xl font-bold text-zinc-900 dark:text-zinc-50">
            AutoPR Engine
          </div>
          <div className="flex gap-6">
            <Link
              href="/installation"
              className="text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-50"
            >
              Installation
            </Link>
            <Link
              href="/download"
              className="text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-50"
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

      {/* Hero Section */}
      <main className="flex-1">
        <section className="mx-auto max-w-7xl px-6 py-24 text-center">
          <div className="mb-8 inline-block rounded-full bg-gradient-to-r from-blue-50 to-purple-50 px-6 py-2 text-sm font-semibold text-blue-900 dark:from-blue-950 dark:to-purple-950 dark:text-blue-100">
            ⚡ Limited Time: Try our deployed instance →
          </div>
          <h1 className="mb-6 text-5xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 sm:text-6xl">
            AI-Powered GitHub PR Automation
          </h1>
          <p className="mx-auto mb-12 max-w-2xl text-xl text-zinc-600 dark:text-zinc-400">
            Transform your GitHub pull request workflows through intelligent analysis, 
            issue creation, and multi-agent collaboration.
          </p>
          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <a
              href="https://app.autopr.io"
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 px-8 py-3 text-lg font-semibold text-white transition-all hover:from-blue-700 hover:to-purple-700 hover:shadow-lg"
            >
              Try Deployed Instance
            </a>
            <Link
              href="/installation"
              className="rounded-lg bg-zinc-900 px-8 py-3 text-lg font-semibold text-white transition-colors hover:bg-zinc-800 dark:bg-zinc-50 dark:text-zinc-900 dark:hover:bg-zinc-200"
            >
              Get Started
            </Link>
            <Link
              href="/download"
              className="rounded-lg border-2 border-zinc-300 px-8 py-3 text-lg font-semibold text-zinc-900 transition-colors hover:border-zinc-400 dark:border-zinc-700 dark:text-zinc-50 dark:hover:border-zinc-600"
            >
              Download
            </Link>
          </div>
        </section>

        {/* Features Section */}
        <section className="mx-auto max-w-7xl px-6 py-24">
          <h2 className="mb-12 text-center text-3xl font-bold text-zinc-900 dark:text-zinc-50">
            Key Features
          </h2>
          <div className="grid gap-8 md:grid-cols-3">
            <div className="rounded-lg border border-zinc-200 p-6 dark:border-zinc-800">
              <h3 className="mb-3 text-xl font-semibold text-zinc-900 dark:text-zinc-50">
                🤖 AI-Powered Analysis
              </h3>
              <p className="text-zinc-600 dark:text-zinc-400">
                Intelligent code analysis using GPT-4, Claude, and other leading AI models 
                to provide comprehensive PR reviews.
              </p>
            </div>
            <div className="rounded-lg border border-zinc-200 p-6 dark:border-zinc-800">
              <h3 className="mb-3 text-xl font-semibold text-zinc-900 dark:text-zinc-50">
                🔄 Automated Workflows
              </h3>
              <p className="text-zinc-600 dark:text-zinc-400">
                Create custom workflows to automate issue creation, code reviews, 
                and deployment processes.
              </p>
            </div>
            <div className="rounded-lg border border-zinc-200 p-6 dark:border-zinc-800">
              <h3 className="mb-3 text-xl font-semibold text-zinc-900 dark:text-zinc-50">
                🚀 Multi-Agent Collaboration
              </h3>
              <p className="text-zinc-600 dark:text-zinc-400">
                Leverage multiple AI agents working together to handle complex 
                development tasks efficiently.
              </p>
            </div>
          </div>
        </section>

        {/* Limited Time Offer Section */}
        <section className="mx-auto max-w-7xl px-6 py-12">
          <div className="rounded-lg border-2 border-blue-500 bg-gradient-to-r from-blue-50 to-purple-50 p-8 text-center dark:from-blue-950 dark:to-purple-950">
            <div className="mb-2 text-sm font-semibold uppercase tracking-wide text-blue-700 dark:text-blue-300">
              ⚡ Limited Time Offer
            </div>
            <h2 className="mb-4 text-2xl font-bold text-zinc-900 dark:text-zinc-50">
              Try AutoPR Engine Now - No Installation Required!
            </h2>
            <p className="mb-6 text-lg text-zinc-700 dark:text-zinc-300">
              Use our deployed AutoPR instance to experience the power of AI-powered PR automation.
              Perfect for testing and evaluation before setting up your own instance.
            </p>
            <a
              href="https://app.autopr.io"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block rounded-lg bg-gradient-to-r from-blue-600 to-purple-600 px-8 py-3 text-lg font-semibold text-white transition-all hover:from-blue-700 hover:to-purple-700 hover:shadow-lg"
            >
              Access Deployed Instance →
            </a>
          </div>
        </section>

        {/* CTA Section */}
        <section className="mx-auto max-w-7xl px-6 py-24">
          <div className="rounded-lg bg-zinc-900 p-12 text-center dark:bg-zinc-800">
            <h2 className="mb-4 text-3xl font-bold text-white">
              Ready to Transform Your Workflow?
            </h2>
            <p className="mb-8 text-xl text-zinc-300">
              Get started with AutoPR Engine today and experience the future of PR automation.
            </p>
            <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
              <a
                href="https://app.autopr.io"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block rounded-lg bg-gradient-to-r from-blue-500 to-purple-500 px-8 py-3 text-lg font-semibold text-white transition-all hover:from-blue-600 hover:to-purple-600 hover:shadow-lg"
              >
                Try Deployed Instance
              </a>
              <Link
                href="/installation"
                className="inline-block rounded-lg bg-white px-8 py-3 text-lg font-semibold text-zinc-900 transition-colors hover:bg-zinc-100"
              >
                Install Now
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-200 dark:border-zinc-800">
        <div className="mx-auto max-w-7xl px-6 py-8 text-center text-zinc-600 dark:text-zinc-400">
          <p>&copy; {new Date().getFullYear()} AutoPR Engine. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
