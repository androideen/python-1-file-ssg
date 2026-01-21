# Python 1-File SSG

A lightweight, powerful, and portable 1-file Python-based static site generator. Designed for developers who want simplicity without sacrificing essential features like layout inheritance, partials, and YAML frontmatter.

## Features

*   **Zero Configuration**: Just one script and a standard folder structure.
*   **Simple Templating**: Use native HTML-like tags (`<template variable="...">` and `<template include="...">`).
*   **Layout Inheritance**: Wrap your content in reusable layouts easily.
*   **YAML Frontmatter**: Metadata support with automatic sitemap generation.
*   **Built-in Server**: Includes a development server with "Watch" mode for live rebuilding.
*   **Asset Management**: Automatic handling of CSS, JS, and image assets.

## Requirements

*   Python 3.6+

**Optional Recommended Packages:**
*   `PyYAML`: For advanced YAML parsing (manual fallback included).
*   `watchdog`: For high-performance file monitoring in watch mode.

```bash
pip install PyYAML watchdog
```

## Repository Structure

The generator is designed to work with any directory following the standard structure. This repository includes the generator script and documentation sites:

```text
.
├── ssg.py            # The core Static Site Generator script
├── ssg/              # Example/Feature site: SSG
├── demo-site/        # Example/Feature site: Demo Site
├── LICENSE           # AGPL-3.0 License
└── README.md         # This file
```

### Site Project Structure
Each site directory (like `ssg/` or `demo-site/`) follows this standard layout:

```text
my-website/
├── content/      # Page content (HTML files with frontmatter)
├── layouts/      # Layout templates and reusable partials
├── assets/       # Static assets (CSS, JS, Images) -> copied to /assets
├── extra/        # Files copied directly to root (robots.txt, favicon, etc.)
└── _output/      # The generated static site (automatically created)
```

## Usage

Run the generator by pointing it to your site directory and choosing a command.

### Commands

*   **`build`**: Compiles the site once.
    ```bash
    python ssg.py ./ssg build
    ```

*   **`serve`**: Builds and starts a local server at `http://localhost:3000`.
    ```bash
    python ssg.py ./ssg serve
    ```

*   **`watch`**: Monitors for changes, rebuilds automatically, and runs the server.
    ```bash
    python ssg.py ./ssg watch
    ```

## Templating System

### Frontmatter
Add metadata to your HTML files using YAML syntax:

```html
---
title: Getting Started
layout: content.html
---
<h1>Hello SSG</h1>
```

### Variables
Inject frontmatter values or the special `content` variable:

```html
<title><template variable="title" default="My Site"></template></title>
<main><template variable="content"></template></main>
```

### Includes
Include partials from the `layouts/` directory:

```html
<template include="header.html"></template>
```

## License

[AGPL-3.0](LICENSE)
