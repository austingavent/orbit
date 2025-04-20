import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration - update this with your vault path
VAULT_PATH = "/Users/austinavent/Library/CloudStorage/Dropbox/Areas/DASR/DASR"

# Available domains
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
}

# Reserved satellite numbers
INBOX_NUMBER = "0"
SOURCE_NUMBER = "9"

# Hidden inbox directory name
INBOX_DIR = ".0-inbox"

def create_orbit_structure():
    """Create just the directory structure for the ORBIT system (no markdown files)"""
    # Create each domain directory
    for domain_num, domain_name in DOMAINS.items():
        domain_folder = f"{domain_num}-{domain_name}"
        domain_path = os.path.join(VAULT_PATH, domain_folder)
        
        # Create domain directory if it doesn't exist
        if not os.path.exists(domain_path):
            os.makedirs(domain_path)
            logger.info(f"Created domain directory: {domain_path}")
        
        # Create hidden inbox for domain
        domain_inbox = os.path.join(domain_path, INBOX_DIR)
        if not os.path.exists(domain_inbox):
            os.makedirs(domain_inbox)
            logger.info(f"Created domain inbox: {domain_inbox}")
        
        # Create a couple of example project structures in each domain
        example_project_num = int(domain_num) + 10
        example_project = f"{example_project_num}-Example_Project"
        project_path = os.path.join(domain_path, example_project)
        
        if not os.path.exists(project_path):
            os.makedirs(project_path)
            logger.info(f"Created example project: {project_path}")
            
            # Create project inbox
            inbox_path = os.path.join(project_path, f"{INBOX_NUMBER}-inbox")
            if not os.path.exists(inbox_path):
                os.makedirs(inbox_path)
                logger.info(f"Created project inbox: {inbox_path}")
            
            # Create project source folder
            source_path = os.path.join(project_path, f"{SOURCE_NUMBER}-source")
            if not os.path.exists(source_path):
                os.makedirs(source_path)
                logger.info(f"Created project source folder: {source_path}")

    logger.info("ORBIT directory structure created successfully!")

if __name__ == "__main__":
    # Check if vault path exists
    if not os.path.exists(VAULT_PATH):
        logger.error(f"Vault path does not exist: {VAULT_PATH}")
    else:
        create_orbit_structure()