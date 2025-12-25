# Product Roadmap

> Last Updated: 2024-12-25
> Version: 1.1.0
> Status: Active Development

## Phase 0: Core Foundation (Completed)

**Goal:** Core book production pipeline with professional typography
**Status:** Done

### Implemented Features

- [x] **PDF Generation** - WeasyPrint-based PDF output with CSS Paged Media
- [x] **EPUB Generation** - Valid EPUB3 output using ebooklib (patched)
- [x] **4-File Content Structure** - FrontMatter.md, Content.md, Backmatter.md, Decisions.md
- [x] **Content Parser** - YAML frontmatter, section splitting, metadata extraction
- [x] **HTML Templates** - Renderers for all front/back matter sections
- [x] **Custom Fonts** - Embedded fonts with @font-face support
- [x] **TOC Generation** - Automatic table of contents from headings
- [x] **Dot Leaders** - CSS `leader(dotted)` for TOC page numbers
- [x] **Running Headers** - Chapter titles in page headers via `string-set`
- [x] **Page Counters** - Automatic page numbering
- [x] **Pagination Check** - PDF analysis for widow/orphan detection
- [x] **CLI Interface** - `build`, `check`, `preview` commands
- [x] **Multiple Output Formats** - PDF, EPUB, HTML from single source

## Phase 1: Design System (Completed)

**Goal:** Flexible typography and color customization
**Status:** Done

### Implemented Features

- [x] **Font Pairs** - 11+ curated heading/body font combinations
  - Serif pairs (Playfair Display + Lora, Libre Baskerville + Crimson Text)
  - Sans pairs (Inter + Source Sans 3, Poppins + Open Sans)
  - Mixed pairs (Merriweather + Lato, Source Serif + Inter)
- [x] **Density Presets** - 5 text density options (tight, snug, normal, relaxed, loose)
- [x] **Typography System** - `typography.py` with optical size adjustment
- [x] **Smart Typography** - Curly quotes, em dashes, ellipsis, abbreviation spacing
- [x] **Font Auto-Download** - Google Fonts fetching via `font_downloader.py`
- [x] **CSS Variables** - Theming via custom properties in brand.css
- [x] **Color Configuration** - Simple config for palette selection

## Phase 2: Print-on-Demand Support (Completed)

**Goal:** Platform-specific exports for major POD services
**Status:** Done

### Implemented Features

- [x] **Lulu Specifications** - `lulu_specs.py` with 18+ trim sizes
  - Trim sizes (5x8, 5.5x8.5, 6x9, A5, etc.)
  - Paper types (60#/80# cream/white)
  - Binding types with page count constraints
  - Margin and bleed calculations
- [x] **Pumbo Specifications** - `pumbo_specs.py` for Dutch POD service
  - European metric specifications
  - Paper bulk factors for spine calculation
  - Format-specific bleed/margin rules
- [x] **Screen PDF** - RGB-optimized output for digital reading
- [x] **Live Development** - `watch.py` with hot reload and HTTP server

## Phase 3: Quality Assurance (Completed)

**Goal:** Production-ready validation tools
**Status:** Done

### Implemented Features

- [x] **Pagination Checker** - `tools/check_pagination.py` (23KB)
  - Orphan/widow detection
  - Stranded heading detection
  - Split table detection
  - Excessive whitespace warnings
- [x] **Preflight Validator** - `tools/preflight.py` (12KB)
  - Runt detection (single-word last lines)
  - River detection (whitespace gaps)
  - Image resolution checks (<300 DPI)
  - Color profile validation

## Phase 4: Cover Generation (Not Started)

**Goal:** Full cover support including front, spine, and back
**Success Criteria:** Generate print-ready cover PDFs

### Features

- [ ] **Front Cover Template** - Configurable cover layout `M`
- [ ] **Cover Image Support** - Background images and graphics `M`
- [ ] **Spine Generation** - Automatic spine width from page count `L`
- [ ] **Back Cover Template** - Blurb, author bio, barcode area `M`
- [ ] **Full Wrap Cover** - Combined front/spine/back for POD `L`
- [ ] **Cover Dimensions** - Configurable trim sizes `S`

### Dependencies

- Image processing (Pillow already included)
- Platform specs for cover requirements (already have Lulu/Pumbo)

## Phase 5: Book Templates (Not Started)

**Goal:** Genre-specific templates with appropriate typography
**Success Criteria:** One-click selection of complete book styles

### Features

- [ ] **Novel Template** - Fiction-optimized with chapter ornaments `M`
- [ ] **Non-Fiction Template** - Sections, sidebars, callouts `M`
- [ ] **Memoir Template** - Photo support, timeline layouts `L`
- [ ] **Technical Template** - Code blocks, diagrams, indices `L`
- [ ] **Poetry Template** - Verse formatting, spacing control `S`
- [ ] **Template Switching** - Easy template change in config `S`

### Dependencies

- Phase 4 (cover styles matching templates)

## Phase 6: Advanced Features (Not Started)

**Goal:** Professional-grade enhancements
**Success Criteria:** Feature parity with commercial tools

### Features

- [ ] **Drop Caps** - Decorative first letters `S`
- [ ] **Chapter Ornaments** - Decorative breaks and flourishes `S`
- [ ] **Footnotes/Endnotes** - Proper academic referencing `M`
- [ ] **Image Handling** - Figures with captions and numbering `M`
- [ ] **Cross-References** - "See Chapter X" links `M`
- [ ] **Index Generation** - Automated index building `XL`
- [ ] **PDF/X-1a Export** - Commercial print standard `L`
- [ ] **CMYK Conversion** - Color profile for print `L`

## Effort Scale

- **XS:** 1 day
- **S:** 2-3 days
- **M:** 1 week
- **L:** 2 weeks
- **XL:** 3+ weeks

## Success Metrics

### Technical
- PDF file size within 2x of commercial tools
- EPUB passes epubcheck validation
- Build time under 10 seconds for typical books

### Adoption
- GitHub stars as indicator of interest
- Issue reports showing active usage
- Contributions from community

## Risk Mitigation

### Technical Risks
- **WeasyPrint limitations**: Some CSS Paged Media features not fully supported
- **Font licensing**: Must use properly licensed fonts (Google Fonts are safe)
- **Cross-platform testing**: Windows may need additional GTK setup

### Market Risks
- **Commercial competition**: Atticus adding features rapidly
- **Scope creep**: Must maintain simplicity as core value
