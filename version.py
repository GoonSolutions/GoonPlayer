"""
Version information for GoonPlayer.

Copyright (C) 2026 GoonSolutions
Licensed under GNU Affero General Public License v3.0 or later.
See LICENSE file or https://www.gnu.org/licenses/

Uses semantic versioning: MAJOR.MINOR.PATCH[-PRERELEASE]
Examples: 1.0.0, 0.1.0-beta, 0.2.0-alpha
"""

__version__ = "0.1.0-beta"


# Tuple format for version comparison
def parse_version(version_string: str) -> tuple:
    """Parse version string into a comparable tuple."""
    # Split on '-' to separate version from prerelease tag
    base, *prerelease = version_string.split('-')
    major, minor, patch = map(int, base.split('.'))
    pre_tag = prerelease[0] if prerelease else ''
    return (major, minor, patch, pre_tag)
