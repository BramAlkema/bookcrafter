# Technical Decisions

> Last Updated: 2024-12-24
> Version: 1.0.0

## Architecture Decisions

### ADR-001: WeasyPrint over Vivliostyle

**Context:** Need a PDF rendering engine with CSS Paged Media support.

**Decision:** Use WeasyPrint (Python) instead of Vivliostyle (Node.js).

**Rationale:**
- All-Python stack simplifies installation and dependencies
- WeasyPrint v67+ supports `leader()` for TOC dot leaders
- Better integration with Python ecosystem (pdfplumber, ebooklib)
- Side-by-side comparison showed nearly identical output quality

**Consequences:**
- Some advanced CSS Paged Media features may be limited
- Must embed CSS in HTML `<style>` tags (not separate files)
- Font paths must be absolute for reliable loading

### ADR-002: 4-File Content Structure

**Context:** Need to organize book content in a maintainable way.

**Decision:** Use exactly 4 markdown files:
- `FrontMatter.md` - Cover, title page, copyright, dedication
- `Content.md` - Main chapters
- `Backmatter.md` - Bibliography, glossary, index, colophon
- `Decisions.md` - Non-printable editorial notes

**Rationale:**
- Separation matches traditional book structure
- Not too many files (unlike one-file-per-chapter approaches)
- Not too few (unlike monolithic single-file approaches)
- `Decisions.md` keeps editorial notes out of printed output

**Consequences:**
- Large books may have very long Content.md files
- Section parsing uses `# section-name` convention

### ADR-003: Embedded Fonts

**Context:** Need consistent typography across platforms.

**Decision:** Bundle fonts in `/fonts/` directory with @font-face.

**Rationale:**
- No external dependencies at build time
- Consistent rendering regardless of system fonts
- Control over exact font versions

**Consequences:**
- Repository size increased by ~3MB for fonts
- Must use properly licensed fonts (Google Fonts)
- Font paths require absolute path conversion for WeasyPrint

### ADR-004: CSS Variables for Theming

**Context:** Need to support multiple color schemes and potentially font pairs.

**Decision:** Use CSS custom properties (variables) for colors and typography.

**Rationale:**
- Easy to create themes by changing variable values
- Single source of truth for design tokens
- Compatible with both PDF and EPUB output

**Consequences:**
- Variable definitions in `brand.css`
- Must maintain fallback values for EPUB readers with limited CSS support

### ADR-005: CLI-First Interface

**Context:** Need a user interface for building books.

**Decision:** Start with CLI using argparse, defer GUI to later phases.

**Rationale:**
- Simpler to implement and maintain
- Better for automation and scripting
- Target users (self-publishers with markdown skills) comfortable with CLI
- GUI can be added later without architectural changes

**Consequences:**
- Not accessible to non-technical users initially
- Must ensure good error messages and help text

## Rejected Alternatives

### LaTeX
- Pro: Mature, excellent typography
- Con: Steep learning curve, complex dependencies, overkill for most books

### Pandoc
- Pro: Flexible, many output formats
- Con: Less control over typography, template system is complex

### Sphinx/MkDocs
- Pro: Great for documentation
- Con: Designed for technical docs, not narrative books

### Node.js/Vivliostyle
- Pro: Excellent CSS Paged Media support
- Con: Adds Node.js dependency, doesn't integrate with Python tools
