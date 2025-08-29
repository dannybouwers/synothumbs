# -*- coding: utf-8 -*-
"""
Modern Synology Thumbnail Generator

Author: Gemini (based on the original script by phillips321)
License: CC BY-SA 4.0
Version: 6.2

Description:
This script scans a directory structure and generates thumbnails for photos and 
videos, compatible with Synology Photo Station / Synology Photos.

This modernized version includes the following improvements:
- Uses concurrent.futures for modern and efficient multithreading.
- Automatically determines the optimal number of threads based on CPU cores.
- Extended support for RAW formats (NEF, DNG, ARW, etc.) via the 'rawpy' library.
- Extended support for common video formats.
- Logging is written to a unique, timestamped log file instead of the terminal.
- A TQDM progress bar shows the progress in the terminal.
- Uses modern libraries like Pillow, rawpy, and tqdm.
- Utilizes pathlib for more robust file and path manipulation.

Requirements:
- Python 3.6+
- External commands: 'ffmpeg' must be installed and available in the system's PATH.
- Python packages: see requirements.txt (pip install -r requirements.txt)
"""

import os
import sys
import subprocess
import logging
import concurrent.futures
from datetime import datetime
from pathlib import Path

# Try to import external libraries and provide a clear error message if they are missing.
try:
    from PIL import Image, ImageOps
    import rawpy
    from tqdm import tqdm
except ImportError as e:
    print(f"Error: A required library is missing: {e.name}")
    print("Please install the required packages using: pip install -r requirements.txt")
    sys.exit(1)

# --- Configuration ---

# Define thumbnail sizes and filenames.
THUMBNAIL_CONFIG = {
    "SYNOPHOTO_THUMB_XL.jpg": (1280, 1280),
    "SYNOPHOTO_THUMB_L.jpg": (800, 800),
    "SYNOPHOTO_THUMB_B.jpg": (640, 640),
    "SYNOPHOTO_THUMB_M.jpg": (320, 320),
    "SYNOPHOTO_THUMB_S.jpg": (160, 160),
}
# Special configuration for the preview thumbnail
PREVIEW_CONFIG = {
    "name": "SYNOPHOTO_THUMB_PREVIEW.jpg",
    "size": (120, 120) # Adjusted to square for simpler padding
}

# Supported file formats
# rawpy supports most RAW formats from all major brands.
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff']
RAW_EXTENSIONS = ['.arw', '.cr2', '.cr3', '.crw', '.dng', '.erf', '.nef', '.nrw', '.orf', '.pef', '.raf', '.raw', '.rw2', '.sr2', '.srf', '.x3f']
VIDEO_EXTENSIONS = ['.mov', '.m4v', '.mp4', '.avi', '.mkv', '.mpg', '.mpeg', '.wmv', '.3gp', '.flv']

# --- Logging Setup ---

def setup_logging():
    """Configures logging to write to a file."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = log_dir / f"synothumb_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename=log_filename,
        filemode='w'
    )
    # Also add a handler to send errors to the console
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.ERROR)
    logging.getLogger().addHandler(console_handler)
    
    return log_filename

# --- Media Processing Functions ---

def process_image(file_path: Path):
    """Generates thumbnails for a single image file (standard or RAW)."""
    try:
        thumb_dir = file_path.parent / "@eaDir" / file_path.name
        
        # Check if the XL thumbnail already exists, then skip.
        if (thumb_dir / list(THUMBNAIL_CONFIG.keys())[0]).exists():
            return f"Skipped (already exists): {file_path.name}"
            
        thumb_dir.mkdir(parents=True, exist_ok=True)
        
        img = None
        if file_path.suffix.lower() in RAW_EXTENSIONS:
            with rawpy.imread(str(file_path)) as raw:
                # Postprocess the RAW data into an RGB image array
                rgb_array = raw.postprocess(use_camera_wb=True, output_bps=8)
                img = Image.fromarray(rgb_array)
        else: # Standard image
            img = Image.open(file_path)
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')

        # Apply rotation based on EXIF data
        img = ImageOps.exif_transpose(img)

        # Generate all standard thumbnails
        for name, size in THUMBNAIL_CONFIG.items():
            img_copy = img.copy()
            img_copy.thumbnail(size, Image.Resampling.LANCZOS)
            img_copy.save(thumb_dir / name, "JPEG", quality=95)

        # Generate the special preview thumbnail with padding
        p_name = PREVIEW_CONFIG['name']
        p_size = PREVIEW_CONFIG['size']
        img_copy = img.copy()
        img_copy.thumbnail(p_size, Image.Resampling.LANCZOS)
        
        # Add black padding to make it square
        padded_img = Image.new("RGB", p_size, (0, 0, 0))
        paste_pos = ((p_size[0] - img_copy.width) // 2, (p_size[1] - img_copy.height) // 2)
        padded_img.paste(img_copy, paste_pos)
        padded_img.save(thumb_dir / p_name, "JPEG", quality=90)
        
        return f"Image processed: {file_path.name}"

    except Exception as e:
        logging.error(f"Error processing image {file_path}: {e}")
        return f"Error: {file_path.name}"

def process_video(file_path: Path):
    """Generates a video filmstrip and thumbnails for a video file."""
    try:
        thumb_dir = file_path.parent / "@eaDir" / file_path.name
        
        # Check if the XL thumbnail already exists, then skip.
        if (thumb_dir / list(THUMBNAIL_CONFIG.keys())[0]).exists():
            return f"Skipped (already exists): {file_path.name}"
            
        thumb_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Generate the FLV filmstrip (optional, for older Synology versions)
        film_flv_path = thumb_dir / "SYNOPHOTO:FILM.flv"
        flv_cmd = [
            'ffmpeg', '-y', '-i', str(file_path), '-loglevel', 'panic',
            '-ar', '44100', '-r', '12', '-ac', '2', '-f', 'flv',
            '-qscale', '5', '-s', '320x180', str(film_flv_path)
        ]
        subprocess.run(flv_cmd, check=True, capture_output=True)

        # 2. Extract a frame after 1 second for the thumbnails
        temp_thumb_path = thumb_dir / f"{file_path.stem}_temp.jpg"
        thumb_cmd = [
            'ffmpeg', '-y', '-ss', '00:00:01', '-i', str(file_path),
            '-loglevel', 'panic', '-vframes', '1', str(temp_thumb_path)
        ]
        subprocess.run(thumb_cmd, check=True, capture_output=True)

        if not temp_thumb_path.exists():
            raise FileNotFoundError("FFmpeg failed to extract a thumbnail frame.")

        # 3. Generate the different thumbnail sizes from the frame
        with Image.open(temp_thumb_path) as img:
            for name, size in THUMBNAIL_CONFIG.items():
                img_copy = img.copy()
                img_copy.thumbnail(size, Image.Resampling.LANCZOS)
                img_copy.save(thumb_dir / name, "JPEG", quality=95)
        
        # Delete the temporary frame
        temp_thumb_path.unlink()

        return f"Video processed: {file_path.name}"
        
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.decode('utf-8', errors='ignore').strip()
        logging.error(f"FFmpeg error while processing video {file_path}: {error_message}")
        return f"FFmpeg Error: {file_path.name}"
    except Exception as e:
        logging.error(f"Error processing video {file_path}: {e}")
        return f"Error: {file_path.name}"

# --- Main Function ---

def main():
    """Finds media, sets up threads, and starts the process."""
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <path_to_photos_or_videos>")
        sys.exit(1)
        
    root_dir = Path(sys.argv[1])
    if not root_dir.is_dir():
        print(f"Error: The directory '{root_dir}' does not exist.")
        sys.exit(1)

    log_filename = setup_logging()
    print(f"Logging has started. Details are being saved to: {log_filename}")
    logging.info(f"Script started in directory: {root_dir}")

    print("Searching for media files (this might take a while)...")
    all_extensions = IMAGE_EXTENSIONS + RAW_EXTENSIONS + VIDEO_EXTENSIONS
    media_files = [
        f for f in root_dir.rglob('*') 
        if f.suffix.lower() in all_extensions and "@eaDir" not in str(f.parent)
    ]
    
    if not media_files:
        print("No media files found to process.")
        logging.info("No media files found.")
        sys.exit(0)

    print(f"Found {len(media_files)} media files.")
    logging.info(f"Found {len(media_files)} media files to process.")

    # Determine the number of threads (CPU cores, with a max of 32 for I/O-bound tasks)
    max_workers = min(32, (os.cpu_count() or 1) + 4)
    logging.info(f"Using {max_workers} threads.")

    tasks = []
    for file_path in media_files:
        if file_path.suffix.lower() in VIDEO_EXTENSIONS:
            tasks.append((process_video, file_path))
        else:
            tasks.append((process_image, file_path))

    with tqdm(total=len(tasks), desc="Generating thumbnails", unit="file") as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_task = {executor.submit(func, path): (func, path) for func, path in tasks}
            
            for future in concurrent.futures.as_completed(future_to_task):
                result = future.result()
                logging.info(result)
                pbar.update(1)

    print("\nAll tasks completed.")
    logging.info("Script finished successfully.")


if __name__ == "__main__":
    main()

