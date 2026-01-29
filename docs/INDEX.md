# GoonPlayer Documentation Index

Complete guide to all documentation files for GoonPlayer.

---

## Documentation Files

### For End Users

| File | Purpose | When to Read |
|------|---------|--------------|
| [README.md](../README.md) | Complete guide: installation, features, usage, building | Start here |

### For Developers/Contributors

| File | Purpose | When to Read |
|------|---------|--------------|
| [DEVELOPMENT.md](DEVELOPMENT.md) | Code architecture, how to modify | Before making changes |
| [FILE_STRUCTURE.md](FILE_STRUCTURE.md) | Project directory layout and file purposes | To understand the project layout |

### Configuration & Build

| File | Purpose |
|------|---------|
| [version.py](../version.py) | **Edit this to change version** |
| [scripts/build.ps1](../scripts/build.ps1) | **Run this to build executable** |
| [scripts/make-icon.ps1](../scripts/make-icon.ps1) | Generate app icon from SVG |
| [requirements.txt](../requirements.txt) | Python dependencies |
| [.gitignore](../.gitignore) | Git ignore configuration |

---

## Quick Links by Task

### I want to modify the code
1. Read [DEVELOPMENT.md](DEVELOPMENT.md) for architecture
2. Make changes to [GoonPlayer.py](../GoonPlayer.py)
3. Test thoroughly

### I need to build the executable
1. Run: `.\scripts\build.ps1`
2. Test: `dist\GoonPlayer.exe`

### I'm a new contributor
1. Read [README.md](../README.md)
2. Read [DEVELOPMENT.md](DEVELOPMENT.md)

### I'm an end user
1. Read [README.md](../README.md)

---

## File Descriptions

### Core Application Files

**[GoonPlayer.py](../GoonPlayer.py)**
- Main application file
- Implements both playback modes
- Qt/VLC-based video player

**[version.py](../version.py)**
- Single source of truth for version number
- Current: `0.1.0-beta`
- Supports semantic versioning

### Build & Distribution

**[scripts/build.ps1](../scripts/build.ps1)**
- PowerShell build script
- One-command builds
- Auto-cleans previous builds
- Auto-installs Nuitka if needed

**[scripts/make-icon.ps1](../scripts/make-icon.ps1)**
- Icon generation utility
- Converts SVG to ICO format using ImageMagick

**[requirements.txt](../requirements.txt)**
- Python package dependencies
- Current: PySide6, python-vlc

### Documentation

**[README.md](../README.md)** - Users read this first
- Installation instructions
- Feature list
- Usage guide
- Keyboard shortcuts
- Building executable
- Troubleshooting
- Development section

**[DEVELOPMENT.md](DEVELOPMENT.md)**
- Architecture overview
- Component descriptions
- Development setup
- Code organization
- How to modify specific things
- Testing checklist
- Debugging tips
- Known issues & TODOs

**[FILE_STRUCTURE.md](FILE_STRUCTURE.md)**
- Project directory tree
- File purposes by category
- Build output locations

### Configuration

**[.gitignore](../.gitignore)**
- Ignores build artifacts, Python cache, virtual environments, IDE files, OS files

---

## File Relationships

```
version.py ──imports──> GoonPlayer.py (shows in title bar)
                            │
                     ├─ Uses: icons/
                     ├─ Uses: vlc/plugins/
                     └─ Creates: GoonPlayer.config.json

GoonPlayer.py ──builds with──> scripts/build.ps1 (Nuitka)
                                    │
                           dist/GoonPlayer.exe
```

---

## Learning Path

New to the project?

1. **First**: Read [README.md](../README.md)
2. **Then**: Read [DEVELOPMENT.md](DEVELOPMENT.md)
3. **Reference**: [FILE_STRUCTURE.md](FILE_STRUCTURE.md)

---

**Version**: 0.1.0-beta
