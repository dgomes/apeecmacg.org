# APEECMACG

Hugo website for the Associação de Pais e Encarregados de Educação do Conservatório de Música de Aveiro Calouste Gulbenkian. The reusable `apeecmacg` theme follows the archived website’s logo, white canvas, dark frame, typography, and sidebar layout.

## Requirements and local preview

- **Hugo 0.168.0 or later** (tested with 0.168.0; Extended works but is not required).
- **Python 3.9 or later** for migration and validation. No Python packages, Node, or WordPress are needed.

```sh
hugo server -D
```

Open <http://localhost:1313/>. Content, uploaded files, and theme assets are already imported, so the archive is not needed to preview or build.

```sh
hugo --gc --minify
```

Deploy the generated `public/` directory to a static web host. `hugo.toml` sets the canonical site URL to `https://apeecmacg.org/`; use `hugo --baseURL https://your-host.example/` for a different deployment. The host must serve directory `index.html` files and use `404.html` for missing routes. Hosting and DNS have not been changed.

## Editing

- `content/posts/<wordpress-id>/index.html`: imported posts.
- `content/pages/<wordpress-id>/index.html`: association pages. The useful-information guide uses a branch bundle at `content/pages/367/_index.html` with six topic bundles below it.
- `content/_index.md`: homepage shortcuts.
- `data/useful_information.json`: guide topic boundaries, titles, descriptions, and display order.
- `content/posts/_index.html`: the `/blog/` listing.
- `content/archives/`: generated legacy date listings.
- `static/wp-content/uploads/`: all original images and attachments, with stable legacy paths.
- `data/sidebar.json`: original sidebar text and contact links.
- `themes/apeecmacg/`: reusable templates, CSS, JavaScript, logo, and local fonts.

Imported HTML has JSON front matter to preserve the original body, tables, galleries, and captions without a lossy HTML-to-Markdown conversion. New posts can use Markdown; for example `hugo new content posts/my-post/index.md`. Set `title`, `date`, and `category = ['Classificados']` when appropriate, and remove `draft = true` before publishing. Use `author = ['direccao']` for the existing author taxonomy. The `url` field controls the public address independently of the source filename.

The homepage introduces the association, offers four shortcuts, and highlights the three most recent news posts. `/blog/` lists all **18 association news posts**; the **28 classified adverts** appear in `/category/classificados/`. Both lists and post-to-post navigation respect this separation. Original article URLs, date archives, and the complete RSS feed remain available. Old homepage pagination URLs and obsolete news pagination URLs redirect to `/blog/`.

`/informacoes-uteis/` is a topic index linking to contacts and school services, institutional email, the school card, regulations and insurance, legislation, and the Conservatory's history. The archived text is split without omissions or factual updates; these historical instructions have not been reverified with the school. The importer uses explicit topic boundaries and fails if they become ambiguous. Validation checks every fragment and reconstructs the complete original text checksum in source order. Change topic display order using `weight` in `data/useful_information.json`; keep the file's source order intact for splitting.

Search runs locally in the browser against Hugo’s generated `index.json`, ignores accents, and needs no search service. Page navigation works without JavaScript.

## Repeating the migration

Place the original `public_static.zip` in the project root, then run:

```sh
python3 scripts/migrate.py
hugo --gc --minify --destination /tmp/apeecmacg-build
python3 scripts/validate.py /tmp/apeecmacg-build
```

The importer reads directly from the ZIP and preserves it unchanged. Rerunning overwrites generated imported content, sidebar data, assets, and migration reports: back up manual edits before rerunning. It never deletes unrelated authored pages. The ZIP, extracted source, caches, and build output are ignored by Git.

`migration/report.json` records the ZIP checksum, all imported entries, original URLs, text checksums, asset checksums, archive listings, and URL repairs. The import contains **46 posts, six pages, and 647 uploaded files**. Listing pages, feeds, and API responses are checked as duplicate representations rather than imported as duplicate posts. All 52 unique article IDs appearing in archived listings have a canonical imported entry. The archived comments API is empty and no comment lists were found.

`migration/validation.json` records checks against an actual Hugo build: article text (including all six guide pages), uploaded-file hashes, legacy listings, local links and fragments, font files, and complete separation of news and classified listings. Validation exits nonzero on errors. Text checks normalize block boundaries and whitespace to tolerate Hugo minification while detecting missing or changed prose.

WordPress image-proxy URLs now use local originals. One duplicated Google Forms URL was repaired; the exact change is recorded in the migration report. The source’s historical text, prices, dates, contact information, and external links remain intact. YouTube embeds and one external emoji image still need their original services; external destinations have not been verified live. Local HTML previews were visually compared with the archived design in Safari at 1280 px and 390 px. A local development preview is also available with the command above.

## Contributions

Use focused commits and include build/validation results. Include desktop/mobile screenshots for visual changes. Do not commit the generated `public/` directory or the source ZIP. See [AGENTS.md](AGENTS.md) for contributor guidance and [theme documentation](themes/apeecmacg/README.md) for reuse.
