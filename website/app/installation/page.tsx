import Header from "../components/Header";

export default function Installation() {
  return (
    <div className="flex min-h-screen flex-col bg-gradient-to-b from-zinc-50 to-white dark:from-black dark:to-zinc-950">
      <Header currentPage="installation" />

      <main className="flex-1">
        <section className="mx-auto max-w-4xl px-6 py-24">
          <h1 className="mb-6 text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
            Installation Guide
          </h1>
          <p className="mb-12 text-xl text-zinc-600 dark:text-zinc-400">
            Get AutoPR Engine up and running in minutes. Choose your preferred installation method.
          </p>

          <div className="space-y-8">
            {/* Quick Install */}
            <div className="rounded-lg border border-zinc-200 p-6 dark:border-zinc-800">
              <h2 className="mb-4 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
                Quick Install (Recommended)
              </h2>
              <p className="mb-4 text-zinc-600 dark:text-zinc-400">
                Use our automated installation script for the fastest setup:
              </p>
              <div className="rounded-lg bg-zinc-900 p-4 font-mono text-sm text-zinc-50 dark:bg-zinc-800">
                <code>curl -fsSL https://raw.githubusercontent.com/JustAGhosT/autopr-engine/main/install.sh | bash</code>
              </div>
            </div>

            {/* Docker Install */}
            <div className="rounded-lg border border-zinc-200 p-6 dark:border-zinc-800">
              <h2 className="mb-4 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
                Docker Installation
              </h2>
              <p className="mb-4 text-zinc-600 dark:text-zinc-400">
                Run AutoPR Engine in a containerized environment:
              </p>
              <div className="space-y-2 rounded-lg bg-zinc-900 p-4 font-mono text-sm text-zinc-50 dark:bg-zinc-800">
                <div>
                  <span className="text-zinc-400"># Pull the image</span>
                </div>
                <div>
                  <code>docker pull ghcr.io/justaghost/autopr-engine:latest</code>
                </div>
                <div className="mt-4">
                  <span className="text-zinc-400"># Run the container</span>
                </div>
                <div>
                  <code>docker run -p 8000:8000 ghcr.io/justaghost/autopr-engine:latest</code>
                </div>
              </div>
            </div>

            {/* Python Install */}
            <div className="rounded-lg border border-zinc-200 p-6 dark:border-zinc-800">
              <h2 className="mb-4 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
                Python Installation
              </h2>
              <p className="mb-4 text-zinc-600 dark:text-zinc-400">
                Install from PyPI using pip:
              </p>
              <div className="space-y-2 rounded-lg bg-zinc-900 p-4 font-mono text-sm text-zinc-50 dark:bg-zinc-800">
                <div>
                  <code>pip install autopr-engine</code>
                </div>
                <div className="mt-4">
                  <span className="text-zinc-400"># Or using Poetry</span>
                </div>
                <div>
                  <code>poetry add autopr-engine</code>
                </div>
              </div>
            </div>

            {/* GitHub App Setup */}
            <div className="rounded-lg border border-zinc-200 p-6 dark:border-zinc-800">
              <h2 className="mb-4 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
                GitHub App Setup
              </h2>
              <p className="mb-4 text-zinc-600 dark:text-zinc-400">
                Configure AutoPR Engine as a GitHub App:
              </p>
              <ol className="list-decimal space-y-2 pl-6 text-zinc-600 dark:text-zinc-400">
                <li>Create a new GitHub App in your organization settings</li>
                <li>Set the webhook URL to your AutoPR Engine instance</li>
                <li>Configure the required permissions (read/write access to PRs and issues)</li>
                <li>Install the app on your repositories</li>
                <li>Configure environment variables in your AutoPR Engine instance</li>
              </ol>
            </div>
          </div>

          <div className="mt-12 rounded-lg bg-blue-50 p-6 dark:bg-blue-950">
            <h3 className="mb-2 text-lg font-semibold text-blue-900 dark:text-blue-50">
              Need Help?
            </h3>
            <p className="text-blue-800 dark:text-blue-200">
              Check out our{" "}
              <a
                href="https://github.com/JustAGhosT/autopr-engine/blob/main/README.md"
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:no-underline"
              >
                documentation
              </a>{" "}
              or open an issue on GitHub.
            </p>
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

