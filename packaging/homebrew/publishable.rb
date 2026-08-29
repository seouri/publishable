# STAGING COPY. `seouri/homebrew-tap` is the source of truth; this file is here
# so the formula survives a `brew untap`, which deletes the tap tree Homebrew
# keeps under its own prefix. Edit both, or the two drift.
#
# The installable name is `seouri/tap/publishable`. A bare `brew install
# publishable` resolves only in homebrew-core, whose bar is >=75 stars, >=30
# forks or >=30 watchers plus a public repository with an immutable tagged
# release; until that is met, the tap is the route.
#
# Bumping this formula, and why each pin is what it is:
# docs/releasing.md § Homebrew.
class Publishable < Formula
  include Language::Python::Virtualenv

  desc "Run experiments so the record is publishable by default"
  homepage "https://github.com/seouri/publishable"
  url "https://files.pythonhosted.org/packages/55/62/cba9a28854402d4ae3ecfcd3be31fa5f33e1f2746b101ff44d063abaf3d3/publishable-0.2.4.tar.gz"
  sha256 "b8c8ae51a22d7dec1eb0c8cf75a3fcb43f1ae66021703bf0c9890aafe39ee96e"
  license "MIT"

  # `numpy` and `scipy` are Homebrew formulae and bottled, so they are
  # dependencies rather than resources — building either from source inside the
  # virtualenv costs minutes and buys nothing. `pyarrow` has no formula, so it
  # is a resource compiled against Homebrew's `apache-arrow`; its version must
  # match that formula's, which is why it is pinned rather than tracking latest.
  depends_on "cmake" => :build
  depends_on "ninja" => :build
  depends_on "rust" => :build # pyarrow > libcst
  depends_on "apache-arrow"
  depends_on "libyaml" # pyyaml
  depends_on "numpy"
  depends_on "python@3.13"
  depends_on "scipy"

  # `uv` and git are mandatory at runtime, not optional paths: `run` pins the
  # environment through `uv.lock` and refuses outside a git repository.
  depends_on "uv"
  uses_from_macos "git"

  resource "pyarrow" do
    url "https://files.pythonhosted.org/packages/3d/e3/27f57f80141379d60defe6703eb50a707325706f07fedfd1312c7a751995/pyarrow-25.0.1.tar.gz"
    sha256 "9150a83248bfed9813ea3c3af74c3856c1984d444aa28e58bf7733b9750ddf6a"
  end

  resource "python-dotenv" do
    url "https://files.pythonhosted.org/packages/6a/53/ed9d74092561d4b01a2ef1349d52cdbc135e526c245f366b089cfca6de49/python_dotenv-1.2.3.tar.gz"
    sha256 "a20a594dabeaa385725aa239d5244871c143ecb356add8a20fcf23773a6c3a35"
  end

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/05/8e/961c0007c59b8dd7729d542c61a4d537767a59645b82a0b521206e1e25c2/pyyaml-6.0.3.tar.gz"
    sha256 "d76623373421df22fb4cf8817020cbb7ef15c725b9d5e45f17e189bfc384190f"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    # `list-templates` renders core's own template without touching a repo or
    # the network, and naming `generic` proves the registry resolved rather
    # than that the entry point merely dispatched.
    assert_match "generic", shell_output("#{bin}/publishable list-templates")

    # `new` is the scaffold path, and it reads `readme_templates/*.tmpl`
    # through `importlib.resources` — the one payload a wheel can silently
    # drop, so the test asserts a scaffolded file rather than the exit code.
    system bin/"publishable", "new", "my-study"
    assert_path_exists testpath/"my-study/pyproject.toml"
    assert_path_exists testpath/"my-study/README.md"
  end
end
