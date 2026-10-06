# Directives (Layer 1: What to do)

Standard Operating Procedures (SOPs) live in this directory.

Each directive defines:
- **Goal**: High-level objective and definition of done
- **Inputs**: Required arguments, parameters, or input files
- **Execution Scripts**: Which deterministic script(s) in `execution/` to invoke
- **Outputs**: Deliverables or generated artifacts (e.g., deliverables in cloud services, intermediate files in `.tmp/`)
- **Edge Cases & Failure Modes**: Known failure modes, retry logic, rate limits, and fallback strategies

## Format Example

See `_template.md` in this directory for a standard SOP layout.
