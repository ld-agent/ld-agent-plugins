# Plugin README Validation Checklist

Use this checklist to ensure your plugin README follows best practices for concise, informative documentation. This example has been generated with Python in mind, but the principles apply equally to Go and Typescript plugins as well.

## ✅ Required Sections

### 1. **Plugin Title & Brief Description**
- [ ] Clear plugin name as H1 header
- [ ] One-line description that explains what the plugin does
- [ ] No marketing fluff or excessive adjectives

**Example:**
```markdown
# Discord Notifier Plugin

Send notifications to Discord channels via webhooks.
```

### 2. **What it does**
- [ ] Bullet points explaining core functionality
- [ ] Focus on user benefits, not implementation details
- [ ] Include return value behavior (True/False, data types, etc.)

**Example:**
```markdown
## What it does

- Sends messages to Discord channels using webhook URLs
- Supports custom titles and bot names
- Returns `True`/`False` for success/failure
```

### 3. **Requirements**
- [ ] Python version requirement
- [ ] List of dependencies with versions
- [ ] Platform support (if applicable)

**Example:**
```markdown
## Requirements

- Python 3.10+
- `pydantic>=2.0.0`
- `requests`
- Platform: any (or specify: Linux, Windows, macOS)
```

### 4. **Environment Variables**
- [ ] Table format with columns: Variable, Required, Default, Description
- [ ] Clear indication of required vs optional variables
- [ ] Descriptive but concise descriptions

**Example:**
```markdown
## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PLUGIN_API_KEY` | Yes | - | Your API key |
| `PLUGIN_ENABLED` | No | `true` | Enable/disable plugin |
```

### 5. **Exported Functions/Tools**
- [ ] Section listing all exported tools, agents, resources, etc.
- [ ] Function signatures with parameter types
- [ ] Brief description of what each function does
- [ ] Parameter descriptions from docstrings

**Example:**
```markdown
## Exported Functions

### Tools

#### `send_discord_notification(message, title, bot_name) -> bool`
Send a notification message to Discord via webhook.

**Parameters:**
- `message` (str): The message content to send to Discord
- `title` (str, optional): Optional title for the Discord embed
- `bot_name` (str, optional): Optional bot name to display as sender

**Returns:** `bool` - True if message was sent successfully, False otherwise
```

### 6. **Usage**
- [ ] Code examples showing basic usage
- [ ] Multiple examples for different use cases
- [ ] Clear, runnable code snippets
- [ ] Shows import statements

**Example:**
```markdown
## Usage

```python
from your_plugin import your_function

# Basic usage
result = your_function("example")

# With options
result = your_function("example", option=True)
```

### 7. **Setup/Prerequisites** (if applicable)
- [ ] Step-by-step setup instructions
- [ ] External service configuration (APIs, webhooks, etc.)
- [ ] Numbered steps that are easy to follow
- [ ] No unnecessary details

**Example:**
```markdown
## Setup API Access

1. Go to service.com → API Settings
2. Create new API key
3. Set `YOUR_PLUGIN_API_KEY` environment variable
```

## ❌ Things to Avoid

### Content to Remove:
- [ ] No excessive feature lists with emojis
- [ ] No detailed architecture explanations
- [ ] No comprehensive troubleshooting sections
- [ ] No changelog sections
- [ ] No contribution guidelines
- [ ] No license information (belongs in repo root)
- [ ] No extensive examples or tutorials
- [ ] No implementation details
- [ ] No plugin specification compliance mentions

### Writing Style:
- [ ] Avoid marketing language ("robust", "powerful", "efficient")
- [ ] Don't explain obvious things
- [ ] No wall-of-text paragraphs
- [ ] Keep technical jargon to minimum

## 📏 Length Guidelines

- **Total README length**: 30-60 lines maximum
- **Each section**: 3-10 lines
- **Code examples**: Keep minimal and focused
- **Descriptions**: One sentence per feature/function

## ✅ Quality Checks

### Clarity:
- [ ] A new user can understand what the plugin does in 30 seconds
- [ ] Setup instructions are clear and complete
- [ ] Code examples are copy-pasteable
- [ ] Function parameters are clearly explained

### Completeness:
- [ ] All exported functions are documented
- [ ] All required environment variables are listed
- [ ] All prerequisites are covered
- [ ] Examples cover main use cases

### Conciseness:
- [ ] No redundant information
- [ ] No excessive explanations
- [ ] Focus on essentials only
- [ ] Remove anything that doesn't help users get started

## 📋 Validation Command

Run this mental checklist:
1. **5-second test**: Can someone understand what this plugin does in 5 seconds?
2. **Copy-paste test**: Can someone copy the usage examples and run them?
3. **Setup test**: Can someone follow the setup instructions without confusion?
4. **Length test**: Is this README under 60 lines?

## 📝 Template

```markdown
# [Plugin Name]

[One-line description of what the plugin does]

## What it does

- [Main functionality point 1]
- [Main functionality point 2]  
- [Return value/behavior information]

## Requirements

- Python 3.10+
- `dependency>=version`
- Platform: [any/linux/windows/macos]

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VAR_NAME` | Yes/No | value | Description |

## Exported Functions

### Tools

#### `function_name(param1, param2) -> return_type`
Brief description of what the function does.

**Parameters:**
- `param1` (type): Description
- `param2` (type, optional): Description

**Returns:** `type` - Description

## Usage

```python
from plugin_name import function_name

# Basic example
result = function_name("example")

# Advanced example
result = function_name("example", option=True)
```

## Setup [Service Name] (if needed)

1. Step one
2. Step two  
3. Step three
```

---

**Remember: A good README gets users started quickly without overwhelming them with details.** 