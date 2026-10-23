# Repository Guidelines

## Purpose & Implementation Order

Build a Hugo website for the parents association of Aveiro’s music school, CMACG (`cmacg.pt`). The association’s existing website is `apeecmacg.org`.

1. Create a reusable Hugo theme named `apeecmacg`, resembling the existing website’s visual identity. Inspect archived HTML, styles, images, and representative pages before designing templates.
2. Programmatically migrate all content from the root-level `public_static.zip` web archive. Navigation and page structure may change; content completeness is mandatory.

Preserve Portuguese text and accents. Do not invent association information or replace original material with placeholder copy.

## Project Structure

The site is implemented in Hugo, with imported content and the original `public_static.zip` retained locally. Follow this layout:

- `hugo.toml`: site configuration, language, menus, and theme selection.
- `themes/apeecmacg/`: theme templates, partials, styles, and theme-owned assets.
- `content/`: migrated pages and posts, preferably page bundles for associated media.
- `static/`: shared downloads and assets requiring stable paths.
- `scripts/`: repeatable archive inventory, migration, and validation tools.
- `migration/`: source-to-destination mappings and completeness reports.

Keep extracted sources and generated `public/` output separate from authored files. Preserve the original ZIP unchanged; ignore `__MACOSX` and AppleDouble metadata during extraction.

## Development & Style

Use Hugo 0.168.0+ and Python 3.9+. Run `hugo server -D` for local previews and `hugo --gc --minify` for production builds. Reimport with `python3 scripts/migrate.py`; this overwrites generated imports, so preserve manual edits first. Validate a temporary build with `python3 scripts/validate.py /tmp/apeecmacg-build`. Keep commands documented in `README.md`.

Use semantic HTML, accessible navigation, responsive CSS, and reusable Hugo partials. Use two-space indentation in templates and styles, descriptive lowercase filenames, and consistent front matter. Keep theme presentation separate from association content. Avoid unnecessary JavaScript and dependencies.

## Migration & Verification

Inventory unique posts, pages, attachments, images, and other meaningful content before importing. Distinguish original entries from category, author, pagination, and feed duplicates. Preserve titles, dates, body content, captions, taxonomy, and available attribution; retain substantive comments when present.

Make imports deterministic and safe to rerun. Rewrite internal links and asset references, preserve legacy URLs through aliases where feasible, and report missing files or ambiguous conversions. Never silently discard content.

Verify source-to-output coverage, links, media, and Hugo builds. Compare representative desktop and mobile pages with the archived design. A successful build alone does not establish migration completeness.

## Contributions

No Git history or test framework exists yet. Use focused, imperative commits. Pull requests should explain changes and validation, include screenshots for visual updates, and provide migration counts and unresolved exceptions for imports. Keep credentials out of version control.
