# GoonPlayer Development Guide

## Project Overview

GoonPlayer is a Python-based video player using PySide6 (Qt) and python-vlc. It specializes in playing random videos or snippets of videos from a video library with optional random start points.

## Architecture

### Main Components

1. **GoonPlayer.py** - Main application file containing:
   - `ClickSeekSlider` - Custom slider for click-to-seek functionality
   - `ConfigDialog` - Settings UI dialog
   - `Player` - Main window and playback logic

2. **version.py** - Version management (semantic versioning)

3. **Assets**:
   - `icons/` - SVG icons for UI controls
   - `vlc/plugins/` - VLC plugin directory (bundled with releases)
   - `GoonPlayer.config.json` - User configuration (generated at runtime)

#### Playback Modes

**Random Clip Mode** (`random_length = True`):
- Plays video segments of random duration within min/max range
- Uses `clip_timer` to auto-advance after segment ends
- Tracks `snippet_remaining_ms` for countdown display
- Seek bar is disabled (display-only)

**Normal Mode** (`random_length = False`):
- Plays full videos or portions selected by user
- Seek bar is fully interactive
- Time display toggles between elapsed/remaining (click on time label)

#### UI Timer vs Clip Timer

- **ui_timer** (250ms): Updates seek bar, time labels, countdown
- **clip_timer**: Fires after video/segment ends, triggers `next_clip()`
- **debug_timer** (1s): Prints countdown when DEBUG is enabled (random clip mode only)
- **cursor_timer**: Auto-hides cursor in fullscreen after 2 seconds inactivity

#### Configuration

Config is stored in `GoonPlayer.config.json` and persists:
- Selected directories (`paths`)
- Playback settings (`random_start`, `random_length`, `min_seconds`, `max_seconds`)
- Audio settings (`volume`, `muted`)

New settings automatically merge with defaults, maintaining backward compatibility.

## Development Setup

### Prerequisites

```powershell
# Python 3.10+
python --version

# Virtual environment (recommended)
python -m venv venv
.\venv\Scripts\activate  # Windows PowerShell
# source venv/bin/activate  # macOS/Linux (if cross-platform)
```

### Installation

```powershell
pip install -r requirements.txt
```

### Running from Python

```powershell
python GoonPlayer.py
```

Debug mode is automatically enabled when running from Python. When running the bundled .exe, use the `--debug` flag to enable debug output and open a console window. Console output shows:
- Selected video path
- Random start position (if enabled)
- Clip duration and countdown (if enabled)

Debug behavior:
- **Running from Python**: Debug always enabled (console already exists)
- **Bundled .exe without --debug**: No console window, no debug output
- **Bundled .exe with --debug**: Console window opens, debug output shown

## Code Organization

### Entry Point
```python
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = Player()
    win.show()
    sys.exit(app.exec())
```

### VLC Initialization
- Plugin path set to bundled `vlc/plugins/` when packaged
- Video output bound to Qt widget via platform-specific methods
- Event listener on `MediaPlayerEndReached` triggers `next_clip()`

### Video Scanning
`scan_videos()` recursively walks configured directories and collects supported formats (.mp4, .m4v, .mkv, .avi, .mov, .mpg, .mpeg, .webm, .flv, .ogv, .vob, .wmv, .3gp, .3g2, .f4v, .ts, .m2ts, .mts, .divx).

### Seek Behavior

**ClickSeekSlider** extends QSlider to enable:
- **Click-to-seek**: Click anywhere on the groove to jump to that position
- **Standard drag**: Drag the handle for continuous seeking

In random clip mode, both are disabled (read-only display).

## Common Modifications

### Adding a New Video Format

In `GoonPlayer.py`, update `VIDEO_EXTENSIONS`:
```python
VIDEO_EXTENSIONS = {
    ".mp4", ".m4v", ".mkv", ".avi", ".mov", ".mpg", ".mpeg", ".webm",
    ".flv", ".ogv", ".vob", ".wmv", ".3gp", ".3g2", ".f4v",
    ".ts", ".m2ts", ".mts", ".divx", ".rv"
} # added RealVideo extension
```

### Adding Debug Output

Use the `debug()` method:
```python
self.debug(f"Video loaded: {self.current_video}")
```

This automatically prints when running from Python (DEBUG is enabled for non-bundled execution)

### Changing Default Config Values

In `GoonPlayer.py`, update `DEFAULT_CONFIG`:
```python
DEFAULT_CONFIG = {
    "paths": [],
    "min_seconds": 25,
    "max_seconds": 45,
    "random_start": True,
    "random_length": True,
    "volume": 80,
    "muted": False,
}
```

### Modifying UI Controls

- Buttons created in `build_controls()` → `btn()` helper creates styled toolbar buttons
- Control layout is three zones: left (transport), center (seek), right (audio)
- Icons loaded via `icon(name)` function

### Time Format Changes

The `ms_to_clock()` function formats milliseconds. Modify it to change time display format.

## Testing Checklist

Before committing changes:

- [ ] Application launches without errors
- [ ] Settings dialog opens and saves correctly
- [ ] Can add/remove folders in settings
- [ ] Videos are found and can play
- [ ] Random clip mode works (countdown appears, auto-advances)
- [ ] Normal mode works (full video plays)
- [ ] Seek bar functions (normal mode)
- [ ] Play/pause toggles correctly
- [ ] Volume and mute controls work
- [ ] Fullscreen toggle works (Alt+Enter)
- [ ] Cursor hides in fullscreen (after 2 seconds)
- [ ] Time display toggles in normal mode
- [ ] Debug output appears when running from Python
- [ ] No errors in console

## Packaging

### Build Requirements

Nuitka is automatically installed by the build script if not present. A C compiler is also required (MSVC or MinGW64; Nuitka can auto-download MinGW64 if needed).

### Building the Executable

```powershell
.\scripts\build.ps1
```

This script:
- Checks for Python and Nuitka (installs if missing)
- Compiles the application to native code via Nuitka (standalone mode)
- Bundles icons from `icons/` folder
- Includes VLC plugins from `vlc/plugins/` folder
- Creates a windowed executable (no console)
- Outputs to `dist/GoonPlayer.dist/`
- Auto-cleans Nuitka build cache after success

**Options:**
- `.\scripts\build.ps1` - Build standalone
- `.\scripts\build.ps1 -release` - Build and create release archive
- `.\scripts\build.ps1 -clean` - Clean build artifacts

## Performance Considerations

- **Video scanning**: Happens on `start_playlist()`, can be slow for large directories
  - Consider caching scan results in future versions
- **UI updates**: 250ms interval provides smooth visuals without excessive CPU usage
- **VLC plugin path**: Must be set before creating VLC instance
- **Memory**: Video files are streamed via VLC, not loaded into memory

## Known Issues & TODOs

- No playlist feature currently
- No video filtering/search
- Windows-only packaging support (not tested on macOS/Linux)
- Cursor hiding doesn't work on all window managers
- VLC plugin availability varies by system (fallback to system VLC on some platforms)

## Future Enhancements

- Playlist support with save/load
- Video search and filtering
- Customizable keyboard shortcuts
- Theme/UI customization
- Linux/macOS packaging
- Remote control support
- Video thumbnails
- Watch history

## Debugging Tips

### VLC Issues
If videos won't play:
1. Check VLC plugin path: `os.environ["VLC_PLUGIN_PATH"]`
2. Verify VLC installation: `python -c "import vlc; print(vlc.__version__)"`
3. Run from Python (not bundled .exe) to see debug output and VLC errors
4. Check video file is in a supported format

### UI Issues
- Use `setStyleSheet()` to debug widget visibility
- Check event connections with breakpoints
- Verify icons exist in `icons/` directory

### Config Issues
- Delete `GoonPlayer.config.json` to reset to defaults
- Check that JSON is valid (use online JSON validator)
- Ensure paths in config are accessible

## Code Style

The codebase follows PEP 8 with:
- Type hints for function parameters and returns
- Clear section comments (# ====== ... ======)
- Docstrings for classes and public methods
- Self-documenting variable names

## Getting Help

- Check existing comments in code
- Review VLC documentation: https://www.videolan.org/developers/vlc/
- Review PySide6 documentation: https://doc.qt.io/qtforpython/
- GitHub Issues for bug reports and feature requests
