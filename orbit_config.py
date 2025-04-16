# ORBIT System Configuration

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
LOG_FILE = "orbit_watchdog.log"

# File watching settings
DEBOUNCE_TIME = 1  # seconds