import subprocess
import os
import sys
import concurrent.futures
import threading
import configparser

DEFAULT_CONFIG = {
    'Settings': {
        'Count': '1',
        'Path': '',
        'Browser': 'firefox'
    }
}
CONFIG_FILE = "config.txt"
TARGET_FILE = "urls.txt"

def read_config(filename):
    """Reads configuration from a file."""
    config = configparser.ConfigParser()
    config.read_dict(DEFAULT_CONFIG)
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            if not content.strip().startswith('['):
                content = "[Settings]\n" + content
                config.read_string(content)
            else:
                config.read(filename, encoding='utf-8')
        
    except Exception as e:
        config.read_dict(DEFAULT_CONFIG)

    settings = {}
    try:
        count_str = config.get('Settings', 'Count', fallback='1')
        settings['count'] = int(count_str)
        if settings['count'] < 1:
            settings['count'] = 1
    except ValueError:
        settings['count'] = 1

    path_str = config.get('Settings', 'Path', fallback='').strip()
    if path_str.startswith('"') and path_str.endswith('"'):
        path_str = path_str[1:-1]
    settings['path'] = path_str if path_str else "."

    settings['browser'] = config.get('Settings', 'Browser', fallback='firefox').strip().lower()
    valid_browsers = ['firefox', 'chrome', 'edge', 'brave', 'opera', 'safari']
    if settings['browser'] not in valid_browsers:
        pass

    return settings

def check_yt_dlp():
    """Checks if yt-dlp command is accessible."""
    try:
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True, check=True, encoding='utf-8')
        return True
    except FileNotFoundError:
        return False
    except subprocess.CalledProcessError:
        return False
    except Exception:
        return False


def read_download_targets(filename):
    """
    Reads download targets from a file.
    Expected format per line: <output_filename_without_extension> <url>
    Returns a list of tuples: [(filename, url), ...]
    """
    targets = []
    line_num = 0
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line_num += 1
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(' ', 1)
                if len(parts) == 2:
                    output_filename_base = parts[0].strip()
                    url = parts[1].strip()
                    if output_filename_base and url:
                        targets.append((output_filename_base, url))
                else:
                    pass
        return targets
    except FileNotFoundError:
        return None
    except Exception:
        return None


def download_video(url, output_filename_base, output_dir, cookie_browser):
    """
    Downloads a single video using yt-dlp with a specified base filename.
    Returns True on success, False on failure.
    """
    prefix = f"[{output_filename_base}] "

    if output_dir != "." and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError:
            return False

    full_output_path_template = os.path.join(output_dir, f"{output_filename_base}.%(ext)s")

    command = [
        'yt-dlp',
        '--no-check-certificates',
        '--cookies-from-browser', cookie_browser,
        '-o', full_output_path_template,
        url
    ]

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='replace')

        def stream_output(pipe, stream_type):
            try:
                for line in iter(pipe.readline, ''):
                    output_stream = sys.stdout if stream_type == 'stdout' else sys.stderr
                    output_stream.write(prefix + line)
                    output_stream.flush()
            finally:
                pipe.close()

        stdout_thread = threading.Thread(target=stream_output, args=(process.stdout, 'stdout'))
        stderr_thread = threading.Thread(target=stream_output, args=(process.stderr, 'stderr'))
        stdout_thread.start()
        stderr_thread.start()
        stdout_thread.join()
        stderr_thread.join()
        return process.wait() == 0
    except FileNotFoundError:
        return False
    except Exception:
        return False


if __name__ == "__main__":
    config = read_config(CONFIG_FILE)
    max_concurrent = config['count']
    download_path = config['path']
    browser_name = config['browser']

    if not check_yt_dlp():
        sys.exit(1)

    download_targets = read_download_targets(TARGET_FILE)

    if download_targets is None:
        sys.exit(1)

    if not download_targets:
        sys.exit(0)

    success_count = 0
    fail_count = 0
    futures = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        for filename, url in download_targets:
            future = executor.submit(download_video, url, filename, download_path, browser_name)
            futures.append(future)

        processed_count = 0
        for future in concurrent.futures.as_completed(futures):
            processed_count += 1
            try:
                success = future.result()
                if success:
                    success_count += 1
                else:
                    fail_count += 1
            except Exception:
                fail_count += 1

    sys.stdout.write(f"Successfully downloaded: {success_count}\n")
    sys.stdout.write(f"Failed downloads:      {fail_count}\n")
