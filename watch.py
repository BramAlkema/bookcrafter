#!/usr/bin/env python3
"""Watch mode for BookCrafter - live preview with auto-rebuild."""

import sys
import time
import threading
import http.server
import socketserver
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from build import setup_instance, load_file, load_styles, STYLES_DIR
from content_parser import (
    parse_frontmatter_file, parse_content_file, parse_backmatter_file,
)
from templates import render_frontmatter, render_backmatter, assemble_book

# Configuration
PORT = 8000
DEBOUNCE_SECONDS = 0.5


class RebuildHandler(FileSystemEventHandler):
    """Handler that triggers rebuild on file changes."""

    def __init__(self, builder):
        self.builder = builder
        self.last_rebuild = 0
        self.pending = False

    def on_modified(self, event):
        if event.is_directory:
            return

        path = Path(event.src_path)

        # Only watch relevant files
        if path.suffix not in ['.md', '.css', '.html']:
            return

        # Debounce rapid changes
        now = time.time()
        if now - self.last_rebuild < DEBOUNCE_SECONDS:
            self.pending = True
            return

        self.last_rebuild = now
        self.builder.rebuild()

    def on_created(self, event):
        self.on_modified(event)


class LiveBuilder:
    """Manages live rebuilding of the book."""

    def __init__(self, config, content_dir, output_dir, target=None, typography=None, pages=200):
        self.config = config
        self.content_dir = content_dir
        self.output_dir = output_dir
        self.target = target
        self.typography = typography
        self.pages = pages
        self.html_path = output_dir / f"{config['slug']}.html"
        self.rebuild_count = 0

    def rebuild(self):
        """Rebuild HTML for preview."""
        self.rebuild_count += 1
        print(f"\n{'='*60}")
        print(f"Rebuild #{self.rebuild_count} at {time.strftime('%H:%M:%S')}")
        print('='*60)

        try:
            start = time.time()

            # Load content
            content_config = self.config.get("content", {})
            frontmatter_raw = load_file(content_config.get("frontmatter", "FrontMatter.md"))
            content_raw = load_file(content_config.get("content", "Content.md"))
            backmatter_raw = load_file(content_config.get("backmatter", "Backmatter.md"))

            # Parse
            frontmatter = parse_frontmatter_file(frontmatter_raw) if frontmatter_raw else {}
            content = parse_content_file(content_raw) if content_raw else {'html': '', 'toc': []}
            backmatter = parse_backmatter_file(backmatter_raw) if backmatter_raw else {}

            # Load styles
            css = load_styles(target=self.target, page_count=self.pages, typography=self.typography)

            # Render
            frontmatter_html = render_frontmatter(frontmatter, content['toc'], self.config)
            backmatter_html = render_backmatter(backmatter, self.config)

            # Assemble with live reload script
            full_html = assemble_book(
                frontmatter_html,
                content['html'],
                backmatter_html,
                css,
                self.config
            )

            # Add live reload script
            reload_script = '''
<script>
(function() {
    var lastModified = null;
    setInterval(function() {
        fetch(window.location.href, {method: 'HEAD'})
            .then(function(response) {
                var modified = response.headers.get('Last-Modified');
                if (lastModified && modified !== lastModified) {
                    window.location.reload();
                }
                lastModified = modified;
            });
    }, 1000);
})();
</script>
'''
            full_html = full_html.replace('</body>', reload_script + '</body>')

            # Write
            self.html_path.write_text(full_html)

            elapsed = time.time() - start
            print(f"Built: {self.html_path.name} ({elapsed:.2f}s)")
            print(f"Preview: http://localhost:{PORT}/{self.html_path.name}")

        except Exception as e:
            print(f"Build error: {e}")
            import traceback
            traceback.print_exc()


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that suppresses most logs."""

    def log_message(self, format, *args):
        # Only log errors
        if args[1] != '200':
            super().log_message(format, *args)


def serve(directory, port):
    """Start HTTP server in background."""
    import os
    os.chdir(directory)
    with socketserver.TCPServer(("", port), QuietHandler) as httpd:
        httpd.serve_forever()


def main():
    import argparse
    import build

    parser = argparse.ArgumentParser(description="Watch and rebuild book on changes")
    parser.add_argument("--instance", "-i", help="Instance to build")
    parser.add_argument("--target", "-t", help="Target platform (e.g., pumbo:a5_paperback_roman)")
    parser.add_argument("--typography", "-y", help="Typography preset")
    parser.add_argument("--pages", "-p", type=int, default=200, help="Estimated page count")
    parser.add_argument("--port", type=int, default=PORT, help="HTTP server port")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser")
    args = parser.parse_args()

    # Set up instance (this sets build.CONTENT_DIR, build.OUTPUT_DIR, etc.)
    config = setup_instance(args.instance)

    builder = LiveBuilder(
        config=config,
        content_dir=build.CONTENT_DIR,
        output_dir=build.OUTPUT_DIR,
        target=args.target,
        typography=args.typography,
        pages=args.pages
    )

    # Initial build
    builder.rebuild()

    # Start HTTP server in background (serve from output dir)
    server_thread = threading.Thread(target=serve, args=(build.OUTPUT_DIR, args.port), daemon=True)
    server_thread.start()

    print(f"\nServer running at http://localhost:{args.port}/")
    print(f"Watching: {build.CONTENT_DIR}, {STYLES_DIR}")
    print("Press Ctrl+C to stop\n")

    # Open browser
    if not args.no_browser:
        import webbrowser
        webbrowser.open(f"http://localhost:{args.port}/{config['slug']}.html")

    # Set up file watcher
    handler = RebuildHandler(builder)
    observer = Observer()
    observer.schedule(handler, str(build.CONTENT_DIR), recursive=True)
    observer.schedule(handler, str(STYLES_DIR), recursive=True)
    if build.INSTANCE_STYLES_DIR and build.INSTANCE_STYLES_DIR.exists():
        observer.schedule(handler, str(build.INSTANCE_STYLES_DIR), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nStopped watching.")

    observer.join()


if __name__ == "__main__":
    main()
