#!/usr/bin/env python3
"""
Plugin Validation Script

This script validates that a plugin follows the AgentKit Plugin Specification.
Use this to ensure your plugin is compliant before deployment.
"""

import os
import sys
import importlib.util
import inspect
from typing import get_type_hints
from pathlib import Path


class PluginValidator:
    """Validates plugin compliance with AgentKit specification."""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed_checks = []
    
    def validate_plugin(self, plugin_path: Path) -> dict:
        """
        Validate a plugin against the specification.
        
        Args:
            plugin_path: Path to the plugin directory or file
            
        Returns:
            dict: Validation results with errors, warnings, and passed checks
        """
        self.errors = []
        self.warnings = []
        self.passed_checks = []
        
        # Load the plugin module
        module = self._load_plugin_module(plugin_path)
        if not module:
            return self._get_results()
        
        # Run validation checks
        self._validate_module_metadata(module)
        self._validate_exports(module)
        self._validate_public_api(module)
        self._validate_documentation(module)
        
        return self._get_results()
    
    def _load_plugin_module(self, plugin_path: Path):
        """Load a plugin module for validation."""
        if plugin_path.is_file() and plugin_path.suffix == '.py':
            # Single file plugin
            init_file = plugin_path
        else:
            # Directory plugin
            init_file = plugin_path / "__init__.py"
            if not init_file.exists():
                self.errors.append(f"Missing __init__.py file in {plugin_path}")
                return None
        
        # Add parent directory to sys.path for imports
        parent_dir = plugin_path.parent if plugin_path.is_file() else plugin_path.parent
        if str(parent_dir) not in sys.path:
            sys.path.insert(0, str(parent_dir))
        
        try:
            spec = importlib.util.spec_from_file_location(
                plugin_path.stem if plugin_path.is_file() else plugin_path.name,
                init_file
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module
        except Exception as e:
            self.errors.append(f"Failed to load plugin module: {str(e)}")
            return None
        
        return None
    
    def _validate_module_metadata(self, module):
        """Validate _module_info dictionary."""
        if not hasattr(module, '_module_info'):
            self.errors.append("Missing _module_info dictionary")
            return
        
        self.passed_checks.append("✓ _module_info dictionary exists")
        
        module_info = module._module_info
        required_fields = [
            'name', 'description', 'author', 'version', 
            'platform', 'python_requires', 'dependencies', 'environment_variables'
        ]
        
        for field in required_fields:
            if field not in module_info:
                self.errors.append(f"Missing required field in _module_info: {field}")
            else:
                self.passed_checks.append(f"✓ _module_info.{field} exists")
        
        # Validate version format
        if 'version' in module_info:
            version = module_info['version']
            if not isinstance(version, str) or not version.count('.') >= 1:
                self.warnings.append(f"Version '{version}' should follow semantic versioning (e.g., '1.0.0')")
            else:
                self.passed_checks.append("✓ Version format looks valid")
        
        # Validate platform
        if 'platform' in module_info:
            valid_platforms = ['any', 'linux', 'windows', 'macos']
            if module_info['platform'] not in valid_platforms:
                self.warnings.append(f"Platform '{module_info['platform']}' not in recommended values: {valid_platforms}")
            else:
                self.passed_checks.append("✓ Platform value is valid")
        
        # Validate dependencies
        if 'dependencies' in module_info:
            deps = module_info['dependencies']
            if not isinstance(deps, list):
                self.errors.append("dependencies must be a list")
            else:
                self.passed_checks.append("✓ Dependencies is a list")
                if 'pydantic>=2.0.0' not in deps and any('pydantic' in dep for dep in deps):
                    self.warnings.append("Consider using 'pydantic>=2.0.0' for compatibility")
        
        # Validate environment variables
        if 'environment_variables' in module_info:
            env_vars = module_info['environment_variables']
            if not isinstance(env_vars, dict):
                self.errors.append("environment_variables must be a dictionary")
            else:
                self.passed_checks.append("✓ Environment variables is a dictionary")
                for var_name, var_info in env_vars.items():
                    if not isinstance(var_info, dict):
                        self.errors.append(f"Environment variable '{var_name}' must be a dictionary")
                        continue
                    
                    required_var_fields = ['description', 'default', 'required']
                    for field in required_var_fields:
                        if field not in var_info:
                            self.errors.append(f"Missing field '{field}' in environment variable '{var_name}'")
                        else:
                            self.passed_checks.append(f"✓ Environment variable '{var_name}.{field}' exists")
    
    def _validate_exports(self, module):
        """Validate _module_exports dictionary."""
        if not hasattr(module, '_module_exports'):
            self.errors.append("Missing _module_exports dictionary")
            return
        
        self.passed_checks.append("✓ _module_exports dictionary exists")
        
        exports = module._module_exports
        if not isinstance(exports, dict):
            self.errors.append("_module_exports must be a dictionary")
            return
        
        # Check that at least one category has content
        has_content = any(
            isinstance(category_items, list) and len(category_items) > 0 
            for category_items in exports.values()
        )
        
        if not has_content:
            self.warnings.append("_module_exports has no content in any category")
        else:
            self.passed_checks.append("✓ _module_exports has content")
        
        # Validate common categories
        common_categories = ['tools', 'agents', 'resources', 'middleware', 'models', 'utilities']
        
        for category, items in exports.items():
            if not isinstance(items, list):
                self.errors.append(f"_module_exports['{category}'] must be a list")
                continue
            
            if len(items) > 0:
                self.passed_checks.append(f"✓ Found {len(items)} items in '{category}' category")
                
                # For tools category, validate that items are callable
                if category == 'tools':
                    for i, item in enumerate(items):
                        if not callable(item):
                            self.errors.append(f"Tool {i} in '{category}' is not callable")
                        else:
                            self.passed_checks.append(f"✓ Tool '{item.__name__}' is callable")
                
                # For other categories, just check they exist
                else:
                    for i, item in enumerate(items):
                        if hasattr(item, '__name__'):
                            self.passed_checks.append(f"✓ Item '{item.__name__}' in '{category}' category")
                        else:
                            self.passed_checks.append(f"✓ Item {i} in '{category}' category exists")
            
            # Warn about unknown categories (but don't error)
            if category not in common_categories:
                self.warnings.append(f"Custom category '{category}' found (this is allowed but uncommon)")
    
    def _validate_public_api(self, module):
        """Validate public API functions."""
        if not hasattr(module, '_module_exports'):
            return
        
        exports = module._module_exports
        tools = exports.get('tools', [])
        
        for tool in tools:
            if not callable(tool):
                continue
            
            self._validate_function_signature(tool)
            self._validate_function_docstring(tool)
    
    def _validate_function_signature(self, func):
        """Validate function signature and type annotations."""
        func_name = func.__name__
        
        # Check if function has type annotations
        try:
            sig = inspect.signature(func)
            hints = get_type_hints(func)
        except Exception as e:
            self.errors.append(f"Failed to get signature for {func_name}: {str(e)}")
            return
        
        # Check return type annotation
        if 'return' not in hints:
            self.warnings.append(f"Function '{func_name}' missing return type annotation")
        else:
            self.passed_checks.append(f"✓ Function '{func_name}' has return type annotation")
        
        # Check parameter annotations
        for param_name, param in sig.parameters.items():
            if param.annotation == inspect.Parameter.empty:
                self.warnings.append(f"Parameter '{param_name}' in '{func_name}' missing type annotation")
            else:
                # Check if it's using Annotated with Field (basic check)
                annotation_str = str(param.annotation)
                if 'Annotated' in annotation_str and 'Field' in annotation_str:
                    self.passed_checks.append(f"✓ Parameter '{param_name}' in '{func_name}' uses Annotated[Type, Field(...)]")
                else:
                    self.warnings.append(f"Parameter '{param_name}' in '{func_name}' should use Annotated[Type, Field(...)]")
    
    def _validate_function_docstring(self, func):
        """Validate function docstring."""
        func_name = func.__name__
        docstring = inspect.getdoc(func)
        
        if not docstring:
            self.errors.append(f"Function '{func_name}' missing docstring")
            return
        
        self.passed_checks.append(f"✓ Function '{func_name}' has docstring")
        
        # Check for required docstring sections
        required_sections = ['Args:', 'Returns:']
        for section in required_sections:
            if section not in docstring:
                self.warnings.append(f"Function '{func_name}' docstring missing '{section}' section")
            else:
                self.passed_checks.append(f"✓ Function '{func_name}' docstring has '{section}' section")
    
    def _validate_documentation(self, module):
        """Validate documentation requirements."""
        # Check for README.md file in the plugin directory
        module_file = getattr(module, '__file__', None)
        if module_file:
            # Get the directory containing the module
            module_dir = Path(module_file).parent
            readme_path = module_dir / 'README.md'
            
            if readme_path.exists():
                self.passed_checks.append("✓ Module has documentation (README.md)")
            else:
                self.warnings.append("Module missing documentation (no README.md found)")
        else:
            self.warnings.append("Module missing documentation (could not determine module path)")
    
    def _get_results(self):
        """Get validation results."""
        return {
            'errors': self.errors,
            'warnings': self.warnings,
            'passed_checks': self.passed_checks,
            'is_valid': len(self.errors) == 0
        }


def print_validation_results(results: dict, plugin_name: str):
    """Print validation results in a readable format."""
    print(f"\n{'='*60}")
    print(f"VALIDATION RESULTS FOR: {plugin_name}")
    print(f"{'='*60}")
    
    if results['is_valid']:
        print("🎉 PLUGIN IS VALID!")
    else:
        print("❌ PLUGIN HAS ERRORS")
    
    print(f"\nSummary:")
    print(f"  ✅ Passed checks: {len(results['passed_checks'])}")
    print(f"  ⚠️  Warnings: {len(results['warnings'])}")
    print(f"  ❌ Errors: {len(results['errors'])}")
    
    if results['passed_checks']:
        print(f"\n✅ PASSED CHECKS:")
        for check in results['passed_checks']:
            print(f"  {check}")
    
    if results['warnings']:
        print(f"\n⚠️  WARNINGS:")
        for warning in results['warnings']:
            print(f"  ⚠️  {warning}")
    
    if results['errors']:
        print(f"\n❌ ERRORS:")
        for error in results['errors']:
            print(f"  ❌ {error}")
    
    print(f"\n{'='*60}")


def main():
    """Main validation script."""
    if len(sys.argv) != 2:
        print("Usage: python validate_plugin.py <plugin_path>")
        print("Example: python validate_plugin.py ./my_plugin")
        print("Example: python validate_plugin.py ./simple_plugin.py")
        sys.exit(1)
    
    plugin_path = Path(sys.argv[1])
    
    if not plugin_path.exists():
        print(f"Error: Plugin path '{plugin_path}' does not exist")
        sys.exit(1)
    
    validator = PluginValidator()
    results = validator.validate_plugin(plugin_path)
    
    print_validation_results(results, plugin_path.name)
    
    # Exit with error code if validation failed
    if not results['is_valid']:
        sys.exit(1)


if __name__ == "__main__":
    main() 
