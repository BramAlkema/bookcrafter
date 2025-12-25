# Analyze Product

This instruction guides the agent through analyzing the BookCrafter codebase and maintaining Agent OS documentation.

## Steps

1. **Read existing documentation** - Check `.agent-os/product/` files for current state
2. **Explore codebase** - Use the Explore agent to understand architecture
3. **Update tech-stack.md** - Reflect actual dependencies and structure
4. **Update roadmap.md** - Mark completed features and identify gaps
5. **Create/update decisions.md** - Document architectural decisions

## Key Files to Analyze

- `build.py` - Main build orchestrator
- `content_parser.py` - Markdown content processing
- `typography.py` - Typography system with font pairs
- `templates.py` - HTML template rendering
- `lulu_specs.py` / `pumbo_specs.py` - POD platform specifications
- `tools/check_pagination.py` - Quality assurance
- `styles/` - CSS styling system
