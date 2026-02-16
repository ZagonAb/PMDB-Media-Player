# PMDB Media Player

**PMDB Media Player** is an advanced media player built with **Python**, **VLC**, and **CustomTkinter**, specifically designed to integrate seamlessly with the [PMDB-Theme](https://github.com/ZagonAb/PMDB-Theme) interface.

It provides a lightweight yet powerful playback experience focused on local media libraries and controller-friendly navigation.

![Window mode](https://github.com/ZagonAb/PMDB-Media-Player/blob/1ce3b7a661f3fd3d872408b2826129e12b2e08ba/.meta/screenshots/screen.png)
![Fullscreen mode](https://github.com/ZagonAb/PMDB-Media-Player/blob/1ce3b7a661f3fd3d872408b2826129e12b2e08ba/.meta/screenshots/screen1.png)

---

## Features

* Multi-format video playback powered by VLC
* Modern and customizable UI built with CustomTkinter
* External and embedded subtitle support
* Volume control and mute functionality
* Fullscreen playback mode
* Automatic playback position saving
* Keyboard shortcuts for fast interaction
* **Gamepad / joystick support (Linux & Windows)**
* Bilingual interface (Spanish / English)
* Native integration with **PMDB-Theme**

---

## System Requirements

### Common Requirements

* Python **3.8+**
* VLC Media Player installed on the system

---

### Linux (Debian / Ubuntu)

```bash
sudo apt-get install -y python3-dev python3-pip libvlc-dev vlc libx11-dev libgtk-3-dev
```

---

### Windows

Install the following components:

* [VLC Media Player (64-bit)](https://www.videolan.org/)
* [Python 3.8 or newer](https://www.python.org/)
* [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) (required by Pygame)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/ZagonAb/PMDB-Media-Player
cd PMDB-Media-Player
```

---

### 2. Create a virtual environment (recommended on Linux)

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

**Windows users** may install dependencies globally if preferred.

Make sure the VLC installation directory is available in the Windows `PATH` environment variable.

---

### Add VLC to PATH (Windows)

Open **Command Prompt as Administrator** and run:

```cmd
setx /M PATH "%PATH%;C:\Program Files\VideoLAN\VLC"
```

> Notes:
>
> * `/M` modifies the system PATH.
> * Restart the terminal after running the command.

Verify installation:

```cmd
vlc --version
```

---

## Running the Player

```bash
python main.py /path/to/video.mp4
```

### Available Options

| Option          | Description              |                           |
| --------------- | ------------------------ | ------------------------- |
| `--fullscreen`  | Start in fullscreen mode |                           |
| `--language [es | en]`                     | Select interface language |

Example:

```bash
python main.py --language en --fullscreen /path/to/video.mp4
```

---

## Building a Standalone Executable (Linux)

Recommended when using PMDB-Theme integration.

```bash
python build.py
```

Output location:

```
dist/PMDB_Media_Player
```

### Windows Note

Packaging is **not required**. You can directly reference the player in `metadata.txt`:

```
python path/to/PMDB-Media-Player/main.py --fullscreen {file.path}
```

---

## Gamepad Support

* Linux: most controllers work out of the box
* Windows: XInput-compatible controllers (Xbox controllers recommended)
* Generic controllers may require [x360ce](https://www.x360ce.com/) for Xbox controller emulation

---

## Controls

### Keyboard

| Key          | Action                         |
| ------------ | ------------------------------ |
| Space        | Play / Pause                   |
| Left Arrow   | Rewind 10 seconds              |
| Right Arrow  | Forward 10 seconds             |
| Up Arrow     | Increase volume                |
| Down Arrow   | Decrease volume                |
| F11          | Toggle fullscreen              |
| Double Click | Toggle fullscreen              |
| Escape       | Exit fullscreen / Close player |

### Gamepad

| Control     | Action             |
| ----------- | ------------------ |
| A (1)       | Play / Pause       |
| B (2)       | Toggle subtitles   |
| X (3)       | Toggle fullscreen  |
| Y (4)       | Close player       |
| D-Pad Up    | Volume up          |
| D-Pad Down  | Volume down        |
| D-Pad Left  | Rewind 10 seconds  |
| D-Pad Right | Forward 10 seconds |

---

## Advanced Configuration

Playback progress is automatically stored at:

| System          | Location                                                                                          |
| --------------- | ------------------------------------------------------------------------------------------------- |
| Linux           | `~/.config/pegasus-frontend/themes/PMDB-Theme/database.json`                                      |
| Linux (Flatpak) | `~/.var/app/org.pegasus_frontend.Pegasus/config/pegasus-frontend/themes/PMDB-Theme/database.json` |
| Windows         | `%LOCALAPPDATA%\pegasus-frontend\themes\PMDB-Theme\database.json`                                 |

---

## Customization

### Icons

Place PNG files inside:

```
PMDB_MP/assets/icons/
```

Required filenames:

| Category   | Files                                                     |
| ---------- | --------------------------------------------------------- |
| Playback   | `play.png`, `pause.png`                                   |
| Volume     | `volume.png`, `mute.png`                                  |
| Fullscreen | `fullscreen.png`, `no-fullscreen.png`                     |
| Navigation | `forward.png`, `backward.png`                             |
| Subtitles  | `subtitle-on.png`, `subtitle-off.png`, `embedded-sub.png` |

---

## Support

If you encounter a bug or have a feature request, please open an issue:

[https://github.com/ZagonAb/PMDB-Media-Player/issues](https://github.com/ZagonAb/PMDB-Media-Player/issues)

---

## License

This project is licensed under the **GNU General Public License v3.0 or later**, complying with the licensing requirements of python-vlc/VLC.

---

## Disclaimer

PMDB Media Player is a personal project and is **not officially affiliated** with Pegasus Frontend.

---

### 💖 DONATE
I'm a programming enthusiast and passionate about free software, with a special love for classic games and the retro community. All my themes and projects are open-source and available for anyone to use. If you'd like to show your support or help me continue creating and improving these projects, you can make a voluntary donation. Every contribution, no matter how small, allows me to continue improving and maintaining these projects. 👾

[![Support on PayPal](https://img.shields.io/badge/PayPal-0070ba?style=for-the-badge)](https://paypal.me/ZagonAb)
[![Donate using Liberapay](https://liberapay.com/assets/widgets/donate.svg)](https://liberapay.com/Gonzalo/donate)
[![Ko-fi](https://img.shields.io/badge/Ko--fi-29abe0?style=for-the-badge&logo=ko-fi)](https://ko-fi.com/zagonab)
