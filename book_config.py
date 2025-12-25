"""Book configuration - customize for each book project."""

config = {
    # Book metadata
    "title": "Your Book Title",
    "slug": "your-book",
    "author": "Author Name",
    "language": "en",
    "publisher": "Publisher Name",

    # Page settings
    "size": "A5",

    # Content structure (4-file system)
    "content": {
        "frontmatter": "FrontMatter.md",
        "content": "Content.md",
        "backmatter": "Backmatter.md",
        "decisions": "Decisions.md",  # Non-printable
    },

    # Cover image (optional)
    "cover": "cover.png",

    # Output formats
    "formats": ["pdf", "epub"],
}
