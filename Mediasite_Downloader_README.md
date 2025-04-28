# Mediasite Batch Downloader for Lectures

A Python script designed to download Mediasite lecture videos in bulk using **yt-dlp**, addressing the lack of information online about this VERY specific problem I have.

## Motivation

Downloading university lectures hosted on platforms like Mediasite can be annoying. Existing generic video downloaders or browser extensions struggle with the specific authentication mechanisms (like temporary playback tickets) or streaming formats (M3U8) used. Previous attempts using custom JavaScript bookmarklets also proved unreliable due to API changes and request failures.

This script leverages the well-maintained **yt-dlp** tool and automates the download process once the URLs have been gathered.

## Features

- Download multiple Mediasite videos specified in a text file (`urls.txt`).
- Uses **yt-dlp** for robust handling of M3U8 streams and other formats.
- Leverages browser cookies (`--cookies-from-browser`) for authentication, handling temporary playback tickets effectively.
- Allows specifying custom output filenames for each video URL, ideal for organizing paired recordings.
- Supports configurable concurrent downloads via `config.txt`.
- Allows configuration of the output directory via `config.txt`.
- Provides console feedback on download progress and errors.

## Prerequisites

- **Python 3:** Install from <https://www.python.org/>.
- **yt-dlp:** Install and ensure it’s in your system `PATH`. Verify with:

  ```bash
  yt-dlp --version
  ```

- **JavaScript Bookmarklet (for URL Gathering):** The “Mediasite M3U8 Finder” bookmarklet to extract video URLs.

## Setup

1. **Get the code:**
   - Clone this repository or download `mediasite_downloader.py`.
2. **Create files:** In the same directory, create:
   - `config.txt` – configuration settings  
   - `urls.txt` – list of videos to download

## Configuration (`config.txt`)

```ini
[Settings]
# Number of simultaneous downloads (positive integer). Default: 1
Count=1

# Output directory path ("" for current directory)
Path=""

# Browser to extract cookies from (e.g., firefox, chrome). Default: firefox
Browser=firefox
```

> **Note:** The script will prepend `[Settings]` if it’s missing.

## Usage: Getting URLs and Running the Script

### Stage 1 – Gathering URLs with the Bookmarklet

1. Open the Mediasite lecture page in your chosen browser and log in.
2. Wait for the player to load, then play for a second and pause.
3. Open Developer Console (F12) and run the **Mediasite M3U8 Finder** javascript (alternatively you can save the javascript as a bookmark and just click on it on the page).
4. Copy the M3U8 URL(s) from the popup (may be multiple files depending on format of the lecture, which can include shared screen and room camera).
5. Paste the links quickly in the urls.txt file—playback tickets expire (I don't know in how long but run the python script in the same session).

### Stage 2 – Formatting `urls.txt` and Running the Downloader

1. Open `urls.txt` and add lines in the format:

   ```text
   DesiredFilenameWithoutExtension <space> Full_M3U8_URL
   ```

2. Ensure filenames have no spaces (use underscores).
3. Save and run:

   ```bash
   python mediasite_downloader.py
   ```

4. The script reads `config.txt`, processes `urls.txt`, and downloads videos concurrently.

## Troubleshooting / Notes

- **Bookmarklet failures:** Check the console for errors or network issues; API changes may require updating the bookmarklet.
- **yt-dlp errors:**
  - **401 / 403:** Expired playback ticket or cookie issue.
  - **429:** Reduce `Count` to avoid rate limits.
  - **404:** URL may be incorrect or expired.
- **Cookie issues:** Ensure you’re logged into Mediasite in the specified browser.
- **Path issues:** Verify `Path` is valid and writable.

## To-Do / Future Features

- **Video stitching:** Automatically combine paired videos (e.g., PIP or side-by-side).
- **Web automation:** Use Selenium or Playwright to extract URLs automatically.
- **GUI:** Provide a graphical interface for easier use.
- **Enhanced error handling:** Add recovery logic for common yt-dlp errors.

## License

This project is intended for personal use. To share publicly, consider adding an MIT License:

```text
MIT License

Copyright (c) 2025 Nicholas Barry Wissman

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
