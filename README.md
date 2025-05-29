# ld-agent-plugins

A collection of various plugins that have been developed to specification for the [ld-agent](https://github.com/ld-agent) ecosystem and shared with the community.

## 🔌 Available Plugins

### By batteryshark

#### 🎵 [Spotify Controller](python_plugins/batteryshark/spotify_controller/)
Control Spotify playback, search music, and manage playlists through the Spotify Web API. Features include play/pause/skip controls, volume management, device switching, playlist access, and comprehensive music search capabilities.

**Key Features:**
- Full playback control (play, pause, skip, volume)
- Search tracks, artists, albums, and playlists
- Device management and transfer
- User playlist access
- Premium Spotify account required for playback control

#### 🔍 [Google Web Search](python_plugins/batteryshark/google_websearch/)
Perform real-time web searches using Google Gemini API with grounding support. Returns AI-generated responses with detailed citations and references from web sources.

**Key Features:**
- Real-time web search capabilities
- AI-generated responses with grounding
- Automatic page title extraction and redirect following
- Structured results with metadata and citations
- Uses Google Gemini API

#### 📚 [Lexy Glossary](python_plugins/batteryshark/lexy/)
AI-powered glossary search and lookup tools with multiple search modes. Supports exact matching, fuzzy search for typos, and semantic search using natural language queries.

**Key Features:**
- Exact term lookup
- Fuzzy search with typo tolerance
- AI-powered semantic search
- Batch operations for multiple terms
- YAML-based glossary format
- Configurable AI models (Gemini/OpenAI)

#### 💬 [Discord Notifier](python_plugins/batteryshark/discord_notifier/)
Send notifications to Discord channels via webhooks. Simple and reliable way to get alerts and status updates directly in Discord.

**Key Features:**
- Webhook-based Discord messaging
- Custom titles and bot names
- Embed support
- Success/failure status returns

#### 📱 [Slack Notifier](python_plugins/batteryshark/slack_notifier/)
Send notifications to Slack channels via webhooks with support for Slack markdown formatting and custom titles.

**Key Features:**
- Webhook-based Slack messaging
- Slack markdown formatting support
- Optional message titles
- Success/failure status returns

#### 🍎 [macOS Notifier](python_plugins/batteryshark/macos_notifier/)
Send native macOS notification popups with custom messages and titles. Respects system notification settings and preferences.

**Key Features:**
- Native macOS notification system integration
- Custom notification sounds
- System preference compliance
- macOS-only compatibility

## 📋 Plugin Specification

All plugins in this repository are built according to the [ld-agent Plugin Specification v1.0](PLUGIN_DEVELOPMENT_GUIDE.md), ensuring:

- **Standardized Architecture**: Consistent file structure and organization
- **Type Safety**: Full Pydantic type annotations for all public functions
- **Auto-Discovery**: Standardized metadata for automatic plugin loading
- **Documentation**: Comprehensive docstrings and README files
- **Environment Configuration**: Structured environment variable definitions
- **Cross-Platform Support**: Clear platform compatibility specifications

## 🛠️ Development & Validation

This repository includes a validation tool (`validate_plugin.py`) that ensures plugins conform to the specification. Contributors are encouraged to validate their plugins before submission.

## 🤝 Contributing

We welcome contributions of new plugins! Please ensure your plugins:

1. Follow the [Plugin Development Guide](PLUGIN_DEVELOPMENT_GUIDE.md)
2. Include comprehensive documentation
3. Pass validation using `validate_plugin.py`
4. Include appropriate tests
5. Follow semantic versioning

## 📄 License & Usage

Each plugin may have its own licensing terms. Please check individual plugin directories for specific license information. The repository structure and specification are designed to facilitate easy integration with ld-agent systems.

## 🔗 Repository

**GitHub**: [https://github.com/ld-agent/ld-agent-plugins](https://github.com/ld-agent/ld-agent-plugins)
