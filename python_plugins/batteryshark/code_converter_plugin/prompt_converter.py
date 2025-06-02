"""
Prompt Converter Implementation

This module contains the implementation logic for converting prompt files
back to directory structures and files.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)


class PromptToDirectory:
    """Converts prompt file format back to directory structure."""
    
    def __init__(self):
        """Initialize the converter."""
        pass
    
    def parse_prompt_file(self, prompt_content: str) -> Tuple[str, List[Dict[str, str]]]:
        """
        Parse the prompt file content to extract project info and files.
        
        Args:
            prompt_content: Content of the prompt file
            
        Returns:
            Tuple of (project_name, files_data)
            files_data is a list of dicts with 'path', 'language', and 'content' keys
        """
        lines = prompt_content.split('\n')
        
        # Extract project name
        project_name = "project"  # Default
        for i, line in enumerate(lines):
            if line.startswith("Project Path:"):
                project_name = line.split("Project Path:")[1].strip()
                # Remove any additional info like "(Selected Files)"
                if "(" in project_name:
                    project_name = project_name.split("(")[0].strip()
                break
        
        # Find all file blocks
        files_data = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for file path pattern: `path/to/file`:
            if line.startswith('`') and line.endswith('`:'):
                file_path = line[1:-2]  # Remove backticks and colon
                
                # Skip the empty line after file path
                i += 1
                if i < len(lines) and lines[i].strip() == "":
                    i += 1
                
                # Look for code block start
                if i < len(lines):
                    code_block_start = lines[i].strip()
                    if code_block_start.startswith('```'):
                        language = code_block_start[3:].strip()
                        i += 1
                        
                        # Collect content until closing ```
                        content_lines = []
                        while i < len(lines):
                            if lines[i].strip() == '```':
                                # Found closing code block
                                files_data.append({
                                    'path': file_path,
                                    'language': language,
                                    'content': '\n'.join(content_lines)
                                })
                                break
                            else:
                                content_lines.append(lines[i])
                            i += 1
            
            i += 1
        
        return project_name, files_data
    
    def create_directory_structure(self, 
                                 files_data: List[Dict[str, str]], 
                                 output_dir: Path,
                                 project_name: str) -> Dict[str, Any]:
        """
        Create the directory structure and files.
        
        Args:
            files_data: List of file data dictionaries
            output_dir: Base output directory
            project_name: Name of the project
            
        Returns:
            Dictionary with creation results
        """
        # Check if file paths already include the project name
        # If most files start with the project name, don't create an extra project directory
        paths_with_project = sum(1 for f in files_data if f['path'].startswith(f"{project_name}/"))
        use_project_dir = paths_with_project < len(files_data) * 0.5  # Less than half start with project name
        
        if use_project_dir:
            # Create the project directory
            base_dir = output_dir / project_name
            base_dir.mkdir(parents=True, exist_ok=True)
        else:
            # Use output directory directly since paths already include project structure
            base_dir = output_dir
            base_dir.mkdir(parents=True, exist_ok=True)
        
        created_files = []
        created_dirs = set()
        
        for file_info in files_data:
            file_path = Path(file_info['path'])
            
            # If we're not using a project dir but the path starts with project name, strip it
            if not use_project_dir and str(file_path).startswith(f"{project_name}/"):
                # Remove the project name from the beginning of the path
                path_parts = file_path.parts[1:]  # Skip the first part (project name)
                if path_parts:
                    file_path = Path(*path_parts)
                else:
                    # If only the project name, skip this file
                    continue
            
            full_path = base_dir / file_path
            
            # Create parent directories if they don't exist
            parent_dir = full_path.parent
            if parent_dir != base_dir:
                parent_dir.mkdir(parents=True, exist_ok=True)
                created_dirs.add(str(parent_dir.relative_to(output_dir)))
            
            # Write the file content
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(file_info['content'])
                created_files.append(str(file_path))
            except Exception as e:
                logger.warning(f"Could not create file {file_path}: {e}")
        
        # Return results
        result = {
            'project_name': project_name,
            'output_directory': str(base_dir),
            'files_created': len(created_files),
            'directories_created': len(created_dirs),
            'created_files': created_files,
            'created_directories': list(created_dirs),
            'used_project_dir': use_project_dir
        }
        
        return result
    
    def validate_prompt_format(self, prompt_content: str) -> bool:
        """
        Validate that the prompt content is in the expected format.
        
        Args:
            prompt_content: Content to validate
            
        Returns:
            True if format appears valid, False otherwise
        """
        lines = prompt_content.split('\n')
        
        # Check for basic structure markers
        has_project_path = any(line.startswith("Project Path:") for line in lines[:10])
        has_source_tree = any("Source Tree:" in line for line in lines[:20])
        has_file_blocks = any(line.startswith('`') and line.endswith('`:') for line in lines)
        has_code_blocks = any(line.strip().startswith('```') for line in lines)
        
        return has_project_path or (has_source_tree and has_file_blocks and has_code_blocks)


def _convert_prompt_to_directory_impl(prompt_file_path: str, output_dir_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Implementation function for convert_prompt_to_directory.
    
    Args:
        prompt_file_path: Path to the prompt file to convert
        output_dir_path: Path where to create the directory structure
        
    Returns:
        Dictionary with conversion results
    """
    try:
        prompt_path = Path(prompt_file_path)
        
        if not prompt_path.exists():
            logger.error(f"Prompt file not found: {prompt_file_path}")
            return {
                'success': False,
                'error': f"Prompt file not found: {prompt_file_path}",
                'files_created': 0
            }
        
        # Read prompt file
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt_content = f.read()
        except Exception as e:
            logger.error(f"Could not read prompt file: {e}")
            return {
                'success': False,
                'error': f"Could not read prompt file: {e}",
                'files_created': 0
            }
        
        # Initialize converter
        converter = PromptToDirectory()
        
        # Validate format
        if not converter.validate_prompt_format(prompt_content):
            logger.warning("Prompt file doesn't appear to be in expected format, attempting to parse anyway")
        
        # Parse the prompt
        project_name, files_data = converter.parse_prompt_file(prompt_content)
        
        if not files_data:
            logger.error("No files found in prompt file")
            return {
                'success': False,
                'error': "No files found in prompt file",
                'files_created': 0
            }
        
        # Determine output directory
        if output_dir_path:
            output_dir = Path(output_dir_path)
        else:
            # Use the same directory as the prompt file
            output_dir = prompt_path.parent / f"{project_name}_reconstructed"
        
        # Create directory structure
        result = converter.create_directory_structure(files_data, output_dir, project_name)
        
        # Add success flag and summary
        result['success'] = True
        result['prompt_file'] = str(prompt_path)
        result['total_files_in_prompt'] = len(files_data)
        
        logger.info(f"Successfully reconstructed {result['files_created']} files to {result['output_directory']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error converting prompt to directory: {str(e)}")
        return {
            'success': False,
            'error': f"Error converting prompt to directory: {str(e)}",
            'files_created': 0
        } 