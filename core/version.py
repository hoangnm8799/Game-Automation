"""Version embedded in a packaged release.

GitHub Actions generates ``core._build_version`` from the release tag
(for example, tag ``v1.2.3`` becomes version ``1.2.3``) immediately before
PyInstaller builds the executable.  Keeping the generated file out of git
makes the tag the single source of truth for every published version.
"""

try:
    # Created only while packaging a release; bundled by PyInstaller.
    from core._build_version import APP_VERSION
except ImportError:
    # Running directly from source is never a published release.
    APP_VERSION = "0.0.0-dev"
