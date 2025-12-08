# Homebrew formula for AutoPR Engine
# Install with: brew install JustAGhosT/tap/codeflow-engine
# Or tap first: brew tap JustAGhosT/tap && brew install codeflow-engine

class CodeflowEngine < Formula
  include Language::Python::Virtualenv

  desc "AI-Powered GitHub PR Automation and Issue Management"
  homepage "https://github.com/JustAGhosT/codeflow-engine"
  url "https://github.com/JustAGhosT/codeflow-engine/archive/refs/tags/v1.0.1.tar.gz"
  sha256 "PLACEHOLDER_SHA256"  # Update with actual SHA256 after release
  license "MIT"
  head "https://github.com/JustAGhosT/codeflow-engine.git", branch: "main"

  depends_on "python@3.12"

  # Core dependencies
  resource "pydantic" do
    url "https://files.pythonhosted.org/packages/source/p/pydantic/pydantic-2.9.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "click" do
    url "https://files.pythonhosted.org/packages/source/c/click/click-8.1.7.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "openai" do
    url "https://files.pythonhosted.org/packages/source/o/openai/openai-1.99.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  resource "pygithub" do
    url "https://files.pythonhosted.org/packages/source/p/PyGithub/PyGithub-2.4.0.tar.gz"
    sha256 "PLACEHOLDER"
  end

  def install
    virtualenv_install_with_resources

    # Generate shell completions
    generate_completions_from_executable(bin/"autopr", shells: [:bash, :zsh, :fish], shell_parameter_format: :click)
  end

  def caveats
    <<~EOS
      AutoPR Engine has been installed!

      To get started, set up your API keys:
        export GITHUB_TOKEN=ghp_your_token
        export OPENAI_API_KEY=sk-your_key

      Then run:
        autopr --help

      To add AutoPR to a GitHub repository:
        cd your-repo
        autopr init

      Documentation: https://github.com/JustAGhosT/codeflow-engine
    EOS
  end

  test do
    assert_match "AutoPR Engine", shell_output("#{bin}/autopr --version")
    assert_match "Usage:", shell_output("#{bin}/autopr --help")
  end
end
