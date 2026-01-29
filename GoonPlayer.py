#!/usr/bin/env python3
"""
GoonPlayer

Copyright (C) 2026 GoonSolutions

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

Source code: https://github.com/GoonSolutions/GoonPlayer
"""

import sys
import os
import json
import random
import ctypes
from pathlib import Path
from PySide6 import QtWidgets, QtCore, QtGui

try:
    from version import __version__
except ImportError:
    __version__ = ""


# ============================================================
# DEBUG MODE (MUST BE BEFORE VLC SETUP)
# ============================================================
IS_BUNDLED = "__compiled__" in dir()
DEBUG = "--debug" in sys.argv or not IS_BUNDLED


# ============================================================
# VLC LIBRARY CONFIGURATION (MUST BE BEFORE IMPORTING VLC)
# ============================================================
def _bundle_dir() -> str:
    """Return the base directory for bundled data files."""
    # When running as a Nuitka one-file executable, use the extraction directory
    if getattr(sys, 'frozen', False) and hasattr(sys, '_NUITKA_BINARY_LOCATION'):
        # sys._NUITKA_BINARY_LOCATION points to the compiled binary itself
        # The extracted files are in the same directory
        return os.path.dirname(sys._NUITKA_BINARY_LOCATION)

    # Check if we're running from within a Nuitka standalone bundle
    # (sys.frozen may be False, but __file__ will point to the bundle directory)
    try:
        if __file__:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # If __file__ points to a location with 'GoonPlayer.dist' or similar, we're bundled
            if os.path.isdir(script_dir) and os.path.exists(os.path.join(script_dir, 'vlc')):
                return script_dir
    except NameError:
        pass

    # Fallback to current directory
    return os.getcwd()


def _setup_vlc_library() -> None:
    """
    Configure VLC library paths with priority:
    1. Bundled VLC (if available - for packaged builds)
    2. System VLC (if available - for development)

    For bundled builds, uses the bundled VLC exclusively.
    For source/development, falls back to system VLC if bundled is not found.
    """
    _vlc_dir = _bundle_dir()
    _vlc_lib_dir = os.path.join(_vlc_dir, "vlc")

    # Check if bundled VLC exists
    bundled_vlc_exists = os.path.isdir(_vlc_lib_dir)
    if bundled_vlc_exists:
        # Verify libvlc.dll (Windows) or libvlc.so (Linux) or libvlc.dylib (macOS) exists
        if sys.platform == "win32":
            libvlc_files = ["libvlc.dll"]
        elif sys.platform.startswith("linux"):  # pragma: no cover
            libvlc_files = ["libvlc.so", "libvlc.so.5"]
        elif sys.platform == "darwin":  # pragma: no cover
            libvlc_files = ["libvlc.dylib"]
        else:  # pragma: no cover
            libvlc_files = []

        bundled_vlc_exists = any(os.path.isfile(os.path.join(_vlc_lib_dir, f)) for f in libvlc_files) if libvlc_files else False

    if bundled_vlc_exists:
        # Use bundled VLC
        # Configure environment variables for VLC
        os.environ["VLC_PLUGIN_PATH"] = os.path.join(_vlc_lib_dir, "plugins")

        # On Windows, prioritize our VLC folder in the DLL search path
        if sys.platform == "win32":
            # Add VLC directory to the DLL search path (Python 3.8+)
            if hasattr(os, 'add_dll_directory'):
                try:
                    os.add_dll_directory(_vlc_lib_dir)
                except Exception:
                    pass  # Silent failure - will try PATH-based loading

            # Prepend to PATH to ensure our VLC DLLs are found first
            os.environ["PATH"] = _vlc_lib_dir + os.pathsep + os.environ.get("PATH", "")

        # Set library path environment variable for Linux/macOS
        elif sys.platform.startswith("linux"):
            os.environ["LD_LIBRARY_PATH"] = _vlc_lib_dir + os.pathsep + os.environ.get("LD_LIBRARY_PATH", "")
        elif sys.platform == "darwin":
            os.environ["DYLD_LIBRARY_PATH"] = _vlc_lib_dir + os.pathsep + os.environ.get("DYLD_LIBRARY_PATH", "")
    else:
        # No bundled VLC - check for system VLC installation
        # This allows development builds to use system VLC
        if DEBUG:
            print("Bundled VLC not found. Attempting to use system VLC installation...")

        # System VLC should be in PATH already, no special configuration needed
        # Just ensure we have a valid VLC_PLUGIN_PATH if possible
        if sys.platform == "win32":
            # Try common Windows installation paths
            vlc_paths = [
                "C:\\Program Files\\VideoLAN\\VLC",
                "C:\\Program Files (x86)\\VideoLAN\\VLC"
            ]
            for path in vlc_paths:
                if os.path.isdir(path) and os.path.isfile(os.path.join(path, "libvlc.dll")):
                    os.environ["VLC_PLUGIN_PATH"] = os.path.join(path, "plugins")
                    if hasattr(os, 'add_dll_directory'):
                        try:
                            os.add_dll_directory(path)
                        except Exception:
                            pass
                    os.environ["PATH"] = path + os.pathsep + os.environ.get("PATH", "")
                    if DEBUG:
                        print(f"Found system VLC at: {path}")
                    return
        elif sys.platform.startswith("linux"):
            # Linux usually has VLC in standard paths, just set LD_LIBRARY_PATH
            os.environ["LD_LIBRARY_PATH"] = "/usr/lib:/usr/local/lib" + os.pathsep + os.environ.get("LD_LIBRARY_PATH", "")
        elif sys.platform == "darwin":
            # macOS usually has VLC in standard paths
            os.environ["DYLD_LIBRARY_PATH"] = "/usr/local/lib" + os.pathsep + os.environ.get("DYLD_LIBRARY_PATH", "")


# Set up VLC before importing
_setup_vlc_library()

# Import vlc - this must happen AFTER environment variables are set
# Use a try/except to provide better error messages if it fails
try:
    import vlc
except ImportError as e:
    # If vlc module import fails, we need to give clear instructions
    error_msg = (
        f"Failed to import python-vlc module: {e}\n\n"
        "To fix this:\n"
        "1. Install the python-vlc package: pip install python-vlc\n"
        "2. Install VLC on your system from: https://www.videolan.org/vlc/\n"
        "3. Run this application again\n\n"
        "For development, ensure VLC is installed in a standard location:\n"
        "  - Windows: C:\\Program Files\\VideoLAN\\VLC\n"
        "  - Linux: /usr/lib (via package manager)\n"
        "  - macOS: /usr/local/lib (via Homebrew)\n\n"
        f"VLC library path was configured to: {os.environ.get('VLC_PLUGIN_PATH', 'NOT SET')}"
    )
    print(error_msg, file=sys.stderr)
    raise RuntimeError(error_msg) from e


"""
GoonPlayer

A lightweight PySide6 + python-vlc video player with two playback modes:

1) Normal mode (random_length = False)
    - Behaves like a standard video player.
    - Seek bar is interactive (click-to-seek + drag-to-seek).
    - Time display (right side) toggles between remaining (-mm:ss or -h:mm:ss)
        and elapsed (mm:ss or h:mm:ss) when clicked.
    - Advances to the next random video only when the current video ends or user presses next.

2) Random clip mode (random_length = True)
    - Plays a random clip length (between min_seconds and max_seconds).
    - Seek bar becomes indicator-only (disabled, no mouse input) but still reflects position
        within the full video.
    - Clip countdown is shown on the left (mm:ss or h:mm:ss), not clickable.
    - Pausing playback pauses the clip countdown and the auto-advance timer.

Configuration is stored in GoonPlayer.config.json in the working directory.
Icons are loaded from ./icons/*.svg (or from the bundle path when packaged).
"""

# ============================================================
# VERSION
# ============================================================
# Imported from version.py above


# ============================================================
# USER CONFIGURABLE APPLICATION NAME
# ============================================================
APP_NAME = "GoonPlayer"


# When packaged on Windows, optionally attach a console for debug output.
if DEBUG and IS_BUNDLED and sys.platform == "win32":
    if ctypes.windll.kernel32.AllocConsole():
        sys.stdout = open("CONOUT$", "w")
        sys.stderr = open("CONOUT$", "w")


# ============================================================
# CONFIG
# ============================================================
CONFIG_PATH = Path("GoonPlayer.config.json")
VIDEO_EXTENSIONS = {
    ".mp4", ".m4v", ".mkv", ".avi", ".mov", ".mpg", ".mpeg", ".webm",
    ".flv", ".ogv", ".vob", ".wmv", ".3gp", ".3g2", ".f4v",
    ".ts", ".m2ts", ".mts", ".divx"
}

DEFAULT_CONFIG = {
    "paths": [],
    "min_seconds": 25,
    "max_seconds": 45,
    "random_start": True,
    "random_length": True,
    "volume": 80,
    "muted": False,
}


def load_config() -> dict:
    """
    Load GoonPlayer.config.json and merge into defaults.

    Any new keys added to DEFAULT_CONFIG in future versions will automatically
    appear without breaking older config files.
    """
    cfg = DEFAULT_CONFIG.copy()
    if CONFIG_PATH.exists():
        try:
            cfg.update(json.loads(CONFIG_PATH.read_text()))
        except Exception:
            # If config is corrupt, fall back to defaults silently.
            pass
    return cfg


def save_config(cfg: dict) -> None:
    """Persist configuration to GoonPlayer.config.json."""
    CONFIG_PATH.write_text(json.dumps(cfg, indent=4))


def ms_to_clock(ms: int) -> str:
    """
    Format milliseconds as:
        - mm:ss for durations under 1 hour
        - h:mm:ss for durations >= 1 hour (hours can be many digits)
    """
    s = max(ms // 1000, 0)
    h = s // 3600
    m = (s % 3600) // 60
    s = s % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def icon(name: str) -> QtGui.QIcon:
    """
    Load an SVG icon from the local ./icons folder (or bundled resources).

    Expected filenames:
        icons/{name}.svg

    Falls back to a blank icon if the file is not found.
    """
    icon_path = os.path.join(_bundle_dir(), "icons", f"{name}.svg")
    if os.path.exists(icon_path):
        return QtGui.QIcon(icon_path)
    # Return blank icon if file not found
    return QtGui.QIcon()


# ============================================================
# VIDEO FRAME WITH DOUBLE-CLICK SUPPORT
# ============================================================
class VideoFrame(QtWidgets.QFrame):
    """QFrame that emits a signal when double-clicked."""
    doubleClicked = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Create transparent overlay to capture mouse events above VLC surface
        self.overlay = QtWidgets.QWidget(self)
        self.overlay.setStyleSheet("background: transparent;")
        self.overlay.mouseDoubleClickEvent = self._on_double_click
        self.overlay.show()
        self.overlay.raise_()

        # Create empty state message widget
        self.empty_state_widget = QtWidgets.QWidget(self.overlay)
        self.empty_state_widget.setStyleSheet("background: rgba(0, 0, 0, 150);")

        # Layout for centering
        layout = QtWidgets.QVBoxLayout(self.empty_state_widget)
        layout.addStretch()

        # Text message with inline icon
        text_label = QtWidgets.QLabel()
        text_label.setAlignment(QtCore.Qt.AlignCenter)
        text_label.setWordWrap(True)

        # Create inline icon (16x16 for text size)
        icon_pixmap = icon("settings").pixmap(16, 16)

        # Convert pixmap to base64 for HTML embedding
        import base64
        buffer = QtCore.QByteArray()
        qbuffer = QtCore.QBuffer(buffer)
        qbuffer.open(QtCore.QIODevice.WriteOnly)
        icon_pixmap.save(qbuffer, "PNG")
        qbuffer.close()
        icon_data = base64.b64encode(bytes(buffer)).decode()

        # HTML with inline icon
        html_text = (
            "<p style='line-height: 1.5;'>"
            "No folders configured.<br/>"
            "Click the settings button "
            f"<img src='data:image/png;base64,{icon_data}' width='16' height='16' style='vertical-align: middle; margin: 0 2px;'/> "
            "and configure some video folders."
            "</p>"
        )
        text_label.setText(html_text)
        text_label.setStyleSheet("color: white; font-size: 14pt; padding: 20px;")
        layout.addWidget(text_label)

        layout.addStretch()

        # Initially hidden
        self.empty_state_widget.hide()

    def resizeEvent(self, event):
        """Keep overlay and empty state widget sized to match the frame."""
        super().resizeEvent(event)
        self.overlay.setGeometry(self.rect())
        self.overlay.raise_()
        # Ensure empty state widget fills the overlay
        self.empty_state_widget.setGeometry(self.overlay.rect())

    def _on_double_click(self, event):
        """Handle double-click on the overlay."""
        if event.button() == QtCore.Qt.LeftButton:
            self.doubleClicked.emit()
        event.accept()

    def show_empty_state_message(self):
        """Show the empty state message."""
        self.empty_state_widget.show()
        self.empty_state_widget.raise_()

    def hide_empty_state_message(self):
        """Hide the empty state message."""
        self.empty_state_widget.hide()


# ============================================================
# CLICK-TO-SEEK + DRAG-TO-SEEK SLIDER
# ============================================================
class ClickSeekSlider(QtWidgets.QSlider):
    """
    A QSlider that supports both:
        - Dragging the handle (standard behavior)
        - Clicking on the groove to seek immediately (VLC-style)

    The slider emits seekRequested(new_value) when the user clicks on the groove.
    """
    seekRequested = QtCore.Signal(int)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            opt = QtWidgets.QStyleOptionSlider()
            self.initStyleOption(opt)

            # If the user clicked the handle, keep normal dragging.
            ctrl = self.style().hitTestComplexControl(
                QtWidgets.QStyle.CC_Slider,
                opt,
                event.position().toPoint(),
                self
            )
            if ctrl == QtWidgets.QStyle.SC_SliderHandle:
                return super().mousePressEvent(event)

            # Otherwise, seek to the clicked point on the groove.
            groove = self.style().subControlRect(
                QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderGroove, self
            )
            handle = self.style().subControlRect(
                QtWidgets.QStyle.CC_Slider, opt, QtWidgets.QStyle.SC_SliderHandle, self
            )

            if self.orientation() == QtCore.Qt.Horizontal:
                x = event.position().x()
                left = groove.left()
                right = groove.right() - handle.width() + 1
                if right <= left:
                    return super().mousePressEvent(event)
                x = max(left, min(x, right))
                ratio = (x - left) / (right - left)
            else:
                y = event.position().y()
                top = groove.top()
                bottom = groove.bottom() - handle.height() + 1
                if bottom <= top:
                    return super().mousePressEvent(event)
                y = max(top, min(y, bottom))
                ratio = (y - top) / (bottom - top)

            new_val = int(self.minimum() + ratio * (self.maximum() - self.minimum()))
            self.setValue(new_val)
            self.seekRequested.emit(new_val)
            event.accept()
            return

        super().mousePressEvent(event)


# ============================================================
# SETTINGS DIALOG
# ============================================================
class ConfigDialog(QtWidgets.QDialog):
    """
    Configuration UI for selecting folders and playback options.

    The dialog mutates the provided config dict in-place and persists it on Save.
    """
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        version_str = f" v{__version__}" if __version__ else ""
        self.setWindowTitle(f"GoonPlayer{version_str} Settings")
        self.config = config

        layout = QtWidgets.QVBoxLayout(self)

        # -------- Section 1: Paths --------
        layout.addWidget(QtWidgets.QLabel("Folders to use:"))

        self.path_list = QtWidgets.QListWidget()
        self.path_list.addItems(self.config["paths"])
        layout.addWidget(self.path_list)

        path_buttons = QtWidgets.QHBoxLayout()
        add_btn = QtWidgets.QPushButton("Add Folder")
        rem_btn = QtWidgets.QPushButton("Remove")
        path_buttons.addWidget(add_btn)
        path_buttons.addWidget(rem_btn)
        layout.addLayout(path_buttons)

        layout.addSpacing(12)

        # -------- Section 2: Random start --------
        self.random_start_cb = QtWidgets.QCheckBox("Pick random start point")
        self.random_start_cb.setChecked(self.config.get("random_start", True))
        layout.addWidget(self.random_start_cb)

        layout.addSpacing(12)

        # -------- Section 3: Random clip length + range --------
        self.random_length_cb = QtWidgets.QCheckBox("Play random clip length")
        self.random_length_cb.setChecked(self.config.get("random_length", True))
        layout.addWidget(self.random_length_cb)

        form = QtWidgets.QFormLayout()
        self.min_spin = QtWidgets.QSpinBox()
        self.max_spin = QtWidgets.QSpinBox()
        self.min_spin.setRange(1, 9999)
        self.max_spin.setRange(1, 9999)
        self.min_spin.setValue(self.config["min_seconds"])
        self.max_spin.setValue(self.config["max_seconds"])
        form.addRow("Min seconds:", self.min_spin)
        form.addRow("Max seconds:", self.max_spin)
        layout.addLayout(form)

        layout.addSpacing(16)

        save_btn = QtWidgets.QPushButton("Save")
        layout.addWidget(save_btn)

        add_btn.clicked.connect(self.add_path)
        rem_btn.clicked.connect(self.remove_path)
        save_btn.clicked.connect(self.save)

    def add_path(self) -> None:
        """Prompt the user for a directory and add it to the list."""
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            self.path_list.addItem(path)

    def remove_path(self) -> None:
        """Remove selected directories from the list."""
        for item in self.path_list.selectedItems():
            self.path_list.takeItem(self.path_list.row(item))

    def save(self) -> None:
        """Write UI values back into config and persist to disk."""
        self.config["paths"] = [
            self.path_list.item(i).text()
            for i in range(self.path_list.count())
        ]
        self.config["min_seconds"] = self.min_spin.value()
        self.config["max_seconds"] = self.max_spin.value()
        self.config["random_start"] = self.random_start_cb.isChecked()
        self.config["random_length"] = self.random_length_cb.isChecked()
        save_config(self.config)
        self.accept()


# ============================================================
# PLAYER
# ============================================================
class Player(QtWidgets.QMainWindow):
    """
    Main application window hosting:
        - VLC video output surface
        - A control bar with transport, seek bar, time display, and audio controls
    """
    def __init__(self):
        super().__init__()
        version_str = f" {__version__}" if __version__ else ""
        self.setWindowTitle(f"{APP_NAME}{version_str}")
        self.setWindowIcon(icon("app"))
        self.resize(900, 500)

        self.config = load_config()
        self.videos: list[str] = []
        self.current_video: str | None = None

        # Normal mode: time label toggles between remaining and elapsed
        self.show_remaining = True

        # Random clip mode: countdown to next clip (milliseconds)
        self.snippet_remaining_ms = 0

        # Tracks whether the user is actively interacting with the seek slider
        self.user_seeking = False

        # Create VLC instance - check for None since vlc.Instance() can fail silently
        self.instance = None
        self.player = None

        try:
            self.instance = vlc.Instance("--no-video-title-show", "--quiet")
            if self.instance is None:
                raise RuntimeError("VLC Instance creation failed - vlc.Instance() returned None")
        except Exception as create_error:
            # If quiet mode fails, try again with verbose output
            try:
                self.instance = vlc.Instance("--no-video-title-show")
                if self.instance is None:
                    raise RuntimeError("VLC Instance creation failed even in verbose mode - vlc.Instance() returned None")
            except Exception as verbose_error:
                # Both attempts failed - raise a combined error
                raise RuntimeError(f"VLC initialization failed. Quiet mode: {create_error}. Verbose mode: {verbose_error}")

        try:
            self.player = self.instance.media_player_new()
            if self.player is None:
                raise RuntimeError("VLC Player creation failed - media_player_new() returned None")
        except Exception as e:
            error_msg = (
                f"Failed to initialize VLC: {e}\n\n"
                f"This typically means:\n"
                f"1. The VLC libraries (libvlc.dll) are not found in the vlc/ folder\n"
                f"2. The VLC libraries are missing required dependencies\n"
                f"3. The VLC folder structure is incorrect\n\n"
                f"VLC library path: {os.environ.get('VLC_PLUGIN_PATH', 'NOT SET')}"
            )

            # Try to show error dialog if Qt is available
            try:
                msg_box = QtWidgets.QMessageBox()
                msg_box.setIcon(QtWidgets.QMessageBox.Critical)
                msg_box.setWindowTitle("VLC Initialization Error")
                msg_box.setText(error_msg)
                msg_box.exec()
            except Exception:
                pass

            # Always print to stderr
            print(f"ERROR: {error_msg}", file=sys.stderr)
            sys.exit(1)

        # Only set up event manager if player was successfully created
        if self.player is not None:
            # When a video ends, go to the next clip in the UI thread.
            self.event_manager = self.player.event_manager()
            self.event_manager.event_attach(
                vlc.EventType.MediaPlayerEndReached,
                lambda _: QtCore.QTimer.singleShot(0, self.next_clip)
            )

        # --- UI layout ---
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.video_frame = VideoFrame()
        self.video_frame.doubleClicked.connect(self.toggle_fullscreen)
        layout.addWidget(self.video_frame, 1)

        self.controls = self.build_controls()
        layout.addWidget(self.controls)

        self.setup_vlc()
        self.setup_cursor_hiding()

        # --- Fullscreen (video-only) ---
        self._is_fullscreen = False
        self._normal_geometry = None
        self._cursor_visible = True

        # Application-level shortcuts so they work regardless of focus.
        for seq in ("Alt+Enter", "Alt+Return"):
            sc = QtGui.QShortcut(QtGui.QKeySequence(seq), self)
            sc.setContext(QtCore.Qt.ApplicationShortcut)
            sc.activated.connect(self.toggle_fullscreen)

        esc = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Escape), self)
        esc.setContext(QtCore.Qt.ApplicationShortcut)
        esc.activated.connect(self.exit_fullscreen)

        # Spacebar to skip to next clip
        space = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Space), self)
        space.setContext(QtCore.Qt.ApplicationShortcut)
        space.activated.connect(self.next_clip)

        # Timer used only in random clip mode to advance to the next clip
        self.clip_timer = QtCore.QTimer(self)
        self.clip_timer.timeout.connect(self.next_clip)

        # Debug timer for countdown text output
        self.debug_timer = QtCore.QTimer(self)
        self.debug_timer.timeout.connect(self.debug_countdown)
        self.remaining_seconds = 0

        # Periodic UI refresh (seek bar, time labels, countdown bookkeeping)
        self.ui_timer = QtCore.QTimer(self)
        self.ui_timer.setInterval(250)
        self.ui_timer.timeout.connect(self.update_ui)
        self.ui_timer.start()

        # Start with the current configuration
        self.start_playlist()

    # ---------------- Fullscreen ----------------
    def toggle_fullscreen(self) -> None:
        if self._is_fullscreen:
            self.exit_fullscreen()
        else:
            self.enter_fullscreen()

    def enter_fullscreen(self) -> None:
        """Enter fullscreen with video only (hide control bar)."""
        if self._is_fullscreen:
            return
        self._is_fullscreen = True
        self._normal_geometry = self.geometry()
        self.controls.hide()
        self.showFullScreen()
        self.activateWindow()
        self.raise_()
        self.video_frame.setFocus()

        # Start cursor hiding timer (cursor will hide after 2 seconds)
        self.cursor_timer.start()

    def exit_fullscreen(self) -> None:
        """Exit fullscreen (Alt+Enter or Escape)."""
        if not self._is_fullscreen:
            return
        self._is_fullscreen = False

        # Stop cursor hiding and restore cursor
        self.cursor_timer.stop()
        self.setCursor(QtCore.Qt.ArrowCursor)
        self._cursor_visible = True

        self.showNormal()
        if self._normal_geometry is not None:
            self.setGeometry(self._normal_geometry)
        self.controls.show()
        self.activateWindow()
        self.raise_()

    # ---------------- Controls ----------------
    def build_controls(self) -> QtWidgets.QWidget:
        """
        Create the bottom control bar.

        Layout is three logical zones:
            - Left: prev / play-pause / next
            - Center: seek bar + time indicators
            - Right: settings / mute / volume slider
        """
        bar = QtWidgets.QHBoxLayout()
        bar.setContentsMargins(8, 0, 8, 8)
        bar.setSpacing(8)

        def btn(name: str) -> QtWidgets.QToolButton:
            b = QtWidgets.QToolButton()
            b.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
            b.setIcon(icon(name))
            b.setIconSize(QtCore.QSize(20, 20))
            b.setFixedSize(32, 32)
            return b

        self.play_btn = btn("play")
        self.play_btn.setToolTip("Play")
        nextb = btn("next")
        nextb.setToolTip("Next")

        left = QtWidgets.QHBoxLayout()
        left.addWidget(self.play_btn)
        left.addWidget(nextb)

        self.seek = ClickSeekSlider(QtCore.Qt.Horizontal)
        self.seek.setRange(0, 1000)

        self.seek.sliderPressed.connect(lambda: setattr(self, "user_seeking", True))
        self.seek.sliderReleased.connect(self.on_seek_released)
        self.seek.sliderMoved.connect(self.on_seek_moved)
        self.seek.seekRequested.connect(self.on_seek_clicked)

        # Normal mode time label (right side, clickable)
        self.time_lbl = QtWidgets.QLabel("-00:00")
        self.time_lbl.setAlignment(QtCore.Qt.AlignCenter)
        self.time_lbl.mousePressEvent = lambda e: self.toggle_time_mode()

        # Random clip mode time label (left side, not clickable)
        self.skip_lbl = QtWidgets.QLabel("00:00")
        self.skip_lbl.setAlignment(QtCore.Qt.AlignCenter)
        self.skip_lbl.hide()

        center = QtWidgets.QHBoxLayout()
        center.setSpacing(6)

        # Center layout always contains the same widgets; we just show/hide as needed
        center.addWidget(self.skip_lbl)
        center.addWidget(self.seek, 1)
        center.addWidget(self.time_lbl)

        settings = btn("settings")
        settings.setToolTip("Settings")
        self.mute_btn = btn("volume")
        self.mute_btn.setToolTip("Mute")
        self.volume = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setFixedWidth(75)
        self.volume.setFixedHeight(16)

        # Vertically center the slider within the fixed-height control bar
        volume_container = QtWidgets.QWidget()
        volume_layout = QtWidgets.QVBoxLayout(volume_container)
        volume_layout.setContentsMargins(0, 0, 0, 0)
        volume_layout.addStretch()
        volume_layout.addWidget(self.volume, alignment=QtCore.Qt.AlignVCenter)
        volume_layout.addStretch()

        right = QtWidgets.QHBoxLayout()
        right.addWidget(settings)
        right.addWidget(self.mute_btn)
        right.addWidget(volume_container)

        bar.addLayout(left)
        bar.addSpacing(12)
        bar.addLayout(center, 1)
        bar.addSpacing(12)
        bar.addLayout(right)

        container = QtWidgets.QWidget()
        container.setLayout(bar)
        container.setFixedHeight(44)

        # Tighten internal button padding while preserving native button borders
        container.setStyleSheet("QToolButton { padding: 0px; }")

        nextb.clicked.connect(self.next_clip)
        self.play_btn.clicked.connect(self.toggle_play)
        settings.clicked.connect(self.open_settings)
        self.mute_btn.clicked.connect(self.toggle_mute)
        self.volume.valueChanged.connect(self.set_volume)

        self.volume.setValue(self.config["volume"])
        self.player.audio_set_volume(self.config["volume"])
        self.player.audio_set_mute(self.config["muted"])
        self.mute_btn.setIcon(icon("mute" if self.config["muted"] else "volume"))

        return container

    def _apply_random_length_ui(self) -> None:
        """
        Apply UI behavior depending on random clip mode.

        - Normal mode: seek is interactive; right time label shown (clickable).
        - Random clip mode: seek becomes a read-only indicator; left countdown shown.
        """
        if self.config["random_length"]:
            self.time_lbl.hide()
            self.skip_lbl.show()

            # Seek bar becomes display-only (no mouse input), greyed out like a disabled control
            self.seek.setEnabled(False)
            self.seek.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
            self.user_seeking = False

            self.skip_lbl.setStyleSheet("color: rgba(255,255,255,140);")
        else:
            self.skip_lbl.hide()
            self.time_lbl.show()

            self.seek.setEnabled(True)
            self.seek.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)

            self.skip_lbl.setStyleSheet("")

    # ---------------- VLC ----------------
    def setup_vlc(self) -> None:
        """
        Bind the VLC video output to the Qt video_frame widget.
        """
        wid = int(self.video_frame.winId())
        if sys.platform == "win32":
            self.player.set_hwnd(wid)
        elif sys.platform.startswith("linux"):
            self.player.set_xwindow(wid)
        elif sys.platform == "darwin":
            self.player.set_nsobject(wid)

        # Prefer Qt handling of mouse events when supported
        try:
            self.player.video_set_mouse_input(False)
            self.player.video_set_key_input(False)
        except Exception:
            pass

    # ---------------- Playback ----------------
    def open_settings(self) -> None:
        """
        Open settings. If accepted and settings changed, re-scan and restart playback.
        Always restarts if all folders were removed (to stop current playback).
        """
        old_config = self.config.copy()
        dlg = ConfigDialog(self.config, self)
        result = dlg.exec()
        if result == QtWidgets.QDialog.Accepted:
            # If all folders were removed, always restart (stops playback)
            if old_config["paths"] and not self.config["paths"]:
                self.start_playlist()
            # Otherwise, only restart if config changed
            elif self.config != old_config:
                self.start_playlist()
            else:
                # Config didn't change, but still show empty state if needed
                if not self.config["paths"]:
                    self.video_frame.show_empty_state_message()
        else:
            # Dialog was cancelled, show empty state if needed
            if not self.config["paths"] or not self.videos:
                self.video_frame.show_empty_state_message()

    def start_playlist(self) -> None:
        """Scan for videos and begin playback."""
        self.videos = self.scan_videos()
        if self.videos:
            self.video_frame.hide_empty_state_message()
        self.next_clip()

    def scan_videos(self) -> list[str]:
        """
        Recursively scan configured folders for supported video files.
        """
        out: list[str] = []
        for b in self.config["paths"]:
            for r, _, f in os.walk(b):
                for file in f:
                    if Path(file).suffix.lower() in VIDEO_EXTENSIONS:
                        out.append(os.path.join(r, file))
        return out

    def next_clip(self) -> None:
        """
        Start playing a random video from the scanned list.

        - If random_start is enabled, begin from a random start point.
        - If random_length is enabled, schedule an auto-advance after the chosen clip length.
        """
        self.clip_timer.stop()
        self.snippet_remaining_ms = 0

        if not self.videos:
            self.current_video = None
            version_str = f" {__version__}" if __version__ else ""
            self.setWindowTitle(f"{APP_NAME}{version_str}")
            self.player.stop()
            self.video_frame.show_empty_state_message()
            return

        # When we have videos, hide the message
        self.video_frame.hide_empty_state_message()

        self.current_video = random.choice(self.videos)
        self.setWindowTitle(f"{APP_NAME} [{self.current_video}]")

        media = self.instance.media_new(self.current_video)
        self.player.set_media(media)
        self.player.play()

        # Wait for VLC to load the video length metadata.
        # We need to poll until we get a valid (non-zero, non-negative) length.
        # Timeout after ~2 seconds with 50ms polling intervals to avoid hanging.
        length = 0
        for _ in range(40):  # 40 * 50ms = 2 seconds max
            QtCore.QThread.msleep(50)
            length = self.player.get_length()
            if length > 0:
                break

        self.play_btn.setIcon(icon("pause"))

        start = 0
        if self.config["random_start"] and length > 0:
            # Ensure we have a valid range for random start
            max_start = max(length - self.config["max_seconds"] * 1000, 0)
            start = random.randint(0, max_start)
            self.player.set_time(start)

        clip_s = 0
        if self.config["random_length"]:
            clip_s = random.randint(self.config["min_seconds"], self.config["max_seconds"])

            # Check if there's enough time remaining in the video for the chosen clip
            remaining_time_s = (length - start) // 1000
            if remaining_time_s < self.config["min_seconds"]:
                # Not enough time for minimum clip duration - skip to next video
                if DEBUG:
                    print(f"Skipping: only {remaining_time_s}s remaining, need at least {self.config['min_seconds']}s")
                QtCore.QTimer.singleShot(0, self.next_clip)
                return

            # If remaining time is less than chosen clip duration, use remaining time
            clip_s = min(clip_s, remaining_time_s)
            self.snippet_remaining_ms = clip_s * 1000

            # Set up debug countdown timer only in random clip mode
            self.remaining_seconds = clip_s
            self.debug_timer.start(1000)
        else:
            clip_s = (length - start) // 1000
            self.debug_timer.stop()

        # Always start clip timer with appropriate duration
        self.clip_timer.start(clip_s * 1000)

        self._apply_random_length_ui()

        # Debug output - conditionally include parts based on config
        msg = f'Playing "{self.current_video}"'
        if self.config["random_start"]:
            msg += f' starting at {ms_to_clock(start)}'
        if self.config["random_length"]:
            msg += f' for {clip_s} seconds'
        if DEBUG:
            # Overwrite countdown line with \r if in random clip mode, otherwise normal print
            prefix = '\r' if self.config["random_length"] else ''
            print(f"{prefix}{msg}")

    def update_ui(self) -> None:
        """
        Periodic UI update:
            - Update countdown for random clip mode while playing
            - Update seek bar (as interactive or indicator)
            - Update time label(s)
        """
        playing = self.player.is_playing()

        # Only decrement the countdown while actually playing.
        if playing and self.config["random_length"] and self.snippet_remaining_ms > 0:
            self.snippet_remaining_ms = max(self.snippet_remaining_ms - 250, 0)

        length = self.player.get_length()
        pos = self.player.get_time()

        if self.config["random_length"]:
            # Left-side countdown to next clip with remaining time
            remaining_ms = self.snippet_remaining_ms
            self.skip_lbl.setText(f"-{ms_to_clock(remaining_ms)}")

            # Seek bar reflects position in the full video (display-only, read-only)
            if length > 0:
                self.seek.blockSignals(True)
                self.seek.setValue(int(pos / length * 1000))
                self.seek.blockSignals(False)
            return

        # Normal mode: interactive seek bar reflects playback position when user isn't dragging
        if length > 0 and not self.user_seeking:
            self.seek.blockSignals(True)
            self.seek.setValue(int(pos / length * 1000))
            self.seek.blockSignals(False)

        # Normal mode time display on the right
        if self.show_remaining:
            self.time_lbl.setText(f"-{ms_to_clock(length - pos)}")
        else:
            self.time_lbl.setText(ms_to_clock(pos))

    # --- Cursor hiding ---
    def setup_cursor_hiding(self):
        """Set up automatic cursor hiding in fullscreen mode."""
        self.cursor_timer = QtCore.QTimer(self)
        self.cursor_timer.setInterval(2000)
        self.cursor_timer.setSingleShot(True)  # Fire once, then stop until restarted
        self.cursor_timer.timeout.connect(self.hide_cursor)

        # Enable mouse tracking to receive mouse move events
        self.setMouseTracking(True)
        self.video_frame.setMouseTracking(True)

        # Install event filter on main window to catch mouse movements
        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        """Show cursor on mouse move in fullscreen, hide after 2 seconds of inactivity."""
        if self._is_fullscreen and event.type() == QtCore.QEvent.MouseMove:
            if not self._cursor_visible:
                # Cursor was hidden, show it
                self.setCursor(QtCore.Qt.ArrowCursor)
                self._cursor_visible = True
            # Restart the timer (resets the 2 second countdown)
            self.cursor_timer.start()

        return super().eventFilter(obj, event)

    def hide_cursor(self):
        """Hide cursor when in fullscreen and idle."""
        if self._is_fullscreen:
            self.setCursor(QtCore.Qt.BlankCursor)
            self._cursor_visible = False

    # --- Debug output ---
    def debug(self, msg):
        """Print debug messages to console if DEBUG mode is enabled."""
        if DEBUG:
            print(msg, flush=True)

    def debug_countdown(self):
        """Periodic debug output for remaining time in random clip mode."""
        self.remaining_seconds -= 1
        if self.remaining_seconds > 0 and self.remaining_seconds % 5 == 0:
            if DEBUG:
                # Use \r to overwrite the same line instead of creating new lines
                print(f"\rSwitching in {self.remaining_seconds} seconds...", end='', flush=True)

    # --- Seek handlers ---
    def seek_to_value(self, slider_value: int) -> None:
        """
        Convert the slider position (0..1000) to a VLC time and seek.
        No effect in random clip mode (seek is disabled/indicator-only).
        """
        if self.config["random_length"]:
            return
        length = self.player.get_length()
        if length <= 0:
            return
        target = int(length * (slider_value / 1000))
        self.player.set_time(target)

        # Restart clip timer with new remaining duration
        remaining_ms = max(length - target, 0)
        if remaining_ms > 0:
            self.clip_timer.start(remaining_ms)
        else:
            # If we're at or past the end, fire next_clip immediately
            QtCore.QTimer.singleShot(0, self.next_clip)

    def on_seek_clicked(self, v: int) -> None:
        """Handle click-to-seek on the slider groove."""
        self.user_seeking = True
        self.seek_to_value(v)
        self.user_seeking = False

    def on_seek_moved(self, v: int) -> None:
        """Handle drag updates while moving the slider handle."""
        self.seek_to_value(v)

    def on_seek_released(self) -> None:
        """Finalize seek when the user releases the slider handle."""
        self.seek_to_value(self.seek.value())
        self.user_seeking = False

    def toggle_time_mode(self) -> None:
        """Toggle remaining vs elapsed display (normal mode only)."""
        if not self.config["random_length"]:
            self.show_remaining = not self.show_remaining

    def toggle_play(self) -> None:
        """
        Toggle playback.
        In random clip mode, also pause/resume the auto-advance timer using the remaining ms.
        """
        if self.player.is_playing():
            self.player.pause()
            self.play_btn.setIcon(icon("play"))
            self.play_btn.setToolTip("Play")
            if self.config["random_length"] and self.snippet_remaining_ms > 0:
                self.clip_timer.stop()
        else:
            self.player.play()
            self.play_btn.setIcon(icon("pause"))
            self.play_btn.setToolTip("Pause")
            if self.config["random_length"] and self.snippet_remaining_ms > 0:
                self.clip_timer.start(self.snippet_remaining_ms)

    def set_volume(self, v: int) -> None:
        """Set VLC volume and persist to config."""
        self.player.audio_set_volume(v)
        self.config["volume"] = v
        save_config(self.config)

    def toggle_mute(self) -> None:
        """Toggle mute and persist to config."""
        m = not self.player.audio_get_mute()
        self.player.audio_set_mute(m)
        self.mute_btn.setIcon(icon("mute" if m else "volume"))
        self.mute_btn.setToolTip("Unmute" if m else "Mute")
        self.config["muted"] = m
        save_config(self.config)


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    win = Player()
    win.show()
    sys.exit(app.exec())
