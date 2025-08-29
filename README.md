# Modern Synology Thumbnail Generator

This script is a modernized, high-performance replacement for the original `synothumb.pyz script by phillips321. It scans a directory for photos and videos and generates the thumbnail files required by Synology Photo Station and Synology Photos.

The entire codebase has been rewritten in Python 3 using modern libraries to improve performance, compatibility, and usability.

## Features

- **High-Performance Multithreading:** Uses a modern `ThreadPoolExecutor` to process multiple files concurrently, significantly speeding up the generation process.
- **Dynamic Thread Management:** Automatically determines the optimal number of threads to use based on your system's CPU cores.
- **Extensive RAW Format Support:** Natively supports a wide range of camera RAW formats (e.g., `.NEF`, `.CR3`, `.ARW`, `.DNG`) using the powerful rawpy library, eliminating the need for an external dcraw executable.
- **Broad Video Format Support:** Handles all common video formats using `ffmpeg` for thumbnail extraction and video processing.
- **Detailed Logging:** All operations, successes, and errors are logged to a timestamped file (`logs/synothumb_YYYYMMDD_HHMMSS.log`) for easy debugging, keeping your terminal clean.
- **Interactive Progress Bar:** Displays a real-time progress bar in the terminal using `tqdm`, so you always know the status of the generation process and the estimated time remaining.
- **Robust and Modern Codebase:** Written in Python 3, using `pathlib` for reliable path handling across different operating systems and including better error management.

## Requirements

 1. **Python 3.6+**
 1. **FFmpeg:** The `ffmpeg` command-line tool must be installed on your system and accessible in your system's PATH. This is used for all video processing.
 1. **Python Packages:** The script depends on a few Python libraries, which can be easily installed. These are listed in `requirements.txt`.

## Installation

 1. **Clone** or **Download**: Download `synothumb.py` and `requirements.txt` into the same directory.
 1. **Install FFmpeg**:
    - **Windows**: Download from the official FFmpeg website and add the `bin` directory to your system's PATH.
    - **macOS** (using Homebrew): `brew install ffmpeg`
    - **Linux** (Debian/Ubuntu): `sudo apt update && sudo apt install ffmpeg`
 1. **Install Python Packages**: Open a terminal in the script's directory and run the following command to install the required libraries:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the script from your terminal, providing the path to the root directory containing your photos and videos as an argument.

```bash
python synothumb.py "/path/to/your/media/folder"
```

The script will then:

 1. Scan the directory recursively for all supported image, RAW, and video files.
 1. Check for existing thumbnails to avoid redundant work.
 1. Process the files and generate the required `@eaDir` thumbnail folders and files.
 1. Log all actions into a new file inside the `logs` directory.

## Key Differences from the Original Script

This version is a significant upgrade over the original script. Here is a summary of the main improvements:

| Feature | Original Script | Modern Script |
| -------- | ------- | -------- |
| Python Version | Python 2 | Python 3.6+ |
| Multithreading | Manual `threading` and `Queue` | Modern `concurrent.futures.ThreadPoolExecutor` |
| Thread Count | Hardcoded (`NumOfThreads=8`) | Dynamically set based on CPU cores |
| RAW Image Handling | External `dcraw` process call for `.CR2` only | Native handling of most RAW formats via `rawpy` library |
| Dependencies | Older `PIL`, external `dcraw` | `Pillow`, `rawpy`, `tqdm` (managed via `requirements.txt`) |
| Logging | Prints all output directly to the terminal | Logs to a unique, timestamped file; only errors appear in terminal |
| User Feedback | Prints file names as they are processed | Displays a clean, real-time `tqdm` progress bar with ETA |
| Path Handling | `os.path` | Modern `pathlib` for cross-platform reliability |
| Error Handling | Basic, can halt on unexpected errors | More robust `try...except` blocks for individual file processing |
