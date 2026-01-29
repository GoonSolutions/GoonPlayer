# Changelog

All notable changes to GoonPlayer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0-beta] - 2026-01-29

### Added
- Initial public release
- Random clip playback mode with configurable duration ranges
- Random start point feature for videos
- Normal playback mode (standard video player behavior, still randomly selected videos)
- Fullscreen mode with auto-hiding controls and cursor
- Interactive seek bar with click-to-seek and drag-to-seek
- Volume and mute controls with persistence
- Multi-folder video library support
- Settings dialog for configuration
- Keyboard shortcuts (Spacebar, Alt+Enter, Esc)
- Debug mode (--debug flag for console output)
- Support for 20+ video formats (MP4, MKV, AVI, WebM, and more)
- Windows executable build via Nuitka
- Initial documentation (README, development guide, file structure info)

### Technical
- Built with PySide6 (Qt6) and python-vlc
- AGPL-3.0 license
- Python 3.10+ compatible

[0.1.0-beta]: https://github.com/GoonSolutions/GoonPlayer/releases/tag/v0.1.0-beta
