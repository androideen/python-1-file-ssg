import os
import shutil
import re
import argparse
import sys
import time
import http.server
import socketserver
import threading
from pathlib import Path
from datetime import datetime
from email.utils import formatdate

# Try to import advanced modules
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False

# --- Core Logic ---

class SSG:
    def __init__(self, directory):
        self.base_dir = Path(directory).resolve()
        self.content_dir = self.base_dir / 'content'
        self.output_dir = self.base_dir / '_output'
        self.layouts_dir = self.base_dir / 'layouts'
        self.assets_dir = self.base_dir / 'assets'
        self.extra_dir = self.base_dir / 'extra'
        
        if not self.content_dir.exists():
            print(f"Error: Content directory not found at {self.content_dir}")
            sys.exit(1)

    def parse_frontmatter(self, content):
        """
        Parses YAML frontmatter block.
        Returns (frontmatter_dict, content_body)
        """
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
        if match:
            fm_text = match.group(1)
            body = match.group(2)
            
            metadata = {}
            if HAS_YAML:
                try:
                    metadata = yaml.safe_load(fm_text) or {}
                except yaml.YAMLError as e:
                    print(f"Warning: YAML parse error: {e}")
            else:
                # Simple manual parser
                for line in fm_text.splitlines():
                    if ':' in line:
                        key, value = line.split(':', 1)
                        metadata[key.strip()] = value.strip()
            
            return metadata, body
        return {}, content

    def process_includes(self, content):
        """
        Recursively replaces <template include="filename.html">
        """
        pattern = r'<template\s+include=["\'](.*?)["\']\s*>'
        
        def replace_include(match):
            filename = match.group(1)
            filepath = self.layouts_dir / filename
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    included_content = f.read()
                    # Recursive processing
                    return self.process_includes(included_content)
            else:
                print(f"Warning: Include file not found: {filename}")
                return "" # or keep tag?
        
        return re.sub(pattern, replace_include, content)

    def process_variables(self, content, variables):
        """
        Replaces <template variable="varname" default="val">
        """
        pattern = r'<template\s+variable=["\'](.*?)["\'](?:\s+default=["\'](.*?)["\'])?\s*>'
        
        def replace_variable(match):
            var_name = match.group(1)
            default_val = match.group(2) or ""
            
            # Handle nested variables if any (e.g. object.prop) - keeping it simple for now
            val = variables.get(var_name, default_val)
            return str(val)
            
        return re.sub(pattern, replace_variable, content)

    def build_page(self, file_path):
        """
        Reads a content file, processes it, and returns (output_rel_path, final_html, metadata).
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
            
        metadata, body = self.parse_frontmatter(raw_content)
        
        # Handle Layout Inheritance
        if 'layout' in metadata:
            layout_name = metadata['layout']
            layout_path = self.layouts_dir / layout_name
            if layout_path.exists():
                # Process the inner content first
                body = self.process_includes(body)
                body = self.process_variables(body, metadata)
                
                # Make content available as a variable
                metadata['content'] = body
                
                # Load layout as the new body
                with open(layout_path, 'r', encoding='utf-8') as f:
                    body = f.read()
            else:
                print(f"Warning: Layout {layout_name} not found for {file_path}")

        # 1. Process Includes (Doing this first allows templates to have variables? 
        # Or should we Substitute variables first?
        # User plan: "Parse Content -> Extract Frontmatter -> Apply Templates -> Generate HTML -> Write"
        # "Template Engine -> Include directive... Replace with file content"
        # "Variable directive... Replace with frontmatter values"
        
        # If I include a header that has <template variable="title">, I need to process includes first, then variables.
        pass1 = self.process_includes(body)
        pass2 = self.process_variables(pass1, metadata)
        
        
        # Determine output path
        rel_path = file_path.relative_to(self.content_dir)
        
        if rel_path.name == 'index.html':
            # content/index.html -> _output/index.html
            # content/blog/index.html -> _output/blog/index.html
            output_rel_path = rel_path
        else:
            # content/blog/post1.html -> _output/blog/post1/index.html
            output_rel_path = rel_path.with_suffix('') / 'index.html'
            
        return output_rel_path, pass2, metadata

    def generate_sitemap(self, pages):
        """
        Generates sitemap.xml
        """
        sitemap = ['<?xml version="1.0" encoding="UTF-8"?>']
        sitemap.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
        
        for path, meta in pages:
            # Assuming base url is / for now or we could add a config
            url_path = str(path).replace('index.html', '').replace('\\', '/')
            if not url_path.startswith('/'):
                url_path = '/' + url_path
                
            priority = "0.8"
            if url_path == '/': priority = "1.0"
            
            # Date
            lastmod = meta.get('date', datetime.now().strftime('%Y-%m-%d'))
            
            sitemap.append('  <url>')
            sitemap.append(f'    <loc>{url_path}</loc>')
            sitemap.append(f'    <lastmod>{lastmod}</lastmod>')
            sitemap.append(f'    <priority>{priority}</priority>')
            sitemap.append('  </url>')
            
        sitemap.append('</urlset>')
        
        with open(self.output_dir / 'sitemap.xml', 'w', encoding='utf-8') as f:
            f.write('\n'.join(sitemap))

    def build(self):
        print(f"Building site from {self.base_dir}...")
        start_time = time.time()
        
        # Clean output
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir()

        # Track pages for sitemap
        built_pages = []

        # Process Content
        for root, dirs, files in os.walk(self.content_dir):
            for file in files:
                if file.endswith('.html'):
                    src_path = Path(root) / file
                    try:
                        out_rel_path, html, meta = self.build_page(src_path)
                        
                        out_path = self.output_dir / out_rel_path
                        out_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(out_path, 'w', encoding='utf-8') as f:
                            f.write(html)
                            
                        # Store for sitemap (using out_rel_path)
                        built_pages.append((out_rel_path, meta))
                        print(f"  Generated: {out_rel_path}")
                    except Exception as e:
                        print(f"  Error processing {src_path}: {e}")

        # Copy Assets
        if self.assets_dir.exists():
            shutil.copytree(self.assets_dir, self.output_dir / 'assets')
            print("  Copied assets")

        # Copy Extra
        if self.extra_dir.exists():
            for item in self.extra_dir.iterdir():
                dest = self.output_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)
            print("  Copied extra files")

        # Generate Sitemap
        self.generate_sitemap(built_pages)
        print("  Generated sitemap.xml")

        print(f"Build complete in {time.time() - start_time:.2f}s")

    def serve(self, port=3000):
        os.chdir(self.output_dir)
        handler = http.server.SimpleHTTPRequestHandler
        # Allow reusing address to avoid "Address already in use" errors on restart
        socketserver.TCPServer.allow_reuse_address = True
        
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"Serving at http://localhost:{port}")
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nServer stopped.")

    def watch(self):
        print("Watching for changes...")
        
        # Initial build
        self.build()
        
        # Start server in separate thread
        server_thread = threading.Thread(target=self.serve, kwargs={'port': 3000})
        server_thread.daemon = True
        server_thread.start()
        
        if HAS_WATCHDOG:
            print("Using Watchdog for monitoring.")
            event_handler = SSGEventHandler(self)
            observer = Observer()
            observer.schedule(event_handler, str(self.base_dir), recursive=True)
            observer.start()
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                observer.stop()
            observer.join()
        else:
            print("Watchdog not installed. Using polling (slower).")
            # Simple polling implementation
            last_mtime = 0
            try:
                while True:
                    # check max mtime of all files
                    current_max = 0
                    for root, _, files in os.walk(self.base_dir):
                        if '_output' in root: continue
                        for f in files:
                            p = Path(root) / f
                            mtime = p.stat().st_mtime
                            if mtime > current_max:
                                current_max = mtime
                    
                    if last_mtime == 0:
                        last_mtime = current_max
                    
                    if current_max > last_mtime:
                        print("\nChange detected. Rebuilding...")
                        self.build()
                        last_mtime = current_max
                        
                    time.sleep(1)
            except KeyboardInterrupt:
                print("Stopping watch...")

if HAS_WATCHDOG:
    class SSGEventHandler(FileSystemEventHandler):
        def __init__(self, ssg_instance):
            self.ssg = ssg_instance
            self.last_build = 0
            
        def on_any_event(self, event):
            if event.is_directory: return
            if '_output' in event.src_path: return
            
            # Debounce
            now = time.time()
            if now - self.last_build < 1:
                return
            
            print(f"\nChanged: {event.src_path}")
            self.ssg.build()
            self.last_build = now

# --- CLI ---

def main():
    parser = argparse.ArgumentParser(description="Static Site Generator")
    parser.add_argument('directory', help="Website directory")
    parser.add_argument('command', choices=['build', 'serve', 'watch'], help="Command to execute")
    
    args = parser.parse_args()
    
    ssg = SSG(args.directory)
    
    if args.command == 'build':
        ssg.build()
    elif args.command == 'serve':
        ssg.build()
        ssg.serve()
    elif args.command == 'watch':
        ssg.watch()

if __name__ == '__main__':
    main()
