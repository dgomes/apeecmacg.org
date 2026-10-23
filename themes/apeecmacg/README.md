# apeecmacg

A Hugo theme inspired by the association’s archived Twenty Sixteen website: an illustrated header, dark page frame, serif reading text, sans-serif headings, and a right sidebar. Layouts and CSS are newly written; no WordPress runtime or original theme code is required.

Requires Hugo 0.168.0+. Copy this directory into another Hugo project’s `themes/apeecmacg/` directory and set `theme = 'apeecmacg'`. Define `params.shortTitle`, `params.description`, `params.logo`, `params.email`, `params.facebook`, and `menus.main` in the host site’s configuration. Supply your own logo at the configured path.

The home page lists content with `type = 'posts'`. Define the taxonomies `category = 'category'` and `author = 'author'` to retain this site’s URLs; front matter uses `category` and `author` arrays. Configure home outputs as `['HTML', 'RSS', 'JSON']` for search and feeds. See the root `hugo.toml` for a complete example.

Optional `data/sidebar.json` is an array of objects with `title` and trusted `html` fields. The search widget links to `/pesquisa/`; add a content page with `layout = 'search'` to enable it. Imported HTML content requires the explicit `security.allowContent` configuration shown in the root configuration. Only allow trusted local editorial HTML.

New layout, CSS, and JavaScript code is available under the MIT license in `LICENSE`. Original association branding, photographs, documents, and editorial content retain their respective owners’ rights; they are not relicensed by the theme. Bundled Merriweather and Montserrat fonts use the SIL Open Font License; see `FONT-LICENSE.txt`.
