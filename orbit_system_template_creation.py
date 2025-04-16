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

# Available domains for dropdown selection
DOMAINS = {
    "200": "Health",
    "300": "Work",
    "400": "Personal",
    # Add more as needed
}

# Templates
TEMPLATES = {
    "project_template.md": """---
type: project
created: CURRENT_DATE
satellites: []
domain: DOMAIN_OPTIONS
orbits: []
---

# PROJECT_TITLE

## Overview

Project dashboard for PROJECT_TITLE.

## Sources

```dataview
TABLE file.ctime as Created
FROM "PROJECT_PATH/9-source"
SORT file.ctime DESC
```

## Notes

```dataview
TABLE type, file.ctime as Created
FROM "PROJECT_PATH/0-inbox"
SORT file.ctime DESC
```
""",
    "dust_template.md": """---
type: dust
created: CURRENT_DATE
domain: DOMAIN_OPTIONS
orbits: PARENT_PROJECT
---

# NOTE_TITLE

## Notes

New dust note orbiting PARENT_PROJECT.
""",
    "source_template.md": """---
type: source
created: CURRENT_DATE
domain: DOMAIN_OPTIONS
orbits: PARENT_PROJECT
---

# SOURCE_TITLE

## Source

[SOURCE_TITLE](SOURCE_URL)

## Notes

Source material for PARENT_PROJECT.
""",
    "domain_template.md": """---
type: domain
created: CURRENT_DATE
---

# DOMAIN_NAME Dashboard

## Overview

Main dashboard for DOMAIN_NAME domain.

## Designated Projects

```dataview
TABLE satellites as "Sub-Projects", created
FROM "DOMAIN_PATH"
WHERE type = "project" AND contains(file.folder, "DOMAIN_PATH")
SORT file.name ASC
```

## Inbox Projects

```dataview
TABLE orbits as "Parent Projects", created
FROM "DOMAIN_PATH/.0-inbox"
WHERE type = "project"
SORT file.name ASC
```

## Recent Notes

```dataview
TABLE type, orbits as "Projects", created
FROM "DOMAIN_PATH"
WHERE type != "project" AND type != "domain"
SORT created DESC
LIMIT 10
```
"""
}

def create_templates():
    """Create template files in the vault"""
    template_dir = os.path.join(VAULT_PATH, "templates")
    
    # Create templates directory if it doesn't exist
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)
        logger.info(f"Created templates directory: {template_dir}")
    
    # Create domain option string for templates
    domain_options = []
    for num, name in DOMAINS.items():
        domain_options.append(f"{num}-{name}")
    domain_options_str = ", ".join(domain_options)
    
    # Create each template file
    for template_name, template_content in TEMPLATES.items():
        template_path = os.path.join(template_dir, template_name)
        
        # Replace domain options placeholder
        template_content = template_content.replace("DOMAIN_OPTIONS", domain_options_str)
        
        # Check if template already exists
        if os.path.exists(template_path):
            logger.info(f"Template already exists: {template_path}")
            continue
            
        # Create the template file
        try:
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(template_content)
            logger.info(f"Created template: {template_path}")
        except Exception as e:
            logger.error(f"Error creating template {template_path}: {str(e)}")

if __name__ == "__main__":
    create_templates()
    logger.info("Template creation complete")