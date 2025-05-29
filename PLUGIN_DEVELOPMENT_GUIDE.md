# ld-agent Plugin Specification v1.0

This document defines the standard architecture and interface requirements for ld-agent plugins. Follow this specification to ensure your plugin is compatible with the ld-agent ecosystem and can be automatically documented, loaded, and managed.

Note: There is a 'validate_plugin.py' module in the 'plugins' folder that will validate your plugins to ensure it matches the specification, and will give warnings and errors if it does not.

Example:

```
============================================================
VALIDATION RESULTS FOR: discord_notifier
============================================================
❌ PLUGIN HAS ERRORS

Summary:
  ✅ Passed checks: 26
  ⚠️  Warnings: 5
  ❌ Errors: 1

✅ PASSED CHECKS:
  ✓ _module_info dictionary exists
  ✓ _module_info.name exists
  ✓ _module_info.description exists
  ✓ _module_info.author exists
  ✓ _module_info.version exists
  ✓ _module_info.platform exists
  ✓ _module_info.python_requires exists
  ✓ _module_info.dependencies exists
  ✓ _module_info.environment_variables exists
  ✓ Version format looks valid
  ✓ Platform value is valid
  ✓ Dependencies is a list
  ✓ Environment variables is a dictionary
  ✓ Environment variable 'DISCORD_NOTIFIER_WEBHOOK_URL.description' exists
  ✓ Environment variable 'DISCORD_NOTIFIER_WEBHOOK_URL.default' exists
  ✓ Environment variable 'DISCORD_NOTIFIER_WEBHOOK_URL.required' exists
  ✓ Environment variable 'DISCORD_NOTIFIER_ENABLED.description' exists
  ✓ Environment variable 'DISCORD_NOTIFIER_ENABLED.default' exists
  ✓ Environment variable 'DISCORD_NOTIFIER_ENABLED.required' exists
  ✓ Environment variable 'DISCORD_NOTIFIER_BOT_NAME.description' exists
  ✓ Environment variable 'DISCORD_NOTIFIER_BOT_NAME.default' exists
  ✓ Environment variable 'DISCORD_NOTIFIER_BOT_NAME.required' exists
  ✓ _module_exports dictionary exists
  ✓ _module_exports has content
  ✓ Found 1 items in 'tools' category
  ✓ Tool 'send_discord_notification' is callable

⚠️  WARNINGS:
  ⚠️  Function 'send_discord_notification' missing return type annotation
  ⚠️  Parameter 'message' in 'send_discord_notification' missing type annotation
  ⚠️  Parameter 'title' in 'send_discord_notification' missing type annotation
  ⚠️  Parameter 'bot_name' in 'send_discord_notification' missing type annotation
  ⚠️  Module missing documentation

❌ ERRORS:
  ❌ Function 'send_discord_notification' missing docstring
```

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [File Structure Requirements](#file-structure-requirements)
3. [Module Metadata Specification](#module-metadata-specification)
4. [Public API Definition Standards](#public-api-definition-standards)
5. [Implementation Module Guidelines](#implementation-module-guidelines)
6. [Export Specification](#export-specification)
7. [Type Annotation Requirements](#type-annotation-requirements)
8. [Documentation Standards](#documentation-standards)
9. [Error Handling Guidelines](#error-handling-guidelines)
10. [Testing Requirements](#testing-requirements)
11. [Examples](#examples)
12. [Validation Checklist](#validation-checklist)

## 🏗️ Architecture Overview

ld-agent plugins follow a **centralized API definition** pattern with clear separation of concerns:

- **`__init__.py`**: Contains all public API definitions with Pydantic type annotations
- **Implementation modules**: Contain business logic without Pydantic decorations
- **Clean interface**: Public API is completely separated from implementation details

### Core Principles

1. **Single Source of Truth**: All exported functions defined in `__init__.py`
2. **Type Safety**: Full Pydantic type annotations for all public functions
3. **Documentation First**: Comprehensive docstrings and metadata
4. **Implementation Isolation**: Business logic separated from interface definitions
5. **Auto-Discovery**: Standardized metadata for automatic plugin loading

## 📁 File Structure Requirements

### Minimum Required Structure

```
your_plugin/
├── __init__.py              # REQUIRED: Public API definitions
├── implementation.py        # REQUIRED: Business logic (can be multiple files)
└── README.md               # RECOMMENDED: Plugin documentation
```

### Complex Plugin Structure

```
your_plugin/
├── __init__.py              # Public API definitions
├── core/                    # Implementation modules
│   ├── __init__.py
│   ├── main_logic.py
│   ├── helpers.py
│   └── utils.py
├── tests/                   # Test modules
│   ├── __init__.py
│   ├── test_main.py
│   └── test_integration.py
├── README.md               # Plugin documentation
└── requirements.txt        # Optional: Plugin-specific dependencies
```

### Single-File Plugin Structure

```
simple_plugin.py            # All-in-one plugin file
```

## 🏷️ Module Metadata Specification

Every plugin MUST define `_module_info` in its `__init__.py` (or main file for single-file plugins):

```python
_module_info = {
    "name": str,                    # REQUIRED: Human-readable plugin name
    "description": str,             # REQUIRED: Brief description of functionality
    "author": str,                  # REQUIRED: Plugin author/maintainer
    "version": str,                 # REQUIRED: Semantic version (e.g., "1.0.0")
    "platform": str,                # REQUIRED: "any", "linux", "windows", "macos"
    "python_requires": str,         # REQUIRED: Minimum Python version (e.g., ">=3.10")
    "dependencies": List[str],      # REQUIRED: List of required packages
    "environment_variables": Dict[str, Dict[str, Any]]  # REQUIRED: Env var definitions
}
```

### Environment Variables Schema

```python
"environment_variables": {
    "VAR_NAME": {
        "description": str,         # REQUIRED: What this variable is for
        "default": str,             # REQUIRED: Default value (use "" for no default)
        "required": bool            # REQUIRED: Whether this variable is mandatory
    }
}
```

### Example Module Metadata

```python
_module_info = {
    "name": "Document Processor",
    "description": "Process and analyze documents with AI",
    "author": "Jane Developer",
    "version": "2.1.0",
    "platform": "any",
    "python_requires": ">=3.10",
    "dependencies": ["pydantic>=2.0.0", "requests", "openai>=1.0.0"],
    "environment_variables": {
        "OPENAI_API_KEY": {
            "description": "OpenAI API key for document analysis",
            "default": "",
            "required": True
        },
        "MAX_DOCUMENT_SIZE": {
            "description": "Maximum document size in MB",
            "default": "10",
            "required": False
        }
    }
}
```

## 🔧 Public API Definition Standards

All public functions MUST be defined in `__init__.py` with complete Pydantic type annotations.

### Function Definition Template

```python
from typing import Annotated, Optional, Dict, Any, List
from pydantic import Field

def your_function_name(
    param1: Annotated[Type, Field(description="Parameter description")],
    param2: Annotated[Optional[Type], Field(description="Optional parameter", default=None)]
) -> ReturnType:
    """
    Brief function description.
    
    Detailed explanation of what the function does, its purpose,
    and any important behavior or side effects.
    
    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2
    
    Returns:
        ReturnType: Description of what is returned
        
    Raises:
        SpecificException: When this exception might be raised
    """
    return _your_function_name_impl(param1, param2)
```

### Required Type Annotations

1. **All parameters** MUST use `Annotated[Type, Field(...)]`
2. **Field descriptions** MUST be provided for all parameters
3. **Return types** MUST be explicitly specified
4. **Optional parameters** MUST use `Optional[Type]` or `Type | None`
5. **Default values** MUST be specified in Field() for optional parameters

### Supported Parameter Types

```python
# Basic types
str, int, float, bool

# Collections
List[Type], Dict[str, Type], Tuple[Type, ...]

# Optional types
Optional[Type], Union[Type1, Type2]

# Complex types
Dict[str, Any], List[Dict[str, Any]]

# Custom types (with proper imports)
from datetime import datetime
from pathlib import Path
```

## 🛠️ Implementation Module Guidelines

Implementation modules contain the actual business logic and SHOULD follow these guidelines:

### Naming Convention

- Public API function: `your_function_name`
- Implementation function: `_your_function_name_impl` (or imported 'as' this naming convention)

### Implementation Function Template

```python
def _your_function_name_impl(param1: Type, param2: Optional[Type] = None) -> ReturnType:
    """
    Implementation function for your_function_name.
    Brief description of what this implementation does.
    
    Args:
        param1: Description of parameter
        param2: Description of parameter
    
    Returns:
        ReturnType: Description of return value
    """
    # Implementation logic here
    try:
        # Your business logic
        result = process_data(param1, param2)
        return result
    except Exception as e:
        # Proper error handling
        logger.error(f"Error in {__name__}: {str(e)}")
        return None  # or raise appropriate exception
```

### Implementation Guidelines

1. **Clean type hints** using appropriate typing (standard Python typing, Pydantic models, etc.)
3. **Proper error handling** with logging
4. **Single responsibility** per function when practical
5. **Clear documentation** for complex logic
6. **Consistent naming** with the `_function_name_impl` pattern for functions called from public API. You can absolutely import a function as this descriptor to preserve your original component naming, e.g.: ```from .somemodule import do_stuff as _do_stuff_impl```

### Flexibility in Implementation

Implementation modules are **your domain**. You can:

- Use Pydantic models for internal data validation
- Import and use any libraries you need
- Define custom classes, enums, or data structures
- Use dataclasses, NamedTuples, or other data containers
- Implement complex business logic with multiple helper functions
- Use async/await patterns if needed
- Organize code into submodules as appropriate

The only requirement is that your implementation functions should be callable from the public API functions defined in `__init__.py`.

## 📤 Export Specification

Every plugin MUST define `_module_exports` in its `__init__.py`:

```python
_module_exports = {
    "tools": [function1, function2, function3],      # List of callable functions
    "agents": [AgentClass1, AgentClass2],            # List of agent classes
    "resources": [ResourceProvider1],                # List of resource providers
    "middleware": [middleware_func1],                # List of middleware functions
    "models": [DataModel1, DataModel2],              # List of data models/schemas
    "utilities": [utility_func1, utility_func2]     # List of utility functions
}
```

### Export Categories

- **tools**: Functions that can be called directly by agents (most common)
- **agents**: Agent classes that can be instantiated and used
- **resources**: Resource providers (databases, APIs, file systems, etc.)
- **middleware**: Functions that process requests/responses in a pipeline
- **models**: Pydantic models, dataclasses, or other data structures
- **utilities**: Helper functions that other plugins might use

### Flexible Export Rules

1. **At least one category** should have content (usually `tools`)
2. **Empty categories** can be omitted entirely
3. **Custom categories** are allowed for specialized use cases
4. **Mixed exports** are encouraged - export whatever makes sense for your plugin

### Example Exports

```python
# Simple plugin with just tools
_module_exports = {
    "tools": [process_document, analyze_text]
}

# Complex plugin with multiple export types
_module_exports = {
    "tools": [search_documents, index_document],
    "agents": [DocumentSearchAgent, DocumentAnalysisAgent],
    "models": [DocumentModel, SearchResultModel],
    "utilities": [validate_document_format, extract_metadata]
}

# Specialized plugin with custom categories
_module_exports = {
    "tools": [train_model, predict],
    "models": [MLModel, TrainingConfig],
    "pipelines": [DataPreprocessingPipeline, ModelTrainingPipeline]
}
```

## 🏷️ Type Annotation Requirements

### Pydantic Field Specifications

All public API parameters MUST use Pydantic Field with descriptive information:

```python
# Required parameter
param: Annotated[str, Field(description="Clear description of what this parameter does")]

# Optional parameter with default
param: Annotated[Optional[str], Field(description="Description", default="default_value")]

# Parameter with validation
param: Annotated[int, Field(description="Description", ge=1, le=100)]

# Complex parameter
param: Annotated[List[Dict[str, Any]], Field(description="List of objects with specific structure")]
```

### Common Type Patterns

```python
# String parameters
document_id: Annotated[str, Field(description="Unique document identifier")]

# Optional strings
title: Annotated[Optional[str], Field(description="Optional document title", default=None)]

# Lists
items: Annotated[List[str], Field(description="List of item names")]

# Dictionaries
metadata: Annotated[Dict[str, Any], Field(description="Document metadata")]

# Complex structures
documents: Annotated[List[Dict[str, Any]], Field(description="List of document objects")]

# File paths
file_path: Annotated[str, Field(description="Path to input file")]

# Numeric parameters
max_results: Annotated[int, Field(description="Maximum number of results", ge=1, le=1000, default=10)]
```

## 📚 Documentation Standards

### Docstring Requirements

Every public function MUST have a comprehensive docstring:

```python
def function_name(param1: Type, param2: Type) -> ReturnType:
    """
    One-line summary of what the function does.
    
    Detailed description explaining:
    - What the function accomplishes
    - Any important behavior or side effects
    - When you would use this function
    - Any limitations or constraints
    
    Args:
        param1: Detailed description of parameter 1, including expected format
        param2: Detailed description of parameter 2, including valid values
    
    Returns:
        ReturnType: Detailed description of return value, including structure
        
    Raises:
        ValueError: When invalid parameters are provided
        ConnectionError: When external service is unavailable
        
    Example:
        >>> result = function_name("example", 42)
        >>> print(result)
        {'status': 'success', 'data': [...]}
    """
```

### README Requirements

Every plugin SHOULD include a README.md with:

1. **Plugin overview** and purpose
2. **Installation instructions**
3. **Configuration requirements**
4. **Usage examples**
5. **API reference**
6. **Error handling information**
7. **Contributing guidelines**

## ⚠️ Error Handling Guidelines

### Standard Error Handling Pattern

```python
import logging

logger = logging.getLogger(__name__)

def _implementation_function(param: str) -> Optional[Dict[str, Any]]:
    """Implementation with proper error handling."""
    try:
        # Validate inputs
        if not param or not isinstance(param, str):
            logger.error(f"Invalid parameter: {param}")
            return None
        
        # Main logic
        result = perform_operation(param)
        
        # Validate outputs
        if not result:
            logger.warning(f"No result for parameter: {param}")
            return None
            
        return result
        
    except ConnectionError as e:
        logger.error(f"Connection failed: {str(e)}")
        return None
    except ValueError as e:
        logger.error(f"Invalid value: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in {__name__}: {str(e)}")
        return None
```

### Error Handling Rules

1. **Always use logging** instead of print statements
2. **Return None or appropriate default** for recoverable errors
3. **Raise specific exceptions** only for programming errors
4. **Validate inputs** at the start of functions
5. **Provide meaningful error messages** with context

## 🧪 Testing Requirements

### Test Structure

```python
# tests/test_your_plugin.py
import pytest
from your_plugin import function_name

def test_function_name_success():
    """Test successful function execution."""
    result = function_name("valid_input")
    assert result is not None
    assert isinstance(result, dict)
    assert "expected_key" in result

def test_function_name_invalid_input():
    """Test function with invalid input."""
    result = function_name("")
    assert result is None

def test_function_name_missing_env():
    """Test function with missing environment variables."""
    # Mock missing environment variables
    result = function_name("input")
    assert result is None
```

### Testing Guidelines

1. **Test happy path** scenarios
2. **Test error conditions** and edge cases
3. **Test environment variable** handling
4. **Mock external dependencies** appropriately
5. **Use descriptive test names** and docstrings

## 📝 Examples

### Complete Simple Plugin Example

```python
# simple_calculator.py

# =============================================================================
# START OF MODULE METADATA
# =============================================================================
_module_info = {
    "name": "Simple Calculator",
    "description": "Basic arithmetic operations",
    "author": "Example Developer",
    "version": "1.0.0",
    "platform": "any",
    "python_requires": ">=3.10",
    "dependencies": ["pydantic>=2.0.0"],
    "environment_variables": {}
}
# =============================================================================
# END OF MODULE METADATA
# =============================================================================

from typing import Annotated
from pydantic import Field

def add_numbers(
    a: Annotated[float, Field(description="First number to add")],
    b: Annotated[float, Field(description="Second number to add")]
) -> float:
    """
    Add two numbers together and return the result.
    
    Args:
        a: First number to add
        b: Second number to add
    
    Returns:
        float: The sum of a and b
    """
    return _add_numbers_impl(a, b)

def _add_numbers_impl(a: float, b: float) -> float:
    """Implementation function for add_numbers."""
    return a + b

# =============================================================================
# START OF EXPORTS
# =============================================================================
_module_exports = {
    "tools": [add_numbers]
}
# =============================================================================
# END OF EXPORTS
# =============================================================================
```

### Complete Complex Plugin Example

```python
# complex_plugin/__init__.py

# =============================================================================
# START OF MODULE METADATA
# =============================================================================
_module_info = {
    "name": "Document Analyzer",
    "description": "Analyze documents using AI and extract insights",
    "author": "AI Team",
    "version": "2.0.0",
    "platform": "any",
    "python_requires": ">=3.10",
    "dependencies": ["pydantic>=2.0.0", "requests", "openai>=1.0.0"],
    "environment_variables": {
        "OPENAI_API_KEY": {
            "description": "OpenAI API key for document analysis",
            "default": "",
            "required": True
        },
        "MAX_DOCUMENT_SIZE": {
            "description": "Maximum document size in MB",
            "default": "10",
            "required": False
        }
    }
}
# =============================================================================
# END OF MODULE METADATA
# =============================================================================

from typing import Annotated, Optional, Dict, Any, List
from pydantic import Field

# Import implementation functions
from .analyzer import _analyze_document_impl, _extract_keywords_impl
from .processor import _process_batch_impl

# =============================================================================
# START OF PUBLIC API DEFINITIONS
# =============================================================================

def analyze_document(
    document_text: Annotated[str, Field(description="Text content of the document to analyze")],
    analysis_type: Annotated[str, Field(description="Type of analysis: 'summary', 'sentiment', 'keywords'", default="summary")]
) -> Optional[Dict[str, Any]]:
    """
    Analyze a document using AI and return insights.
    
    This function processes document text and returns various types of analysis
    including summaries, sentiment analysis, and keyword extraction.
    
    Args:
        document_text: The text content to analyze
        analysis_type: The type of analysis to perform
    
    Returns:
        Optional[Dict[str, Any]]: Analysis results or None if analysis failed
        
    Example:
        >>> result = analyze_document("This is a sample document.", "summary")
        >>> print(result['summary'])
        "Brief summary of the document content"
    """
    return _analyze_document_impl(document_text, analysis_type)

def extract_keywords(
    text: Annotated[str, Field(description="Text to extract keywords from")],
    max_keywords: Annotated[int, Field(description="Maximum number of keywords to extract", ge=1, le=50, default=10)]
) -> List[str]:
    """
    Extract important keywords from text.
    
    Args:
        text: Input text for keyword extraction
        max_keywords: Maximum number of keywords to return
    
    Returns:
        List[str]: List of extracted keywords
    """
    return _extract_keywords_impl(text, max_keywords)

def process_batch(
    documents: Annotated[List[Dict[str, Any]], Field(description="List of documents to process")]
) -> Dict[str, Any]:
    """
    Process multiple documents in batch.
    
    Args:
        documents: List of document objects with 'id' and 'text' fields
    
    Returns:
        Dict[str, Any]: Batch processing results
    """
    return _process_batch_impl(documents)

# =============================================================================
# END OF PUBLIC API DEFINITIONS
# =============================================================================

# =============================================================================
# START OF EXPORTS
# =============================================================================
_module_exports = {
    "tools": [analyze_document, extract_keywords, process_batch]
}
# =============================================================================
# END OF EXPORTS
# =============================================================================
```

## ✅ Validation Checklist

Use this checklist to ensure your plugin is compliant:

### Module Metadata ✓
- [ ] `_module_info` dictionary is defined
- [ ] All required fields are present (name, description, author, version, platform, python_requires, dependencies, environment_variables)
- [ ] Version follows semantic versioning (e.g., "1.0.0")
- [ ] Dependencies list includes all required packages
- [ ] Environment variables are properly documented

### Public API ✓
- [ ] All public functions are defined in `__init__.py`
- [ ] All parameters use `Annotated[Type, Field(...)]`
- [ ] All Field descriptions are meaningful and complete
- [ ] Return types are explicitly specified
- [ ] Optional parameters use `Optional[Type]` or `Type | None`
- [ ] Functions delegate to implementation functions

### Implementation ✓
- [ ] Implementation functions use `_function_name_impl` naming for functions called from public API
- [ ] Proper error handling with logging
- [ ] Input validation at function start when appropriate
- [ ] Meaningful error messages with context
- [ ] Implementation modules are well-organized and documented

### Documentation ✓
- [ ] All public functions have comprehensive docstrings
- [ ] Docstrings include Args, Returns, and Raises sections
- [ ] README.md exists with usage examples
- [ ] Code is well-commented for complex logic

### Exports ✓
- [ ] `_module_exports` dictionary is defined
- [ ] At least one export category has content
- [ ] All exported items are properly defined and accessible
- [ ] Export categories are used appropriately for the content type

### Error Handling ✓
- [ ] Functions return None or appropriate defaults for errors
- [ ] Logging is used instead of print statements
- [ ] Specific exceptions are caught and handled
- [ ] Environment variable validation is implemented

### Testing ✓
- [ ] Test files exist for all public functions
- [ ] Happy path scenarios are tested
- [ ] Error conditions are tested
- [ ] Environment variable handling is tested

## 🚀 Quick Start Template

Use this template to create a new plugin:

```python
# your_plugin_name/__init__.py

# =============================================================================
# START OF MODULE METADATA
# =============================================================================
_module_info = {
    "name": "Your Plugin Name",
    "description": "Brief description of what your plugin does",
    "author": "Your Name",
    "version": "1.0.0",
    "platform": "any",
    "python_requires": ">=3.10",
    "dependencies": ["pydantic>=2.0.0"],
    "environment_variables": {
        # Add your environment variables here
    }
}
# =============================================================================
# END OF MODULE METADATA
# =============================================================================

from typing import Annotated, Optional, Dict, Any
from pydantic import Field

# Import your implementation functions
from .implementation import _your_function_impl

# =============================================================================
# START OF PUBLIC API DEFINITIONS
# =============================================================================

def your_function(
    param: Annotated[str, Field(description="Description of your parameter")]
) -> Optional[Dict[str, Any]]:
    """
    Brief description of what your function does.
    
    Args:
        param: Description of the parameter
    
    Returns:
        Optional[Dict[str, Any]]: Description of return value
    """
    return _your_function_impl(param)

# =============================================================================
# END OF PUBLIC API DEFINITIONS
# =============================================================================

# =============================================================================
# START OF EXPORTS
# =============================================================================
_module_exports = {
    "tools": [your_function]
}
# =============================================================================
# END OF EXPORTS
# =============================================================================
```

---

**This specification ensures consistency, maintainability, and automatic compatibility with ld-agent's plugin ecosystem. Follow these guidelines to create professional, well-documented, and easily maintainable plugins.** 
