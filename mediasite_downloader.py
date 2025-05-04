import subprocess
import os
import sys
import concurrent.futures
import threading
import shlex # Used for safer command printing

# --- Constants ---
TARGET_FILE = "urls.txt"  # Name of the file containing filenames and URLs

def get_interactive_settings():
    """Gets download settings interactively from the user."""
    settings = {}

    # 1. Concurrent Downloads
    while True:
        try:
            count_str = input("Enter max number of concurrent downloads (e.g., 1, 2, 3) [Default=1]: ")
            if not count_str:
                settings['count'] = 1
            else:
                settings['count'] = int(count_str)
            if settings['count'] < 1:
                print("Count must be 1 or greater.")
            else:
                if settings['count'] > 3:
                     print("Warning: High numbers risk server throttling/blocking. Use with caution!")
                break # Valid input
        except ValueError:
            print("Invalid input. Please enter a whole number.")

    # 2. Download Path
    path_str = input(f"Enter download directory path (leave blank to save in current directory '{os.getcwd()}'): ").strip()
    settings['path'] = path_str if path_str else "." # Use '.' for current dir if empty

    # 3. Browser for Cookies
    common_browsers = ['firefox', 'chrome', 'edge', 'brave', 'safari', 'opera']
    while True:
        browser_str = input(f"Enter browser to use for cookies ({', '.join(common_browsers)}) [Default=firefox]: ").strip().lower()
        if not browser_str:
            settings['browser'] = 'firefox'
            break
        elif browser_str in common_browsers:
            settings['browser'] = browser_str
            break
        else:
             # Allow potentially unsupported browsers but warn
             print(f"Warning: Browser '{browser_str}' might not be directly supported by yt-dlp's --cookies-from-browser. Trying anyway.")
             settings['browser'] = browser_str
             break

    # 4. Download Type
    while True:
        print("\nSelect download type:")
        print("  1: Audio and Video (Default)")
        print("  2: Video Only")
        print("  3: Audio Only (MP3)")
        type_choice = input("Enter choice (1/2/3) [Default=1]: ").strip()

        if not type_choice or type_choice == '1':
            settings['type'] = 'both'
            break
        elif type_choice == '2':
            settings['type'] = 'video'
            break
        elif type_choice == '3':
            settings['type'] = 'audio'
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

    print("\nSettings confirmed:")
    print(f"  Concurrent Downloads: {settings['count']}")
    print(f"  Download Path: {settings['path']}")
    print(f"  Cookie Browser: {settings['browser']}")
    print(f"  Download Type: {settings['type']}")
    print("-" * 30)
    return settings


def check_yt_dlp():
    """Checks if yt-dlp command is accessible."""
    print("Checking for yt-dlp...")
    try:
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True, check=True, encoding='utf-8')
        print(f"Found yt-dlp version: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("ERROR: 'yt-dlp' command not found. Make sure yt-dlp is installed and in your system's PATH.", file=sys.stderr)
        return False
    except subprocess.CalledProcessError as e:
        print(f"ERROR: 'yt-dlp --version' failed. Output:\n{e.stderr}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"An unexpected error occurred while checking for yt-dlp: {e}", file=sys.stderr)
        return False

def read_download_targets(filename):
    """
    Reads download targets from a file.
    Expected format per line: <output_filename_without_extension> <url>
    Returns a list of tuples: [(filename, url), ...]
    """
    targets = []
    print(f"\nReading download targets from '{filename}'...")
    line_num = 0
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line_num += 1
                line = line.strip()
                if not line or line.startswith('#'): # Skip empty lines and comments
                    continue
                parts = line.split(' ', 1)
                if len(parts) == 2:
                    output_filename_base = parts[0].strip()
                    url = parts[1].strip()
                    if output_filename_base and url:
                        targets.append((output_filename_base, url))
                    else:
                        print(f"WARNING: Skipping line {line_num} due to empty filename or URL after split: '{line}'", file=sys.stderr)
                else:
                    print(f"WARNING: Skipping line {line_num} due to incorrect format (expected 'filename URL'): '{line}'", file=sys.stderr)
        print(f"Found {len(targets)} valid download target(s).")
        return targets
    except FileNotFoundError:
        print(f"ERROR: Target file '{filename}' not found in the current directory.", file=sys.stderr)
        return None
    except Exception as e:
        print(f"An error occurred while reading the target file: {e}", file=sys.stderr)
        return None

def download_video(url, output_filename_base, output_dir, cookie_browser, download_type):
    """
    Downloads a single video/audio using yt-dlp with specified settings.
    Returns True on success, False on failure.
    """
    prefix = f"[{output_filename_base}] "
    print(prefix + "-" * 20)
    sys.stdout.write(prefix + f"Attempting download ({download_type}) for: {url}\n")
    sys.stdout.flush()

    # Ensure the output directory exists
    if output_dir != "." and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
            sys.stdout.write(prefix + f"Created output directory: {output_dir}\n")
            sys.stdout.flush()
        except OSError as e:
            sys.stderr.write(prefix + f"ERROR: Could not create directory '{output_dir}': {e}\n")
            sys.stderr.flush()
            return False

    # Construct the output template
    # For audio only, yt-dlp might change the extension based on --audio-format
    # So we let yt-dlp handle the final extension.
    output_template = f"{output_filename_base}.%(ext)s"
    full_output_path_template = os.path.join(output_dir, output_template)

    # Base command arguments
    command = [
        'yt-dlp',
        '--no-check-certificates',
        '--cookies-from-browser', cookie_browser,
        # '--verbose',
        '-o', full_output_path_template,
    ]

    # Add format specific arguments based on download_type
    if download_type == 'video':
        # Try to get the best video-only format. Might need audio stream for muxing depending on source.
        # Often 'bestvideo' requires 'bestaudio' to be downloaded separately and muxed.
        # A simpler approach for video-only might be a format that includes audio but primarily focuses on video quality,
        # or let yt-dlp choose the best MP4 which usually includes audio.
        # Let's stick to a common request: best quality MP4 if available, otherwise best.
        command.extend(['-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'])
        # If you truly want *only* the video stream (which might not play on its own):
        # command.extend(['-f', 'bestvideo'])
        sys.stdout.write(prefix + "Selecting video format (bestvideo*+bestaudio*/best).\n")
    elif download_type == 'audio':
        # Extract audio, convert to mp3
        command.extend(['-f', 'bestaudio/best', '-x', '--audio-format', 'mp3'])
        sys.stdout.write(prefix + "Selecting audio-only format (bestaudio/best), converting to mp3.\n")
    # else: download_type == 'both' -> use default yt-dlp format selection (usually best video+audio)

    # Add the URL at the end
    command.append(url)

    # Use shlex.join for safer printing of command with spaces/quotes
    # Though on Windows it might not look exactly like cmd pasteable command
    sys.stdout.write(prefix + f"Executing command: {shlex.join(command)}\n")
    sys.stdout.flush()

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')

        def stream_output(pipe, stream_type):
            try:
                for line in iter(pipe.readline, ''):
                    output_stream = sys.stdout if stream_type == 'stdout' else sys.stderr
                    # Add prefix only if line is not empty (prevents extra prefixes on blank lines)
                    if line.strip():
                       output_stream.write(prefix + line)
                    else:
                       output_stream.write(line) # Write empty lines as is
                    output_stream.flush()
            finally:
                pipe.close()

        stdout_thread = threading.Thread(target=stream_output, args=(process.stdout, 'stdout'))
        stderr_thread = threading.Thread(target=stream_output, args=(process.stderr, 'stderr'))
        stdout_thread.start()
        stderr_thread.start()

        stdout_thread.join()
        stderr_thread.join()
        return_code = process.wait()

        if return_code == 0:
            sys.stdout.write(prefix + f"Successfully downloaded.\n")
            sys.stdout.write(prefix + "-" * 20 + "\n")
            sys.stdout.flush()
            return True
        else:
            sys.stderr.write(prefix + f"ERROR: yt-dlp exited with error code {return_code}.\n")
            sys.stderr.write(prefix + "-" * 20 + "\n")
            sys.stderr.flush()
            return False

    except FileNotFoundError:
         sys.stderr.write(prefix + "ERROR: 'yt-dlp' command not found during download attempt.\n")
         sys.stderr.flush()
         return False
    except Exception as e:
        sys.stderr.write(prefix + f"An unexpected error occurred during download: {e}\n")
        sys.stderr.flush()
        return False

# --- Main Execution ---
if __name__ == "__main__":
    print("--- Mediasite Batch Downloader (Interactive) ---")

    # Get settings interactively
    settings = get_interactive_settings()
    max_concurrent = settings['count']
    download_path = settings['path']
    browser_name = settings['browser']
    download_type = settings['type']

    if not check_yt_dlp():
        sys.exit(1)

    download_targets = read_download_targets(TARGET_FILE)

    if download_targets is None:
         sys.exit(1)

    if not download_targets:
        print("No valid download targets found in the file. Exiting.")
        sys.exit(0)

    success_count = 0
    fail_count = 0
    futures = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        print(f"\nSubmitting {len(download_targets)} downloads to the executor...")
        for filename, url in download_targets:
            # Pass all configured settings
            future = executor.submit(download_video, url, filename, download_path, browser_name, download_type)
            futures.append(future)

        print("All download tasks submitted. Waiting for completion...")
        processed_count = 0
        for future in concurrent.futures.as_completed(futures):
            processed_count += 1
            # Print completion message outside download_video for clarity
            print(f"\n--- Download Task {processed_count} of {len(download_targets)} Completed ---")
            try:
                success = future.result()
                if success:
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as exc:
                print(f"ERROR: A download task generated an exception: {exc}", file=sys.stderr)
                fail_count += 1

    print("\n--- Download Summary ---")
    print(f"Successfully downloaded: {success_count}")
    print(f"Failed downloads:      {fail_count}")
    print("------------------------")