# Python 1-File SSG

A lightweight, 1-file Python-based static site generator designed for simplicity and flexibility. It transforms plain HTML files with frontmatter and simple templating tags into a fully static website.

## Features

*   **Simple Templating**: Use native HTML-like tags for includes and variables.
*   **Layout Inheritance**: Wrap content in reusable layouts.
*   **YAML Frontmatter**: Define metadata for each page (supports `PyYAML` if installed, with a fallback manual parser).
*   **Asset Management**: detailed handling of static assets like images, CSS, and JS.
*   **Auto Sitemap**: Automatically generates `sitemap.xml` for all built pages.
*   **Development Server**: Built-in HTTP server for previewing your site.
*   **Live Reloading**: "Watch" mode detects file changes and rebuilds automatically (supports `watchdog`).

## Requirements

*   Python 3.6+

**Optional Recommended Packages:**
*   `PyYAML` (for advanced YAML frontmatter support)
*   `watchdog` (for efficient file system monitoring)

Install optional dependencies via pip:
```bash
pip install PyYAML watchdog
```

## Installation

1.  Clone this repository or download `ssg.py`.
2.  Ensure you have the required project structure (see below).

## Project Structure

Your project directory should look like this:

```text
my-website/
├── content/      # Your page content (HTML files)
├── layouts/      # Layout templates and reusable partials
├── assets/       # Static assets (CSS, JS, Images) - copied to /assets
├── extra/        # Files to copy to root (e.g., robots.txt, favicon.ico)
└── _output/      # Generated site (created automatically)
```

## Usage

Run the generator using the `ssg.py` script.

### Basic Syntax
```bash
python ssg.py <directory> <command>
```

### Commands

*   **`build`**: Compiles the site once to the `_output` folder.
    ```bash
    python ssg.py ./my-website build
    ```

*   **`serve`**: Builds the site and starts a local web server at `http://localhost:3000`.
    ```bash
    python ssg.py ./my-website serve
    ```

*   **`watch`**: Monitors the directory for changes and rebuilds automatically. Also runs the server.
    ```bash
    python ssg.py ./my-website watch
    ```

## Templating System

SSG uses a custom, HTML-friendly templating syntax.

### Frontmatter
Add metadata to the top of your HTML content files using YAML syntax between `---` lines.

```html
---
title: My Awesome Page
date: 2023-10-27
layout: base.html
---
<h1>Hello World</h1>
```

### Variables
Inject frontmatter variables into your content or layouts using the `<template variable="...">` tag.

```html
<title><template variable="title" default="My Site"></template></title>
```

### Layouts
Define a layout file (e.g., `layouts/base.html`). To use it, specify `layout: base.html` in your content's frontmatter. The content of your page will be injected into a `content` variable.

**layouts/base.html**:
```html
<!DOCTYPE html>
<html>
<head>
    <title><template variable="title"></template></title>
</head>
<body>
    <nav>...</nav>
    <main>
        <template variable="content"></template>
    </main>
    <footer>...</footer>
</body>
</html>
```

### Includes
Include other HTML files (partials) from the `layouts` directory using the `<template include="...">` tag.

```html
<template include="header.html"></template>
```

## License

AGPL-3.0
