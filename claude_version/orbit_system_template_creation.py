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

# Templates
TEMPLATES = {
    "project_template.md": """<%*
let title = tp.file.title;
if (title.startsWith("Untitled")) {
    title = await tp.system.prompt("Enter Project Title:");
    await tp.file.rename(title);
}
-%>
---
type: project
created: <% tp.date.now("YYYY-MM-DD") %>
satellites: []
domain: 
orbits: []
---

# <% title %>

## Overview

Project dashboard for <% title %>.

## Sources

```dataview
TABLE file.ctime as Created
FROM "[[<% title %>]]/9-source"
SORT file.ctime DESC
```

## Notes

```dataview
TABLE type, file.ctime as Created
FROM "[[<% title %>]]/0-inbox"
SORT file.ctime DESC
```

## Create New Note

This section contains buttons to create new notes in this project:

- [[+New Dust Note]]
- [[+New Source]]
""",
    "dust_template.md": """<%*
let title = tp.file.title;
if (title.startsWith("Untitled")) {
    title = await tp.system.prompt("Enter Note Title:");
    await tp.file.rename(title);
}
-%>
---
type: dust
created: <% tp.date.now("YYYY-MM-DD") %>
domain: 
orbits: []
satellites: []
---

# <% title %>

## Notes

New note.
""",
    "source_template.md": """<%*
let title = tp.file.title;
if (title.startsWith("Untitled")) {
    title = await tp.system.prompt("Enter Source Title:");
    await tp.file.rename(title);
}
-%>
---
type: source
created: <% tp.date.now("YYYY-MM-DD") %>
domain: 
orbits: []
satellites: []
source: 
---

# <% title %>

## Source

[Source Link]()

## Notes

Source material.
""",
    "domain_template.md": """<%*
let title = tp.file.title;
if (title.startsWith("Untitled")) {
    title = await tp.system.prompt("Enter Domain Name:");
    await tp.file.rename(title);
}
-%>
---
type: domain
created: <% tp.date.now("YYYY-MM-DD") %>
---

# <% title %> Dashboard

## Projects in <% title %> Domain

```dataview
TABLE 
  file.ctime as "Created",
  file.mtime as "Modified",
  satellites as "Sub-Notes"
FROM "DOMAIN_PATH"
WHERE type = "project"
SORT file.name ASC

TABLE 
  type as "Type",
  orbits as "Projects",
  file.ctime as "Created"
FROM "DOMAIN_PATH" OR "DOMAIN_PATH/.0-inbox"
SORT file.name ASC

""",
    # Template for creating new dust notes from project dashboards
    "new_dust_template.md": """<%*
let title = await tp.system.prompt("Enter Note Title:");
await tp.file.rename(title);
let parentFolder = tp.file.folder(true);
let parentProject = parentFolder.split('/').pop();
-%>
---
type: dust
created: <% tp.date.now("YYYY-MM-DD") %>
domain: 
orbits: [<% parentProject %>]
satellites: []
---

# <% title %>

## Notes

New note orbiting <% parentProject %>.
""",
    # Template for creating new source notes from project dashboards
    "new_source_template.md": """<%*
let title = await tp.system.prompt("Enter Source Title:");
await tp.file.rename(title);
let parentFolder = tp.file.folder(true);
let parentProject = parentFolder.split('/').pop();
-%>
---
type: source
created: <% tp.date.now("YYYY-MM-DD") %>
domain: 
orbits: [<% parentProject %>]
satellites: []
source: 
---

# <% title %>

## Source

[Source Link]()

## Notes

Source material for <% parentProject %>.
""",
    # Template for creating new projects
    "new_project_template.md": """<%*
let title = await tp.system.prompt("Enter Project Name:");
await tp.file.rename(title);
let parentFolder = tp.file.folder(true);
let domainName = parentFolder.split('-').pop();
-%>
---
type: project
created: <% tp.date.now("YYYY-MM-DD") %>
satellites: []
domain: <% parentFolder %>
orbits: [<% domainName %>]
---

# <% title %>

## Overview

Project dashboard for <% title %>.

## Sources

```dataview
TABLE file.ctime as Created
FROM "[[<% title %>]]/9-source"
SORT file.ctime DESC
```

## Notes

```dataview
TABLE type, file.ctime as Create 
FROM "[[<% title %>]]/0-inbox"
SORT file.ctime DESC
```

## Create New Note

This section contains buttons to create new notes in this project:

- [[+New Dust Note]]
- [[+New Source]]
"""
}

def create_templates():
    """Create template files in the vault"""
    template_dir = os.path.join(VAULT_PATH, "templates")
    
    # Create templates directory if it mainesn't exist
    if not os.path.exists(template_omair):
        os.makeirs(template_dir)
        logger.info(f"Created templates directory: {template_dir}")
    
    # Create each template file
    for template_name, template_content in TEMPLATES.items():
        template_path = os.path.join(template_dir, template_name)
        
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

# Script to create domain buttons for quick access
def create_domain_buttons():
    """Create a note with buttons for all domains"""
    buttons_content = """# ORBIT Domain Buttons

Click any button below to navigate to the domain dashboard:

"""
    
    # Add buttons for each domain
    for domain_num, domain_name in sorted(DOMAINS.items()):
        buttons_content += f"- [[{domain_num}-{domain_name}/{domain_name}|{domain_num} {domain_name}]]\n"
    
    # Add instructions for creating new notes
    buttons_content += """
## Creating New Notes

To create a new note:
1. Navigate to the appropriate domain or project
2. Use the "+New Note" or "+New Project" buttons at the bottom of the dashboard

## Quick Create

- [[+New Thought]]
- [[+New Project]]
- [[+New Source]]
"""
    
    # Write the buttons file
    buttons_path = os.path.join(VAULT_PATH, "ORBIT-Navigation.md")
    try:
        with open(buttons_path, 'w', encoding='utf-8') as f:
            f.write(buttons_content)
        logger.info(f"Created domain buttons at: {buttons_path}")
    except Exception as e:
        logger.error(f"Error creating domain buttons: {str(e)}")

if __name__ == "__main__":
    create_templates()
    create_domain_buttons()
    logger.info("Template creation complete")