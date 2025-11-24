# Reference Materials (_ref)

This folder contains reference materials, documentation, code examples, and assets related to Modal platform development. **This folder is excluded from version control** to prevent accidental uploading of reference materials to repositories.

## Folder Structure

### `docs/`
Official Modal platform documentation and guides:
- `modal-sandboxes-setup.md` - Complete guide to setting up and using Modal Sandboxes
- `modal-sandbox-commands.md` - Documentation for running commands in sandbox environments
- `modal-opentelemetry-integration.md` - Guide for connecting Modal to OpenTelemetry providers
- `modal-dockerfile-deployment.md` - Using existing Docker images and Dockerfiles with Modal
- `modal-vibe-platform-guide.md` - Technical guide for the Modal Vibe AI coding platform

### `examples/`
Code examples demonstrating Modal platform features:
- `safe-code-execution.py` - Multi-language code execution in isolated sandboxes
- `claude-code-sandbox.py` - Running Claude Code agent in a Modal Sandbox for repository analysis

### `blog-posts/`
Blog posts and case studies about Modal platform usage:
- `modal-vibe-scalability-blog.md` - "Modal Vibe: Scaling AI Coding to Millions of Monthly Sessions"
- `hunch-modal-sandboxes-case-study.md` - How Hunch uses Modal Sandboxes for safe AI code execution

### `assets/`
Static assets and images:
- `modal-vibe-demo-image.png` - Demo image for Modal Vibe platform

## Purpose

This folder serves as a centralized reference library for:
- Understanding Modal platform capabilities and best practices
- Learning from real-world implementations and case studies
- Accessing code examples for common use cases
- Preserving important documentation and guides

## Security Note

⚠️ **This folder is intentionally excluded from version control** via `.gitignore`. It contains reference materials that should not be uploaded to public repositories. If you need to share any content from this folder, do so selectively and ensure it doesn't contain sensitive information.

## Contributing

When adding new reference materials:
1. Place content in the appropriate subfolder (`docs/`, `examples/`, `blog-posts/`, or `assets/`)
2. Use clear, descriptive filenames with kebab-case naming convention
3. Clean up file headers and remove any metadata specific to other systems
4. Ensure the content is appropriate for reference purposes
