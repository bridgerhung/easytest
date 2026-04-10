import os
import time

def delete_old_files(folder, age_in_seconds):
    now = time.time()
    try:
        entries = list(os.scandir(folder))
    except OSError:
        return

    for entry in entries:
        try:
            # Never follow symlinks during cleanup.
            if entry.is_symlink() or not entry.is_file(follow_symlinks=False):
                continue

            stat_info = entry.stat(follow_symlinks=False)
            file_age = now - stat_info.st_mtime
            if file_age > age_in_seconds:
                os.unlink(entry.path)
        except OSError:
            continue
