"""
core/version.py

Single source of truth for the app's current version. Bump APP_VERSION
before building each new release - core/updater.py compares this against
the latest GitHub release tag to decide whether an update is available.

Format: plain "MAJOR.MINOR.PATCH" (no leading "v" - the GitHub release
tag itself is "vMAJOR.MINOR.PATCH", updater.py strips the "v" to compare).
"""

APP_VERSION = "1.0.0"
