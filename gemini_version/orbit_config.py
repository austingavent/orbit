# ORBIT System Configuration (Gemini Version)

from pathlib import Path

# Path to your Obsidian vault
VAULT_PATH = "/Users/austinavent/Library/CloudStorage/Dropbox/Areas/DASR/DASR"

# Domain folders (hundreds)
DOMAINS = {
    "000": "Origins",
    "100": "Self",
    "200": "Health",
    "300": "Philosophy",
    "400": "Expression",
    "500": "Culture",
    "600": "People",
    "700": "Environment",
    "800": "Work_systems",
    "900": "Meta_resources",
    # Add more domains as needed
}

# Project numbering increment
PROJECT_INCREMENT = 10

# Reserved satellite numbers
INBOX_NUMBER = "0"
SOURCE_NUMBER = "9"

# Maximum satellites per project (excluding inbox and source)
MAX_SATELLITES = 8

# Hidden inbox directory name
HIDDEN_INBOX = ".0-inbox"

# Log settings
LOG_LEVEL = "INFO"
LOG_FILE = "orbit_manager.log"  # Updated for Gemini version

# File watching settings
DEBOUNCE_TIME = 1  # seconds

# Property names for frontmatter
PROP_OBJECT = "object"
PROP_ORBIT = "orbit"
PROP_STAGE = "stage"
PROP_DOMAIN = "domain"

# Stage directories
STAGE_DIRS = {
    0: ".0-inbox",  # Origin/Inbox
    1: "1-self",    # Self
    2: "2-structure" # Structure
}

# Source directory name
SOURCE_DIR_NAME = "9-source"

def get_vault_path() -> Path:
    """Returns the vault path as a Path object."""
    return Path(VAULT_PATH)

def get_fallback_path() -> Path:
    """Returns the fallback path for unprocessed notes."""
    return Path(VAULT_PATH) / ".orbit" / "fallback"

# Global configuration dictionary
config = {
    "vault_path": VAULT_PATH,
    "domains": DOMAINS,
    "project_increment": PROJECT_INCREMENT,
    "inbox_number": INBOX_NUMBER,
    "source_number": SOURCE_NUMBER,
    "max_satellites": MAX_SATELLITES,
    "hidden_inbox": HIDDEN_INBOX,
    "log_level": LOG_LEVEL,
    "log_file": LOG_FILE,
    "debounce_time": DEBOUNCE_TIME,
    "prop_object": PROP_OBJECT,
    "prop_orbit": PROP_ORBIT,
    "prop_stage": PROP_STAGE,
    "prop_domain": PROP_DOMAIN,
    "stage_dirs": STAGE_DIRS,
    "source_dir_name": SOURCE_DIR_NAME,
    "get_vault_path": get_vault_path,
    "get_fallback_path": get_fallback_path
}