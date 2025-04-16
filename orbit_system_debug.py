import os
import re
import yaml
import argparse
import logging
import shutil
import tempfile
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration - update with your vault path
VAULT_PATH = "/Users/austinavent/Library/CloudStorage/Dropbox/Areas/DASR/DASR"

# Domain folders
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

def validate_vault_path(vault_path):
    """Validate the vault path exists and has the correct structure"""
    if not os.path.exists(vault_path):
        logger.error(f"Vault path does not exist: {vault_path}")
        return False
        
    # Check for domain folders
    has_domains = False
    for item in os.listdir(vault_path):
        if os.path.isdir(os.path.join(vault_path, item)) and re.match(r'^\d{3}-', item):
            has_domains = True
            break
            
    if not has_domains:
        logger.warning("No domain folders found in vault. Expected folders like '200-health', '300-work', etc.")
        return False
        
    return True

def check_yaml_frontmatter(file_path):
    """Check if YAML frontmatter in a file is valid"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Check if file has frontmatter
        if not content.startswith('---'):
            logger.info(f"No frontmatter found in {file_path}")
            return False
        
        # Extract frontmatter
        frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            logger.info(f"No frontmatter found in {file_path}")
            return False
            
        frontmatter_yaml = frontmatter_match.group(1)
        
        # Try to parse YAML
        try:
            frontmatter = yaml.safe_load(frontmatter_yaml)
            if not frontmatter or not isinstance(frontmatter, dict):
                logger.error(f"Invalid or empty frontmatter in {file_path}")
                return False
            
            # Check for template placeholders
            has_placeholders = False
            for key, value in frontmatter.items():
                if isinstance(value, str) and re.search(r'[A-Z_]+', value):
                    logger.warning(f"Template placeholder found in {key}: {value}")
                    has_placeholders = True
            
            if has_placeholders:
                print("\nWarning: Template placeholders found in YAML. These should be replaced with actual values.")
            else:
                logger.info(f"Valid YAML frontmatter in {file_path}: {frontmatter}")
            
            return True
        except Exception as e:
            logger.error(f"Error parsing YAML frontmatter in {file_path}: {str(e)}")
            
            # Display the problematic YAML
            print("\nProblematic YAML:")
            print("-" * 40)
            print(frontmatter_yaml)
            print("-" * 40)
            
            # Analyze common YAML issues
            analyze_yaml_issues(frontmatter_yaml)
            
            return False
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return False

def analyze_yaml_issues(yaml_str):
    """Analyze common YAML syntax issues"""
    issues = []
    
    # Check for unclosed brackets
    if '{' in yaml_str and '}' not in yaml_str:
        issues.append("Unclosed curly brackets '{' (missing '}')")
    
    if '[' in yaml_str and ']' not in yaml_str:
        issues.append("Unclosed square brackets '[' (missing ']')")
    
    # Check for template placeholders
    if re.search(r'[A-Z_]+', yaml_str):
        issues.append("Template placeholders found (e.g., PROJECT_TITLE). These must be replaced with actual values.")
    
    # Check for indentation issues
    lines = yaml_str.split('\n')
    for i, line in enumerate(lines):
        if ':' in line and not line.strip().endswith(':'):
            next_line_indent = len(lines[i+1]) - len(lines[i+1].lstrip()) if i+1 < len(lines) else 0
            current_indent = len(line) - len(line.lstrip())
            
            if next_line_indent <= current_indent and '- ' not in lines[i+1].strip():
                issues.append(f"Possible indentation issue on line {i+2}")
    
    # Check for missing colons
    for i, line in enumerate(lines):
        if ': ' not in line and line.strip() and not line.strip().startswith('-') and not line.strip().startswith('#'):
            issues.append(f"Possible missing colon on line {i+1}: '{line.strip()}'")
    
    # Report issues
    if issues:
        print("\nPotential YAML Issues:")
        for issue in issues:
            print(f"- {issue}")
        
        print("\nSuggested fix:")
        fixed_yaml = fix_yaml_issues(yaml_str)
        print("-" * 40)
        print(fixed_yaml)
        print("-" * 40)
    else:
        print("No common YAML syntax issues detected. The error might be more complex.")

def fix_yaml_issues(yaml_str):
    """Attempt to fix common YAML syntax issues"""
    # Fix unclosed brackets in satellites or orbits lists
    yaml_str = re.sub(r'satellites: *{([^}]*?)$', r'satellites: [\1]', yaml_str)
    yaml_str = re.sub(r'orbits: *{([^}]*?)$', r'orbits: [\1]', yaml_str)
    
    # Replace template placeholders with dummy values
    yaml_str = re.sub(r'([A-Z_]+)', r'dummy_\1', yaml_str)
    
    return yaml_str

def check_orbit_relationships(vault_path):
    """Check orbit relationships across the vault"""
    orbit_relationships = {}
    satellite_relationships = {}
    issues = []
    
    # First pass: collect all orbit and satellite relationships
    for root, _, files in os.walk(vault_path):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                try:
                    frontmatter = extract_frontmatter(file_path)
                    if not frontmatter:
                        continue
                        
                    note_name = os.path.basename(file_path).replace('.md', '')
                    
                    # Process orbits
                    if 'orbits' in frontmatter:
                        orbits = frontmatter['orbits']
                        if isinstance(orbits, str):
                            orbits = [orbits]
                        elif isinstance(orbits, dict):
                            orbits = list(orbits.keys())
                        
                        if not isinstance(orbits, list):
                            issues.append(f"Invalid orbits format in {file_path}: {orbits}")
                            continue
                            
                        for orbit in orbits:
                            if orbit not in orbit_relationships:
                                orbit_relationships[orbit] = []
                            orbit_relationships[orbit].append(note_name)
                    
                    # Process satellites
                    if 'satellites' in frontmatter:
                        satellites = frontmatter['satellites']
                        if isinstance(satellites, str):
                            satellites = [satellites]
                        elif isinstance(satellites, dict):
                            satellites = list(satellites.keys())
                            
                        if not isinstance(satellites, list):
                            issues.append(f"Invalid satellites format in {file_path}: {satellites}")
                            continue
                            
                        satellite_relationships[note_name] = satellites
                        
                except Exception as e:
                    logger.error(f"Error processing {file_path}: {str(e)}")
    
    # Check bidirectional relationships
    for project, satellites in satellite_relationships.items():
        for satellite in satellites:
            # Check if satellite exists
            satellite_file = find_file_by_name(vault_path, satellite)
            if not satellite_file:
                issues.append(f"Satellite '{satellite}' referenced by project '{project}' doesn't exist")
                continue
                
            # Check if satellite orbits back to project
            satellite_frontmatter = extract_frontmatter(satellite_file)
            if not satellite_frontmatter or 'orbits' not in satellite_frontmatter:
                issues.append(f"Satellite '{satellite}' doesn't orbit back to project '{project}'")
                continue
                
            satellite_orbits = satellite_frontmatter['orbits']
            if isinstance(satellite_orbits, str):
                satellite_orbits = [satellite_orbits]
                
            if project not in satellite_orbits:
                issues.append(f"Bidirectional relationship broken: '{satellite}' doesn't orbit '{project}'")
    
    # Check if orbit targets exist
    for orbit, notes in orbit_relationships.items():
        orbit_file = find_project_file(vault_path, orbit)
        if not orbit_file:
            issues.append(f"Project '{orbit}' doesn't exist but is referenced by: {', '.join(notes)}")
    
    # Report issues
    if issues:
        print("\nOrbit Relationship Issues:")
        for issue in issues:
            print(f"- {issue}")
    else:
        print("No orbit relationship issues found.")
    
    return orbit_relationships, satellite_relationships

def find_file_by_name(vault_path, file_name):
    """Find a file by name anywhere in the vault"""
    if not file_name.endswith('.md'):
        file_name = f"{file_name}.md"
        
    for root, _, files in os.walk(vault_path):
        for file in files:
            if file == file_name:
                return os.path.join(root, file)
    
    return None

def find_project_file(vault_path, project_name):
    """Find a project file by name"""
    for root, dirs, files in os.walk(vault_path):
        # Check if project folder exists
        if os.path.basename(root) == project_name:
            # Look for project file in this folder
            for file in files:
                if file == f"{project_name}.md":
                    return os.path.join(root, file)
        
        # Check for project file directly
        for file in files:
            if file == f"{project_name}.md":
                return os.path.join(root, file)
    
    return None

def extract_frontmatter(file_path):
    """Extract YAML frontmatter from a markdown file with error handling"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Check if file has frontmatter
        if not content.startswith('---'):
            return None
        
        # Extract frontmatter
        frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            return None
            
        frontmatter_yaml = frontmatter_match.group(1)
        
        # Try to parse YAML
        try:
            frontmatter = yaml.safe_load(frontmatter_yaml)
            return frontmatter
        except Exception:
            return None
    except Exception:
        return None

def check_directory_structure(vault_path):
    """Check the ORBIT directory structure"""
    domain_folders = []
    project_folders = []
    issues = []
    
    # Scan for domain folders
    for item in os.listdir(vault_path):
        if os.path.isdir(os.path.join(vault_path, item)) and re.match(r'^\d{3}-', item):
            domain_folders.append(item)
    
    if not domain_folders:
        issues.append("No domain folders found (e.g., 200-Health)")
    
    # Check each domain folder
    for domain in domain_folders:
        domain_path = os.path.join(vault_path, domain)
        
        # Check for hidden inbox
        hidden_inbox = os.path.join(domain_path, ".0-inbox")
        if not os.path.exists(hidden_inbox):
            issues.append(f"Missing hidden inbox in domain {domain}")
        
        # Check for domain dashboard
        domain_name = domain.split('-')[1]
        dashboard_file = os.path.join(domain_path, f"{domain_name}.md")
        if not os.path.exists(dashboard_file):
            issues.append(f"Missing domain dashboard for {domain}")
        
        # Check project folders
        for item in os.listdir(domain_path):
            item_path = os.path.join(domain_path, item)
            if os.path.isdir(item_path) and re.match(r'^\d+', item) and item != ".0-inbox":
                project_folders.append(item)
                
                # Check project structure
                inbox = os.path.join(item_path, "0-inbox")
                source = os.path.join(item_path, "9-source")
                
                if not os.path.exists(inbox):
                    issues.append(f"Missing inbox folder in project {item}")
                
                if not os.path.exists(source):
                    issues.append(f"Missing source folder in project {item}")
                
                # Check project dashboard
                project_name = '-'.join(item.split('-')[1:]) if '-' in item else item
                dashboard_file = os.path.join(item_path, f"{project_name}.md")
                if not os.path.exists(dashboard_file):
                    issues.append(f"Missing project dashboard for {item}")
    
    # Report issues
    if issues:
        print("\nDirectory Structure Issues:")
        for issue in issues:
            print(f"- {issue}")
    else:
        print("Directory structure looks good.")
    
    return domain_folders, project_folders

def fix_orbit_issue(file_path):
    """Fix common orbit relationship issues in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Extract frontmatter
        frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            logger.error(f"No frontmatter found in {file_path}")
            return False
            
        frontmatter_yaml = frontmatter_match.group(1)
        file_content = content[frontmatter_match.end():]
        
        # Replace template placeholders with actual values
        frontmatter_yaml = replace_templates(frontmatter_yaml, file_path)
        
        # Fix common YAML issues
        fixed_yaml = fix_yaml_issues(frontmatter_yaml)
        
        # Try to parse the fixed YAML
        try:
            yaml.safe_load(fixed_yaml)
            
            # If parsing succeeds, write the fixed content back to the file
            new_content = f"---\n{fixed_yaml}---{file_content}"
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(new_content)
                
            logger.info(f"Fixed YAML in {file_path}")
            return True
        except Exception as e:
            logger.error(f"Could not fix YAML in {file_path}: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Error reading/writing file {file_path}: {str(e)}")
        return False

def replace_templates(yaml_str, file_path):
    """Replace template placeholders with actual values"""
    # Get file name without extension
    file_name = os.path.basename(file_path).replace('.md', '')
    
    # Get current date
    import datetime
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # Replace placeholders
    yaml_str = re.sub(r'PROJECT_TITLE|NOTE_TITLE|SOURCE_TITLE', file_name, yaml_str)
    yaml_str = re.sub(r'CURRENT_DATE', current_date, yaml_str)
    
    # Replace domain options with first domain
    if DOMAINS:
        first_domain = next(iter(DOMAINS.items()))
        domain_str = f"{first_domain[0]}-{first_domain[1]}"
        yaml_str = re.sub(r'DOMAIN_OPTIONS|DOMAIN_VALUE', domain_str, yaml_str)
    
    return yaml_str

def create_domain_folders():
    """Create domain folders if they don't exist"""
    for domain_num, domain_name in DOMAINS.items():
        domain_folder = f"{domain_num}-{domain_name}"
        domain_path = os.path.join(VAULT_PATH, domain_folder)
        
        if not os.path.exists(domain_path):
            os.makedirs(domain_path)
            logger.info(f"Created domain folder: {domain_path}")
            
            # Create hidden inbox
            inbox_path = os.path.join(domain_path, ".0-inbox")
            os.makedirs(inbox_path)
            logger.info(f"Created inbox folder: {inbox_path}")
            
            # Create domain dashboard
            dashboard_path = os.path.join(domain_path, f"{domain_name}.md")
            create_domain_dashboard(dashboard_path, domain_name, domain_folder)

def create_domain_dashboard(dashboard_path, domain_name, domain_folder):
    """Create a domain dashboard file"""
    import datetime
    current_date = datetime.datetime.now().strftime('%Y-%m-%d')
    
    content = f"""---
type: domain
created: {current_date}
---

# {domain_name} Dashboard

## Overview

Main dashboard for {domain_name} domain.

## Designated Projects

```dataview
TABLE satellites as "Sub-Projects", created
FROM "{domain_folder}"
WHERE type = "project" AND contains(file.folder, "{domain_folder}")
SORT file.name ASC
```

## Inbox Projects

```dataview
TABLE orbits as "Parent Projects", created
FROM "{domain_folder}/.0-inbox"
WHERE type = "project"
SORT file.name ASC
```

## Recent Notes

```dataview
TABLE type, orbits as "Projects", created
FROM "{domain_folder}"
WHERE type != "project" AND type != "domain"
SORT created DESC
LIMIT 10
```
"""
    
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    logger.info(f"Created domain dashboard: {dashboard_path}")

def main():
    parser = argparse.ArgumentParser(description='ORBIT System Debugging Tool')
    parser.add_argument('command', choices=['check-yaml', 'check-orbits', 'check-structure', 'fix-yaml', 'create-domains'],
                        help='Command to run')
    parser.add_argument('--file', help='Specific file to check/fix')
    parser.add_argument('--vault', default=VAULT_PATH, help='Path to the Obsidian vault')
    
    args = parser.parse_args()
    
    vault_path = args.vault
    
    if not validate_vault_path(vault_path):
        return
    
    if args.command == 'check-yaml':
        if args.file:
            file_path = args.file if os.path.isabs(args.file) else os.path.join(vault_path, args.file)
            check_yaml_frontmatter(file_path)
        else:
            logger.error("Please specify a file to check with --file")
    
    elif args.command == 'check-orbits':
        print(f"Checking orbit relationships in {vault_path}...")
        check_orbit_relationships(vault_path)
    
    elif args.command == 'check-structure':
        print(f"Checking directory structure in {vault_path}...")
        check_directory_structure(vault_path)
    
    elif args.command == 'fix-yaml':
        if args.file:
            file_path = args.file if os.path.isabs(args.file) else os.path.join(vault_path, args.file)
            fix_orbit_issue(file_path)
        else:
            logger.error("Please specify a file to fix with --file")
            
    elif args.command == 'create-domains':
        print(f"Creating domain folders in {vault_path}...")
        create_domain_folders()


if __name__ == "__main__":
    main()