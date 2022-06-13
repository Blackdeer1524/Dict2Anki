import os
from pathlib import Path
from platform import system

CURRENT_WORKING_DIR = Path(os.getcwd())
LOCAL_MEDIA_DIR = CURRENT_WORKING_DIR / "media"
HISTORY_FILE_PATH = CURRENT_WORKING_DIR / "history.json"
CONFIG_FILE_PATH = CURRENT_WORKING_DIR / "config.json"
USER_FOLDER = Path(os.path.expanduser("~"))
SYSTEM = system()
if SYSTEM == "Linux":
    MEDIA_DOWNLOADING_LOCATION = USER_FOLDER / ".local/share/Anki2/"
elif SYSTEM == "Windows":
    MEDIA_DOWNLOADING_LOCATION = USER_FOLDER / "AppData/Roaming/Anki2/"
else:
    MEDIA_DOWNLOADING_LOCATION = CURRENT_WORKING_DIR

if not MEDIA_DOWNLOADING_LOCATION.exists():
    MEDIA_DOWNLOADING_LOCATION = CURRENT_WORKING_DIR
