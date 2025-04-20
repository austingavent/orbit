import os
from pathlib import Path
import shutil
from orbit_config import config  # Import from same directory

def create_directory_structure():
    """Create the basic directory structure for the ORBIT system."""
    vault_path = Path(config["vault_path"])
    
    # Create templates directory
    templates_dir = vault_path / "Templates"
    templates_dir.mkdir(exist_ok=True)
    
    # Create domain directories with their structure
    for domain_num, domain_name in config["domains"].items():
        domain_dir = vault_path / f"{domain_num}-{domain_name}"
        domain_dir.mkdir(exist_ok=True)
        
        # Create stage directories in each domain
        for stage_num, stage_dir in config["stage_dirs"].items():
            (domain_dir / stage_dir).mkdir(exist_ok=True)
        
        # Create source directory
        (domain_dir / config["source_dir_name"]).mkdir(exist_ok=True)

    # Create templates
    create_templates(templates_dir)

def create_templates(templates_dir):
    """Create the standard templates for the ORBIT system."""
    # Project template
    project_template = """---
title: {{title}}
object: project
stage: 1
domain: {{domain}}
orbits: []
satellites: []
---

# {{title}}

## Overview
*Purpose and scope of this project*

## Sources
```dataview
TABLE stage, orbits
FROM "{{domain_path}}"
WHERE object = "source"
SORT stage DESC
```

## Supporting Notes
```dataview
TABLE stage
FROM "{{domain_path}}"
WHERE contains(orbits, "{{title}}")
SORT stage DESC
```
"""
    
    # Source template
    source_template = """---
title: {{title}}
object: source
stage: 9
domain: {{domain}}
orbits: {{parent_project}}
---

# {{title}}

## Source
[{{title}}]({{source_url}})

## Notes
Source material for {{parent_project}}.
"""
    
    # Regular note template
    note_template = """---
title: {{title}}
object: note
stage: 0
domain: {{domain}}
orbits: {{parent_project}}
---

# {{title}}

## Notes
*Your notes here*
"""

    # Write templates
    (templates_dir / "project.md").write_text(project_template)
    (templates_dir / "source.md").write_text(source_template)
    (templates_dir / "note.md").write_text(note_template)

def create_orbit_navigation():
    """Create the main navigation file for the ORBIT system."""
    vault_path = Path(config["vault_path"])
    nav_content = """# ORBIT Navigation

## Domains
"""
    
    # Add domain navigation
    for domain_num, domain_name in config["domains"].items():
        nav_content += f"- [[{domain_num}-{domain_name}/{domain_name}|{domain_num} {domain_name}]]\n"
    
    nav_content += """
## Quick Create
- [[+New Project]]
- [[+New Note]]
- [[+New Source]]
"""
    
    (vault_path / "ORBIT-Navigation.md").write_text(nav_content)

def main():
    """Main function to set up the ORBIT system."""
    print("Setting up ORBIT system...")
    
    # Create basic structure
    create_directory_structure()
    print("✓ Created directory structure")
    
    # Create navigation file
    create_orbit_navigation()
    print("✓ Created navigation file")
    
    print("\nORBIT system setup complete!")
    print("\nStructure created:")
    print("- Domain directories (000-Origins, 100-Self, etc.)")
    print("- Stage directories (.0-inbox, 1-self, 2-structure)")
    print("- Source directories (9-source)")
    print("- Templates directory with:")
    print("  - project.md")
    print("  - source.md")
    print("  - note.md")
    print("- ORBIT-Navigation.md")
    
    print("\nNext steps:")
    print("1. Install required Python packages: pip install PyYAML watchdog")
    print("2. Run the orbit manager: python orbit_manager.py")
    print("3. Start creating notes using the templates")

if __name__ == "__main__":
    main() 