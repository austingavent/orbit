import os
import re
import time
import yaml
import logging
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    # Set this to your Obsidian vault path (corrected)
    VAULT_PATH = "/Users/austinavent/Library/CloudStorage/Dropbox/Areas/DASR/DASR"
    
    # Domain folders (hundreds) - Updated with all domains
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
    
    # Project numbering increment
    PROJECT_INCREMENT = 10
    
    # Reserved satellite numbers
    INBOX_NUMBER = "0"
    SOURCE_NUMBER = "9"
    
    # Maximum satellites per project (excluding inbox and source)
    MAX_SATELLITES = 8
    
    # Hidden inbox directory name
    INBOX_DIR = ".0-inbox"
    
    # Minimum age of file before MOVING (in minutes) - Made configurable
    MIN_FILE_AGE = 1
    
    # Template paths
    TEMPLATES = {
        "project": "templates/project_template.md",
        "dust": "templates/dust_template.md",
        "source": "templates/source_template.md",
        "domain": "templates/domain_template.md"
    }


class OrbitSystem:
    def __init__(self, vault_path):
        self.vault_path = Path(vault_path)
        # Load templates first so they're available for domain creation
        self.templates = self._load_templates()
        # Then load domains
        self.domains = self._load_domains()
        # Track file creation times
        self.file_creation_times = {}
    
    def _load_templates(self):
        """Load template files"""
        templates = {}
        
        # Default templates if files not found - Updated to use Templater syntax
        default_templates = {
            "project": """---
type: project
created: <% tp.date.now("YYYY-MM-DD") %>
satellites: []
domain: 
orbits: []
---

# <% tp.file.title %>

## Overview

Project dashboard for <% tp.file.title %>.

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

## Create New Note

This section contains buttons to create new notes in this project:

- [[Creating a new note in this project|+New Dust Note]]
- [[Creating a new source note|+New Source]]
""",
            "dust": """---
type: dust
created: <% tp.date.now("YYYY-MM-DD") %>
domain: 
orbits: []
satellites: []
---

# <% tp.file.title %>

## Notes

New note.
""",
            "source": """---
type: source
created: <% tp.date.now("YYYY-MM-DD") %>
domain: 
orbits: []
satellites: []
source: 
---

# <% tp.file.title %>

## Source

[Source Link]()

## Notes

Source material.
""",
            "domain": """---
type: domain
created: <% tp.date.now("YYYY-MM-DD") %>
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

## Notes in Inbox

```dataview
TABLE type, orbits as "Projects", created
FROM "DOMAIN_PATH/.0-inbox"
WHERE type != "project" AND type != "domain"
SORT created DESC
LIMIT 10
```

## Recent Notes in Projects

```dataview
TABLE type, orbits as "Projects", created
FROM "DOMAIN_PATH"
WHERE type != "project" AND type != "domain"
SORT created DESC
LIMIT 10
```

## Create New Project

- [[Creating a new project|+New Project]]
"""
        }
        
        # Try to load template files
        template_dir = os.path.join(self.vault_path, "templates")
        if not os.path.exists(template_dir):
            os.makedirs(template_dir)
            logger.info(f"Created templates directory: {template_dir}")
        
        for template_type, template_path in Config.TEMPLATES.items():
            full_path = os.path.join(self.vault_path, template_path)
            try:
                if os.path.exists(full_path):
                    with open(full_path, 'r', encoding='utf-8') as f:
                        templates[template_type] = f.read()
                else:
                    # Create the template with default content
                    template_content = default_templates.get(template_type, '')
                    if template_content:
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)
                        with open(full_path, 'w', encoding='utf-8') as f:
                            f.write(template_content)
                        templates[template_type] = template_content
                        logger.info(f"Created template: {full_path}")
            except Exception as e:
                logger.error(f"Error with template {template_path}: {str(e)}")
                templates[template_type] = default_templates.get(template_type, '')
        
        return templates
    
    def _load_domains(self):
        """Load all domain directories from the vault"""
        domains = {}
        
        # First add configured domains
        for domain_num, domain_name in Config.DOMAINS.items():
            domains[domain_num] = domain_name
            
            # Create domain directory if it doesn't exist
            domain_dir = os.path.join(self.vault_path, f"{domain_num}-{domain_name}")
            if not os.path.exists(domain_dir):
                os.makedirs(domain_dir)
                logger.info(f"Created domain directory: {domain_dir}")
                
                # Create domain dashboard
                self._create_domain_dashboard(domain_dir, domain_name)
            
            # Ensure hidden inbox exists
            inbox_path = os.path.join(domain_dir, Config.INBOX_DIR)
            if not os.path.exists(inbox_path):
                os.makedirs(inbox_path)
                logger.info(f"Created inbox directory: {inbox_path}")
        
        # Then scan for any additional domain directories that might exist
        for item in os.listdir(self.vault_path):
            if os.path.isdir(os.path.join(self.vault_path, item)) and re.match(r'^\d{3}-', item):
                domain_number = item.split('-')[0]
                domain_name = item.split('-')[1]
                
                # Add to domains if not already there
                if domain_number not in domains:
                    domains[domain_number] = domain_name
                
                # Ensure hidden inbox exists
                inbox_path = os.path.join(self.vault_path, item, Config.INBOX_DIR)
                if not os.path.exists(inbox_path):
                    os.makedirs(inbox_path)
                    logger.info(f"Created inbox directory: {inbox_path}")
        
        return domains
    
    def _create_domain_dashboard(self, domain_dir, domain_name):
        """Create domain directory structure without markdown files"""
        # Create hidden inbox if it doesn't exist
        inbox_path = os.path.join(domain_dir, Config.INBOX_DIR)
        if not os.path.exists(inbox_path):
            os.makedirs(inbox_path)
            logger.info(f"Created domain inbox directory: {inbox_path}")
        
        # Get template
        template = self.templates.get('domain', '')
        if not template:
            logger.warning("Domain template not found")
            return
        
        # Create dashboard file path
        dashboard_path = os.path.join(domain_dir, f"{domain_name}.md")
        if os.path.exists(dashboard_path):
            return
            
        # Perform template substitution
        content = template
        content = content.replace('DOMAIN_NAME', domain_name)
        content = content.replace('DOMAIN_PATH', os.path.basename(domain_dir))
        
        # Write the file
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logger.info(f"Created domain dashboard: {dashboard_path}")
    
    def process_file(self, file_path):
        """Process a file when it's created or modified"""
        file_path = Path(file_path)
        
        # Only process markdown files
        if file_path.suffix.lower() != '.md':
            return
        
        # Track file creation time if first time seeing it
        if str(file_path) not in self.file_creation_times:
            self.file_creation_times[str(file_path)] = datetime.now()
            logger.info(f"Tracking new file: {file_path}")
        
        logger.info(f"Processing file: {file_path}")
        
        try:
            # Read the file and extract frontmatter
            frontmatter, content = self._read_file_with_frontmatter(file_path)
            if not frontmatter:
                return
            
            # Process domain property first
            domain_value = frontmatter.get('domain', None)
            if domain_value:
                self._process_domain(file_path, frontmatter, domain_value)
            
            # IMMEDIATELY create project directories for orbit relationships
            if 'orbits' in frontmatter and frontmatter['orbits']:
                # First, create all necessary directories without moving the file
                self._create_orbit_projects(file_path, frontmatter)
                
                # Check if file is old enough to move
                file_age = datetime.now() - self.file_creation_times[str(file_path)]
                if file_age >= timedelta(minutes=Config.MIN_FILE_AGE):
                    # Only move if file is old enough
                    self._process_orbits(file_path, frontmatter, move_file=True)
                else:
                    logger.info(f"File {file_path} has orbits but is too new to move, waiting...")
            
            # Process satellites relationship
            if 'satellites' in frontmatter and frontmatter['satellites']:
                self._process_satellites(file_path, frontmatter)
                
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
    
    def _read_file_with_frontmatter(self, file_path):
        """Read a file and extract frontmatter and content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Check if file has frontmatter
            if not content.startswith('---'):
                logger.info(f"No frontmatter found in {file_path}")
                return None, content
            
            # Extract frontmatter
            frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
            if not frontmatter_match:
                logger.info(f"No frontmatter found in {file_path}")
                return None, content
                
            frontmatter_yaml = frontmatter_match.group(1)
            remaining_content = content[frontmatter_match.end():]
            
            # Parse YAML - Handle templater syntax by replacing with actual values
            try:
                # Fix Templater syntax by replacing with actual values
                processed_yaml = self._fix_templater_syntax(frontmatter_yaml)
                frontmatter = yaml.safe_load(processed_yaml)
                
                if not frontmatter or not isinstance(frontmatter, dict):
                    logger.info(f"Invalid or empty frontmatter in {file_path}")
                    return None, content
            except Exception as e:
                logger.error(f"Error parsing YAML frontmatter in {file_path}: {str(e)}")
                # Try to fix common YAML errors
                fixed_yaml = self._attempt_yaml_fix(frontmatter_yaml)
                if fixed_yaml:
                    try:
                        frontmatter = yaml.safe_load(fixed_yaml)
                    except Exception as e2:
                        logger.error(f"Failed to fix YAML in {file_path}: {str(e2)}")
                        return None, content
                else:
                    return None, content
            
            return frontmatter, remaining_content
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return None, ""
    
    def _fix_templater_syntax(self, yaml_str):
        """Fix Templater syntax by replacing with actual values"""
        # Replace date template with actual date
        yaml_str = re.sub(r'<% tp\.date\.now\([^\)]*\) %>', datetime.now().strftime('%Y-%m-%d'), yaml_str)
        
        # Replace other templater tags with empty strings
        yaml_str = re.sub(r'<% [^%]+ %>', '', yaml_str)
        
        return yaml_str
    
    def _attempt_yaml_fix(self, yaml_str):
        """Attempt to fix common YAML syntax errors"""
        # Fix for unclosed brackets in satellites or orbits lists
        yaml_str = re.sub(r'satellites: *{([^}]*?)$', r'satellites: [\1]', yaml_str)
        yaml_str = re.sub(r'orbits: *{([^}]*?)$', r'orbits: [\1]', yaml_str)
        
        # Fix for Templater syntax
        yaml_str = self._fix_templater_syntax(yaml_str)
        
        return yaml_str
    
    def _process_domain(self, file_path, frontmatter, domain_value):
        """Process domain property to place file in correct domain"""
        # Check if this is a valid domain
        domain_folder = None
        domain_number = None
        domain_name = None
        
        # Handle different domain formats:
        # 1. "200-Health" (full format)
        # 2. "Health" (just name)
        # 3. "200" (just number)
        
        if '-' in domain_value:
            # Format is "200-Health"
            domain_parts = domain_value.split('-', 1)
            if domain_parts[0] and domain_parts[0].isdigit():
                domain_number = domain_parts[0]
                domain_name = domain_parts[1]
                domain_folder = f"{domain_number}-{domain_name}"
        elif domain_value.isdigit() and len(domain_value) == 3:
            # Format is just "200" - need to find corresponding name
            domain_number = domain_value
            for num, name in self.domains.items():
                if num == domain_number:
                    domain_name = name
                    domain_folder = f"{domain_number}-{domain_name}"
                    break
        else:
            # Format is just "Health" - need to find corresponding number
            domain_name = domain_value
            for num, name in self.domains.items():
                if name.lower() == domain_name.lower():
                    domain_number = num
                    domain_folder = f"{domain_number}-{name}"
                    break
        
        if not domain_folder:
            logger.warning(f"Invalid domain '{domain_value}' in {file_path}. Available domains: {', '.join([f'{k}-{v}' for k,v in self.domains.items()])}")
            return
        
        # Ensure domain folder exists
        domain_path = os.path.join(self.vault_path, domain_folder)
        if not os.path.exists(domain_path):
            os.makedirs(domain_path)
            logger.info(f"Created domain directory: {domain_path}")
            
            # Create hidden inbox
            inbox_path = os.path.join(domain_path, Config.INBOX_DIR)
            os.makedirs(inbox_path, exist_ok=True)
            logger.info(f"Created inbox directory: {inbox_path}")
            
            # Create domain dashboard
            self._create_domain_dashboard(domain_path, domain_name)

    def create_domain_landing_pages(self):
        """Create landing pages (directories only) for all domains"""
        for domain_num, domain_name in self.domains.items():
            domain_folder = f"{domain_num}-{domain_name}"
            domain_path = os.path.join(self.vault_path, domain_folder)
            
            # Create domain directory if it doesn't exist
            if not os.path.exists(domain_path):
                os.makedirs(domain_path)
                logger.info(f"Created domain landing page: {domain_path}")
                
                # Create hidden inbox
                inbox_path = os.path.join(domain_path, Config.INBOX_DIR)
                os.makedirs(inbox_path, exist_ok=True)
                logger.info(f"Created inbox directory: {inbox_path}")

    def _create_orbit_projects(self, file_path, frontmatter):
        """Create project directories for orbit relationships without moving the file"""
        orbits = frontmatter.get('orbits', [])
        if not orbits:
            return
            
        # Handle different formats
        if isinstance(orbits, str):
            orbits = [orbits]
        elif isinstance(orbits, dict):
            # Handle format like {item1, item2} which becomes a dict with keys
            orbits = list(orbits.keys())
            
        # Get domain from frontmatter or file path
        domain_value = frontmatter.get('domain', None)
        file_domain = self._get_domain_from_path(file_path)
        
        # Get direct relationship if specified
        direct = frontmatter.get('direct', None)
        
        # Create each orbit project directory
        for orbit in orbits:
            if orbit and isinstance(orbit, str):  # Validate orbit value
                self._create_orbit_project(file_path, orbit, domain_value or file_domain, direct == orbit)
    
    def _create_orbit_project(self, file_path, orbit, domain_folder, is_direct=False):
        """Create a project directory for an orbit relationship without moving any files"""
        if not orbit:
            return
            
        # Check if this is a designated project (has number)
        is_designated = re.match(r'^\d+', orbit) is not None
        
        # If no domain folder provided, try to determine it
        if not domain_folder:
            for domain_num, domain_name in self.domains.items():
                if orbit.lower() == domain_name.lower() or (is_designated and orbit.startswith(domain_num)):
                    domain_folder = f"{domain_num}-{domain_name}"
                    break
            
            if not domain_folder:
                # Try to find existing project with this name
                project_path = self._find_existing_project(orbit)
                if project_path:
                    domain_folder = self._get_domain_from_path(project_path)
                else:
                    # Use the first domain as default if none specified
                    domain_num, domain_name = next(iter(self.domains.items()))
                    domain_folder = f"{domain_num}-{domain_name}"
                    logger.warning(f"Using default domain {domain_folder} for orbit: {orbit}")
        
        # Ensure domain format is correct (e.g., "200-Health")
        if not re.match(r'^\d{3}-', domain_folder):
            for domain_num, domain_name in self.domains.items():
                if domain_folder.lower() == domain_name.lower():
                    domain_folder = f"{domain_num}-{domain_name}"
                    break
        
        # Create project folder and notes
        if is_designated:
            # This is a numbered project
            project_path = os.path.join(self.vault_path, domain_folder, orbit)
            
            # Create project dashboard if it doesn't exist
            project_name = orbit.split('-', 1)[1] if '-' in orbit else orbit
            project_note_path = os.path.join(project_path, f"{project_name}.md")
        else:
            # Check if this should be a numbered project (if orbital a domain)
            domain_name = domain_folder.split('-')[1]
            if orbit.lower() != domain_name.lower() and not is_designated:
                # Look for existing project
                existing_project = self._find_existing_project(orbit)
                if existing_project:
                    # Use existing project
                    project_path = os.path.dirname(existing_project)
                    project_note_path = existing_project
                else:
                    # Create a new floating project 
                    project_path = os.path.join(self.vault_path, domain_folder, Config.INBOX_DIR, orbit)
                    project_note_path = os.path.join(project_path, f"{orbit}.md")
            else:
                # This is a floating project
                project_path = os.path.join(self.vault_path, domain_folder, Config.INBOX_DIR, orbit)
                project_note_path = os.path.join(project_path, f"{orbit}.md")
        
        # Create the directories if they don't exist
        if not os.path.exists(project_path):
            os.makedirs(project_path, exist_ok=True)
            logger.info(f"Created project directory: {project_path}")
            
            # Create inbox folder
            inbox_path = os.path.join(project_path, f"{Config.INBOX_NUMBER}-inbox")
            os.makedirs(inbox_path, exist_ok=True)
            
            # Create source folder
            source_path = os.path.join(project_path, f"{Config.SOURCE_NUMBER}-source")
            os.makedirs(source_path, exist_ok=True)
        
        # Create project note if it doesn't exist
        if not os.path.exists(project_note_path):
            self._create_project_note(project_note_path, orbit, domain_folder)
            
            # Add the file as a satellite to the project note
            self._add_as_satellite(project_note_path, file_path)
    
    def _find_existing_project(self, project_name):
        """Find an existing project by name (case insensitive)"""
        for root, dirs, files in os.walk(self.vault_path):
            for file in files:
                if file.lower() == f"{project_name.lower()}.md":
                    return os.path.join(root, file)
        return None
    
    def _add_as_satellite(self, project_path, note_path):
        """Add a note as a satellite to a project note"""
        try:
            # Read the project file
            frontmatter, content = self._read_file_with_frontmatter(project_path)
            if not frontmatter:
                return
                
            # Get the note name without extension
            note_name = os.path.basename(note_path).replace('.md', '')
            
            # Get existing satellites
            satellites = frontmatter.get('satellites', [])
            if isinstance(satellites, str):
                satellites = [satellites]
                
            # Add note as satellite if not already there
            if note_name not in satellites:
                satellites.append(note_name)
                frontmatter['satellites'] = satellites
                
                # Update the project file
                self._update_frontmatter(project_path, frontmatter, content)
                logger.info(f"Added {note_name} as satellite to {project_path}")
        except Exception as e:
            logger.error(f"Error adding satellite to {project_path}: {str(e)}")
    
    def _update_frontmatter(self, file_path, frontmatter, content):
        """Update the frontmatter of a file"""
        try:
            # Create new frontmatter
            new_frontmatter_yaml = yaml.dump(frontmatter, default_flow_style=False)
            new_content = f"---\n{new_frontmatter_yaml}---\n{content}"
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(new_content)
                
            return True
            
        except Exception as e:
            logger.error(f"Error updating frontmatter in {file_path}: {str(e)}")
            return False
    
    def _get_domain_from_path(self, file_path):
        """Extract domain from file path"""
        file_parts = str(file_path).split(os.sep)
        for part in file_parts:
            if re.match(r'^\d{3}-', part):
                return part
        return None
    
    def _process_orbits(self, file_path, frontmatter, move_file=True):
        """Process orbits relationship from a note"""
        orbits = frontmatter.get('orbits', [])
        if not orbits:
            return
            
        # Handle different formats
        if isinstance(orbits, str):
            orbits = [orbits]
        elif isinstance(orbits, dict):
            # Handle format like {item1, item2} which becomes a dict with keys
            orbits = list(orbits.keys())
            
        # Get direct relationship if specified
        direct = frontmatter.get('direct', None)
        
        # Get domain from frontmatter or file path
        domain_value = frontmatter.get('domain', None)
        file_domain = self._get_domain_from_path(file_path)
        
        # Process each orbit
        for orbit in orbits:
            if orbit and isinstance(orbit, str):  # Validate orbit value
                self._handle_orbit_relationship(file_path, orbit, direct, domain_value or file_domain, move_file)
    
    def _handle_orbit_relationship(self, file_path, orbit, direct, domain_folder, move_file=True):
        """Handle a single orbit relationship"""
        if not orbit:
            return
            
        # Check if this is a designated project (has number)
        is_designated = re.match(r'^\d+', orbit) is not None
        
        # If no domain folder provided, try to determine it
        if not domain_folder:
            for domain_num, domain_name in self.domains.items():
                if orbit.lower() == domain_name.lower() or (is_designated and orbit.startswith(domain_num)):
                    domain_folder = f"{domain_num}-{domain_name}"
                    break
            
            if not domain_folder:
                # Try to find existing project
                project_path = self._find_existing_project(orbit)
                if project_path:
                    domain_folder = self._get_domain_from_path(project_path)
                else:
                    # Use the first domain as default
                    domain_num, domain_name = next(iter(self.domains.items()))
                    domain_folder = f"{domain_num}-{domain_name}"
                    logger.warning(f"Using default domain {domain_folder} for orbit: {orbit}")
        
        # Ensure domain format is correct (e.g., "200-Health")
        if not re.match(r'^\d{3}-', domain_folder):
            for domain_num, domain_name in self.domains.items():
                if domain_folder.lower() == domain_name.lower():
                    domain_folder = f"{domain_num}-{domain_name}"
                    break
        
        # Get project paths
        if is_designated:
            # This is a numbered project
            project_path = os.path.join(self.vault_path, domain_folder, orbit)
            project_name = orbit.split('-', 1)[1] if '-' in orbit else orbit
        else:
            # Look for existing project
            existing_project = self._find_existing_project(orbit)
            if existing_project:
                project_path = os.path.dirname(existing_project)
                project_name = orbit
            else:
                # This is a floating project
                project_path = os.path.join(self.vault_path, domain_folder, Config.INBOX_DIR, orbit)
                project_name = orbit
        
        # Move the file if requested
        if move_file:
            # Handle direct relationship or determine where the file should go
            if direct and direct != '*':
                # Move to the directly specified orbit
                if direct == orbit:
                    self._move_file_to_project(file_path, project_path)
            elif direct == '*':
                # Move to all orbit directories (create copies or links)
                self._move_file_to_project(file_path, project_path)
            else:
                # Default behavior - move to the first orbit or the specified direct orbit
                if direct:
                    # Find the direct project
                    direct_project = self._find_existing_project(direct)
                    if direct_project:
                        direct_path = os.path.dirname(direct_project)
                        self._move_file_to_project(file_path, direct_path)
                    else:
                        # Move to first orbit
                        self._move_file_to_project(file_path, project_path)
                else:
                    # Move to first orbit
                    self._move_file_to_project(file_path, project_path)
    
    def _move_file_to_project(self, file_path, project_path):
        """Move a file to the appropriate project folder"""
        # Determine if file is a source, or should go to inbox
        frontmatter, _ = self._read_file_with_frontmatter(file_path)
        if not frontmatter:
            # Default to dust if no frontmatter
            note_type = 'dust'
        else:
            note_type = frontmatter.get('type', 'dust')
        
        if note_type == 'source':
            # Move to source folder
            target_dir = os.path.join(project_path, f"{Config.SOURCE_NUMBER}-source")
        else:
            # Move to inbox folder
            target_dir = os.path.join(project_path, f"{Config.INBOX_NUMBER}-inbox")
        
        # Create directory if it doesn't exist
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
        
        # Create target path
        target_path = os.path.join(target_dir, file_path.name)
        
        # Check if source and target are the same
        if os.path.abspath(file_path) == os.path.abspath(target_path):
            logger.info(f"File {file_path} is already in the correct location")
            return
            
        # Move the file
        try:
            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            # Rename (move) the file
            os.rename(file_path, target_path)
            logger.info(f"Moved {file_path} to {target_path}")
            
            # Update the tracking time for the new path
            self.file_creation_times[str(target_path)] = self.file_creation_times.get(str(file_path), datetime.now())
            # Remove the old path from tracking
            if str(file_path) in self.file_creation_times:
                del self.file_creation_times[str(file_path)]
                
        except Exception as e:
            logger.error(f"Error moving file {file_path} to {target_path}: {str(e)}")
    
    def _process_satellites(self, file_path, frontmatter):
        """Process satellites relationship from a project note"""
        satellites = frontmatter.get('satellites', [])
        if not satellites:
            return
            
        # Handle different formats
        if isinstance(satellites, str):
            satellites = [satellites]
        elif isinstance(satellites, dict):
            # Handle format like {item1, item2} which becomes a dict with keys
            satellites = list(satellites.keys())
            
        # Get project folder and name
        project_folder = os.path.dirname(file_path)
        project_name = os.path.basename(file_path).replace('.md', '')
        
        # Process each satellite
        for satellite in satellites:
            if satellite and isinstance(satellite, str):  # Validate satellite value
                self._handle_satellite_relationship(file_path, project_folder, project_name, satellite)
    
    def _handle_satellite_relationship(self, file_path, project_folder, project_name, satellite):
        """Handle a single satellite relationship"""
        # Create satellite note if it doesn't exist
        satellite_name = f"{satellite}.md"
        
        # Ensure the inbox directory exists
        inbox_path = os.path.join(project_folder, f"{Config.INBOX_NUMBER}-inbox")
        if not os.path.exists(inbox_path):
            os.makedirs(inbox_path, exist_ok=True)
            
        satellite_path = os.path.join(inbox_path, satellite_name)
        
        if not os.path.exists(satellite_path):
            # Get domain from project path
            domain_folder = self._get_domain_from_path(project_folder)
            
            # Create a new note
            self._create_satellite_note(satellite_path, satellite, project_name, domain_folder)
            logger.info(f"Created satellite note: {satellite_path}")
            
            # Track the new file's creation time
            self.file_creation_times[str(satellite_path)] = datetime.now()
    
    def _create_project_note(self, file_path, project_name, domain_folder):
        """Create a new project note"""
        try:
            # Get the template
            template = self.templates.get('project', '')
            if not template:
                logger.warning("Project template not found, using default template")
                template = """---
type: project
created: <% tp.date.now("YYYY-MM-DD") %>
satellites: []
domain: DOMAIN_VALUE
orbits: []
---

# <% tp.file.title %>

## Overview

Project dashboard for <% tp.file.title %>.

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

## Create New Note

This section contains buttons to create new notes in this project:

- [[Creating a new note in this project|+New Dust Note]]
- [[Creating a new source note|+New Source]]
"""
            
            # Determine if this is a designated project
            is_domain = False
            for domain_num, domain_name in self.domains.items():
                if project_name.lower() == domain_name.lower():
                    is_domain = True
                    break
            
            # Clean project name (remove numbering if present)
            clean_project_name = project_name
            if re.match(r'^\d+', project_name) and '-' in project_name:
                clean_project_name = project_name.split('-', 1)[1]
            
            # Set values for template substitution
            current_date = datetime.now().strftime('%Y-%m-%d')
            project_path = os.path.dirname(file_path)
            
            # Get domain value
            domain_value = domain_folder
            if domain_folder and re.match(r'^\d{3}-', domain_folder):
                domain_number = domain_folder.split('-')[0]
                domain_name = domain_folder.split('-')[1]
                domain_value = f"{domain_number}-{domain_name}"
            
            # Perform template substitution
            content = template
            content = content.replace('<% tp.date.now("YYYY-MM-DD") %>', current_date)
            content = content.replace('<% tp.file.title %>', clean_project_name)
            content = content.replace('PROJECT_PATH', project_path)
            content = content.replace('DOMAIN_VALUE', domain_value)
            
            # Handle orbit relationship to domain
            if not is_domain and domain_folder:
                domain_name = domain_folder.split('-')[1]
                # Update orbits in YAML if present
                yaml_match = re.search(r'orbits: *(\[\]|\[\S+\])', content)
                if yaml_match:
                    content = content.replace(yaml_match.group(1), f"[{domain_name}]")
                else:
                    # Add orbit relationship if not present
                    content = content.replace('domain: DOMAIN_VALUE', f'domain: {domain_value}\norbits: [{domain_name}]')
            
            # Create parent directories if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info(f"Created project note: {file_path}")
            
            # Track the new file's creation time
            self.file_creation_times[str(file_path)] = datetime.now()
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating project note {file_path}: {str(e)}")
            return False
    
    def _create_satellite_note(self, file_path, note_name, parent_project, domain_folder=None):
        """Create a new satellite note"""
        try:
            # Get the template
            template = self.templates.get('dust', '')
            if not template:
                logger.warning("Dust template not found, using default template")
                template = """---
type: dust
created: <% tp.date.now("YYYY-MM-DD") %>
domain: DOMAIN_VALUE
orbits: PARENT_PROJECT
satellites: []
---

# <% tp.file.title %>

## Notes

New dust note orbiting PARENT_PROJECT.
"""
            
            # Set values for template substitution
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # Get domain value
            domain_value = ""
            if domain_folder and re.match(r'^\d{3}-', domain_folder):
                domain_value = domain_folder
            
            # Perform template substitution
            content = template
            content = content.replace('<% tp.date.now("YYYY-MM-DD") %>', current_date)
            content = content.replace('<% tp.file.title %>', note_name)
            content = content.replace('PARENT_PROJECT', parent_project)
            content = content.replace('DOMAIN_VALUE', domain_value)
            
            # Create parent directories if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logger.info(f"Created satellite note: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating satellite note {file_path}: {str(e)}")
            return False
    
    def assign_project_number(self, domain_folder, project_name):
        """Assign a new project number to a project in a domain"""
        # Get domain number
        domain_num = domain_folder.split('-')[0]
        
        # Find existing projects in this domain
        existing_projects = []
        domain_path = os.path.join(self.vault_path, domain_folder)
        for item in os.listdir(domain_path):
            if os.path.isdir(os.path.join(domain_path, item)) and re.match(r'^\d+', item):
                existing_projects.append(int(re.match(r'^\d+', item).group()))
        
        # Sort existing projects
        existing_projects.sort()
        
        # Calculate next project number
        if not existing_projects:
            next_number = int(domain_num) + Config.PROJECT_INCREMENT
        else:
            next_number = existing_projects[-1] + Config.PROJECT_INCREMENT
            
        return str(next_number)
    
    def promote_project(self, project_path):
        """Promote a floating project to a designated project with number"""
        # Get domain from project path
        domain_folder = self._get_domain_from_path(project_path)
        if not domain_folder:
            logger.error(f"Cannot determine domain for project: {project_path}")
            return False
            
        # Get project name
        project_name = os.path.basename(project_path)
        
        # Assign a project number
        project_number = self.assign_project_number(domain_folder, project_name)
        new_project_name = f"{project_number}-{project_name}"
        
        # Create new project path
        domain_path = os.path.join(self.vault_path, domain_folder)
        new_project_path = os.path.join(domain_path, new_project_name)
        
        # Move the project
        try:
            os.rename(project_path, new_project_path)
            logger.info(f"Promoted project {project_path} to {new_project_path}")
            
            # Update the project note
            project_note_path = os.path.join(new_project_path, f"{project_name}.md")
            new_note_path = os.path.join(new_project_path, f"{project_name}.md")
            
            if os.path.exists(project_note_path):
                # Read the note
                frontmatter, content = self._read_file_with_frontmatter(project_note_path)
                if frontmatter:
                    # Update the project note (path, etc)
                    self._update_project_after_promotion(new_note_path, frontmatter, content, new_project_name)
            
            return True
        except Exception as e:
            logger.error(f"Error promoting project {project_path}: {str(e)}")
            return False
    
    def _update_project_after_promotion(self, note_path, frontmatter, content, new_project_name):
        """Update a project note after promotion"""
        # Update frontmatter
        if 'type' in frontmatter:
            frontmatter['type'] = 'project'
        
        # Write back to file
        self._update_frontmatter(note_path, frontmatter, content)


class OrbitEventHandler(FileSystemEventHandler):
    def __init__(self, orbit_system):
        self.orbit_system = orbit_system
        self.last_processed = {}  # Track last processed time for each file
        
    def on_modified(self, event):
        if event.is_directory:
            return
            
        file_path = event.src_path
        
        # Only process markdown files
        if not file_path.endswith('.md'):
            return
            
        # Avoid processing the same file multiple times in rapid succession
        current_time = time.time()
        last_time = self.last_processed.get(file_path, 0)
        
        if current_time - last_time < 1:  # 1-second debounce
            return
            
        self.last_processed[file_path] = current_time
        
        # Process the file
        self.orbit_system.process_file(file_path)
        
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.md'):
            self.orbit_system.process_file(event.src_path)

def main():
    # Get vault path from config
    vault_path = Config.VAULT_PATH
    
    if not os.path.exists(vault_path):
        logger.error(f"Vault path does not exist: {vault_path}")
        return
        
    # Initialize the ORBIT system
    orbit_system = OrbitSystem(vault_path)
    
    # Create domain landing pages (directories only)
    orbit_system.create_domain_landing_pages()
    
    # Create event handler and observer
    event_handler = OrbitEventHandler(orbit_system)
    observer = Observer()
    
    # Schedule watching the vault directory
    observer.schedule(event_handler, vault_path, recursive=True)
    observer.start()
    
    logger.info(f"Started watching Obsidian vault at: {vault_path}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        
    observer.join()

if __name__ == "__main__":
    main()