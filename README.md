# GoonPlayer

A lightweight video player that continuously plays random videos or snippets from your video library with optional random start points.

**Current Version:** 0.1.0-beta

---

## Quick Start (For End Users)

### Download & Run

1. **Download** `GoonPlayer-v0.1.0-beta-win64.zip` from the [releases page](https://github.com/GoonSolutions/GoonPlayer/releases)
2. **Extract** the ZIP file to your desired location
3. **Run** `GoonPlayer.exe`
4. That's it! No Python installation required.

### First Launch

When you start GoonPlayer for the first time:

1. Click the settings button to open the Settings dialog
2. Click **Add Folder** and browse to a folder containing your videos
3. (Optional) Add more folders
4. Configure your playback preferences (see below)
5. Click **Save**
6. Your video shuffle starts!

---

## Features

- **Random Video Selection**: Continuously plays videos from your configured folders
- **Random Clip Mode**: Play random-length segments (e.g., 25-45 seconds each)
- **Random Start Points**: Begin each video at a random position
- **Normal Mode**: Play full videos from start to finish (standard player behavior)
- **Persistent Settings**: Volume, mute state, and preferences saved across sessions
- **Fullscreen Mode**: Immersive viewing with auto-hiding cursor
- **Keyboard Shortcuts**: Quick controls for playback and navigation

---

## Playback Options

### Random Clip Length ✓
- Plays video segments of random duration
- Perfect for "ambient" viewing or discovery sessions
- **Min/Max seconds**: Set the duration range (e.g., 25-45 seconds)
- Countdown timer shows time remaining until next clip

### Random Start Point ✓
- Begin each video at a random position
- Great for discovering different parts of your videos
- Works in both normal and random clip mode

### Mode Combinations

- **Both OFF**: Standard video player - plays each randomly selected video from start to finish
- **Random Start ON, Clip Length OFF**: Start at random position, play until video ends
- **Both ON**: Play random snippets from random starting points (most chaotic mode)

---

## Controls & Shortcuts

### UI Controls

| Control | Action |
|---------|--------|
| **▶ / ⏸** | Play / Pause |
| **⏭** | Next Video |
| **⚙️** | Settings |
| **🔊 / 🔇** | Volume / Mute |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| **Spacebar** | Skip to Next Video |
| **Alt + Enter** | Toggle Fullscreen |
| **Double-Click** | Toggle Fullscreen |
| **Esc** | Exit Fullscreen |

### Display Modes

#### Normal Mode
- **Left**: Play/Pause, Next buttons
- **Center**: Interactive seek bar (click or drag to seek)
- **Right**: Time display (click to toggle remaining/elapsed), Volume and mute controls

#### Random Clip Mode
- **Left**: Countdown to next clip (-MM:SS)
- **Center**: Progress indicator (read-only, shows position in video)
- **Right**: Volume and mute controls

### Fullscreen
- Hides controls and time display
- Cursor auto-hides after 2 seconds of inactivity
- Toggle with Alt+Enter or double-click anywhere on the window
- Move mouse to show cursor temporarily
- Press Esc, Alt+Enter or double-click to exit

---

## Supported Video Formats

- MP4 (.mp4, .m4v)
- Matroska (.mkv)
- AVI (.avi)
- QuickTime (.mov)
- MPEG (.mpg, .mpeg)
- WebM (.webm)
- Flash Video (.flv, .f4v)
- Ogg Video (.ogv)
- DVD Video (.vob)
- Windows Media (.wmv)
- Mobile Video (.3gp, .3g2)
- Transport Stream (.ts, .m2ts, .mts)
- DivX (.divx)

*Format support depends on VLC libraries*

---

## Troubleshooting

### "No videos found" error
1. Open Settings (⚙️)
2. Ensure you've added at least one folder with videos
3. Check that the folder path is correct and accessible
4. Verify videos are in a supported format

### Videos won't play
1. Try a different video file to rule out file corruption
2. Check that the file is in a supported format
3. Run `GoonPlayer.exe --debug` to see error messages in console

### Application crashes on startup
1. Delete `GoonPlayer.config.json` in the GoonPlayer folder to reset settings
2. Try launching again
3. Verify all folders in settings are accessible

### Performance issues
- Large video libraries may take a moment to scan on first launch
- Consider organizing videos into smaller folder structures
- Close other resource-intensive applications

### Need more help?
- Run with `--debug` flag to see detailed console output: `GoonPlayer.exe --debug`
- Check the [full documentation](docs/DEVELOPMENT.md) for advanced topics

---

## Uninstalling

Simply delete the `GoonPlayer` folder. No registry changes or leftover files.

The `GoonPlayer.config.json` file (if you want to keep your settings) can be backed up before deleting.

---

## Updating

When a new version is released:
1. Download the new version ZIP
2. Extract to a new folder (or delete the old one first)
3. Run the new `GoonPlayer.exe`
4. Your old `GoonPlayer.config.json` will still work with new versions!

---

# Development & Building

## Running from Source

### Requirements

- Python 3.10 or higher
- pip (Python package manager)

### Installation

1. **Clone or download** this repository
2. **Create virtual environment** (recommended):
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
3. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```
4. **Run the application**:
   ```powershell
   python GoonPlayer.py
   ```

Debug mode is automatically enabled when running from Python source.

---

## Building Windows Executable

### Prerequisites

Before building, you must have **VLC installed on your system**:

1. **Download VLC** from [videolan.org](https://www.videolan.org/vlc/)
2. **Install** using the default installation path
   - Standard: `C:\Program Files\VideoLAN\VLC`
   - 32-bit: `C:\Program Files (x86)\VideoLAN\VLC`

The build script will automatically detect VLC at the default locations.

### Using the Build Script

```powershell
.\scripts\build.ps1
```

This script:
- Checks for Python and Nuitka (installs if needed)
- Finds your system VLC installation
- Builds the standalone executable
- Bundles VLC libraries and plugins into the distribution
- Copies icons to the distribution
- Outputs to `dist/GoonPlayer.dist/`

### Custom VLC Path

If VLC is installed in a non-standard location, specify the path:

```powershell
.\scripts\build.ps1 -vlcPath "D:\CustomPath\VLC"
```

### Creating Release Archive

```powershell
.\scripts\build.ps1 -release
```

This builds and creates a release archive:
- `release/GoonPlayer-{version}-win64.zip` - Binary distribution

### Clean Build Artifacts

```powershell
.\scripts\build.ps1 -clean
```

This removes `build/`, `dist/`, `release/`, `__pycache__/`, and `.spec` files.

### Build Output

- `dist/GoonPlayer.dist/` - Standalone build directory with EXE + dependencies
- `*.build/` - Temporary Nuitka build cache (auto-cleaned)

---

## Project Structure

```
GoonPlayer/
├── GoonPlayer.py           # Main application
├── version.py              # Version management
├── requirements.txt        # Python dependencies
├── GoonPlayer.config.json  # User settings (auto-generated)
├── scripts/                # Build and utility scripts
│   ├── build.ps1           # Build script (finds VLC from system)
│   └── make-icon.ps1       # Icon generation utility
├── icons/                  # Application and UI icons
│   ├── app.svg             # Application window icon (SVG)
│   ├── app.ico             # Application icon for exe embedding
│   └── *.svg               # UI control icons
├── dist/                   # Build output (auto-generated)
│   ├── GoonPlayer.dist/    # Built application with bundled VLC
│   └── GoonPlayer.exe      # Main executable
└── docs/                   # Documentation
    ├── INDEX.md            # Documentation index
    ├── DEVELOPMENT.md      # Developer guide
    └── FILE_STRUCTURE.md   # Project layout
```

---

## Versioning & Releases

GoonPlayer uses [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH[-PRERELEASE]**
- Examples: `0.1.0-beta`, `0.2.0`, `1.0.0`

Version is stored in `version.py` and displayed in the Settings dialog title.

### Creating a Release

1. Update version in `version.py`
2. Test thoroughly (see [DEVELOPMENT.md](docs/DEVELOPMENT.md))
3. Build release archive: `.\scripts\build.ps1 -release`
4. Create git tag and GitHub release
5. Upload `release/GoonPlayer-{version}-win64.zip` as release asset

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for testing guidelines.

---

## Configuration

Settings are stored in `GoonPlayer.config.json`:

```json
{
    "paths": ["C:\\Videos\\Folder1", "D:\\MoreVideos"],
    "min_seconds": 25,
    "max_seconds": 45,
    "random_start": true,
    "random_length": true,
    "volume": 80,
    "muted": false
}
```

Configuration automatically merges with defaults when the app starts, ensuring backward compatibility with older config files.

---

## Advanced Usage

### Debug Mode

Run with the `--debug` flag to see console output:

```powershell
GoonPlayer.exe --debug
```

This opens a console window showing:
- Selected video paths
- Random start positions (if enabled)
- Clip duration and countdown (if in random clip mode)
- Any error messages

Debug is automatically enabled when running from Python source.

---

## Development Resources

- **[DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Architecture, code organization, testing checklist
- **[FILE_STRUCTURE.md](docs/FILE_STRUCTURE.md)** - Project layout and file purposes

### Technology Stack

- **PySide6** (Qt6) - GUI framework
- **python-vlc** - Video playback via VLC libraries
- **Nuitka** - Native compilation and executable packaging

---

## Contributing

Contributions are welcome! Please feel free to:
- Suggest new features
- Submit pull requests

Before contributing code, see [DEVELOPMENT.md](docs/DEVELOPMENT.md) for architecture details and testing guidelines.

---

## License

AGPL-3.0

---

**Enjoy your GoonPlayer experience!** 🎬

For detailed developer documentation, see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).
