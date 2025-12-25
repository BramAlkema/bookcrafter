# Product Mission

> Last Updated: 2024-12-24
> Version: 1.0.0

## Pitch

BookCrafter is an open-source Python-based book production system that helps self-publishers and indie authors create professional-quality PDF and EPUB books by providing a simple 4-file markdown workflow with full typography control, without requiring expensive commercial tools like Vellum or Atticus.

## Users

**Primary Users:**
- **Self-Publishers**: Indie authors who want professional book production without subscription fees or expensive software
- **Open Source Advocates**: Developers and writers who prefer free, transparent, and customizable tools
- **Technical Writers**: Documentation teams who need book-quality output from markdown sources

**Secondary Users:**
- **Small Publishers**: Independent publishers looking for affordable production pipelines
- **Educators**: Authors of textbooks and course materials
- **Hobbyist Authors**: Writers creating personal projects, family histories, or limited-run books

### User Personas

**Alex the Indie Author** (35-50)
- **Role:** Self-published fiction/non-fiction author
- **Context:** Has written manuscripts, uses markdown, comfortable with command line
- **Pain Points:** Vellum is Mac-only and expensive, Atticus subscription adds up, Word templates are inconsistent
- **Goals:** Professional-looking books, consistent typography, control over design

**Sam the Open Source Developer** (25-40)
- **Role:** Developer who also writes technical books or documentation
- **Context:** Prefers open source tools, wants reproducible builds, uses git for version control
- **Pain Points:** Commercial tools are black boxes, hard to integrate with CI/CD, vendor lock-in
- **Goals:** Automation, transparency, customization, markdown-native workflow

## The Problem

### Expensive and Proprietary Tools

Professional book production software costs $250-$500 (Vellum) or $15/month (Atticus), with no free alternatives offering comparable quality. This prices out many indie authors and hobbyists.

**Our Solution:** BookCrafter is 100% free and open source, using Python and WeasyPrint.

### Platform Lock-in

Vellum is Mac-only. Atticus requires cloud connectivity. Word templates produce inconsistent results across platforms. Authors are locked into specific ecosystems.

**Our Solution:** Cross-platform Python that runs on any OS with full offline capability.

### Complexity vs. Control Trade-off

GUI tools hide typography decisions. Manual tools (LaTeX) have steep learning curves. Authors must choose between simplicity and control.

**Our Solution:** Simple 4-file markdown structure with full CSS typography control for those who want it.

### No Proper Front/Back Matter

Most markdown-to-PDF tools are designed for documentation, not books. They lack support for title pages, copyright pages, dedications, bibliographies, indices, and colophons.

**Our Solution:** Dedicated front matter and back matter handling with professional templates.

## Differentiators

### All-Python Stack

Unlike Node.js-based tools (Vivliostyle) or LaTeX-based systems, BookCrafter uses a pure Python stack (WeasyPrint + ebooklib). This means simpler installation, better integration with Python workflows, and easier contributions from Python developers.

### 4-File Content Structure

Unlike monolithic markdown files or complex directory structures, BookCrafter uses exactly 4 files:
- `FrontMatter.md` - Cover, title page, copyright, dedication
- `Content.md` - Main chapters and body text
- `Backmatter.md` - Bibliography, glossary, index, colophon
- `Decisions.md` - Non-printable editorial notes

This separation keeps content organized without overwhelming complexity.

### Professional Typography Out of the Box

BookCrafter includes CSS Paged Media support with dot-leader TOCs, running headers, proper page counters, widow/orphan control, and custom fonts. Unlike basic markdown converters, it produces publication-ready output.

## Key Features

### Core Features

- **PDF Generation**: High-quality PDF output using WeasyPrint with CSS Paged Media support
- **EPUB Generation**: Valid EPUB3 output using ebooklib for e-readers
- **4-File Structure**: Organized content separation for front matter, content, back matter, and editorial notes
- **Custom Fonts**: Full font embedding with @font-face support (Montserrat, Baloo Bhai 2 included)

### Typography Features

- **Dot-Leader TOC**: Table of contents with page numbers and leader dots
- **Running Headers**: Automatic chapter titles in page headers
- **Page Counters**: Roman numerals for front matter, Arabic for content
- **Widow/Orphan Control**: Prevention of single lines at page breaks

### Editorial Features

- **Decisions.md**: Non-printable file for style notes, narrative arcs, and version history
- **Metadata Parsing**: YAML frontmatter and `::key:: value` inline metadata
- **Auto-Generated TOC**: Table of contents built from content headings
- **Pagination Check**: PDF analysis for potential widow/orphan issues

### Developer Features

- **CLI Interface**: `build`, `check`, `preview` commands
- **HTML Preview**: Quick browser preview without PDF generation
- **Multiple Formats**: Output to PDF, EPUB, or HTML from single source
- **Simple Configuration**: Single `book_config.py` file for all settings
