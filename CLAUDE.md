# danwestmoreland.com

Static HTML site for Dan Westmoreland's fractional marketing business. Hosted on Netlify (site id 67d8729f-ba0c-45fc-b93d-41393418ef9d). No build step: the repository root is the published site.

## Working rules
- Pushing to `main` deploys to production. Small, reversible changes (copy edits, a list item, a link, a single page tweak) can go straight to main; Dan said on 2026-10-14 the site "isn't life or death" and things can always be changed. Anything that reshapes a page, adds a section, or touches every page gets a holding branch and a screenshot preview first, then "push it".
- After any multi-file edit, check `git diff --stat` and page byte sizes before pushing; an over-greedy regex once stripped 21 pages' bodies. After pushing, verify live pages with curl (status plus section counts).
- The homepage (`index.html`) and `/writing/` pages are hand-edited HTML with inline CSS. Other pages share `/assets/site.css` and `/assets/site.js`.
- Palette: paper #F6F5F1, elevated #FDFDFB, ink #15171A, ink-soft #4A4D52, rule #E2E1DB, accent #B8431F, pine green #1F3D36. Fonts: Fraunces (display) and Inter (body).
- Never use em dashes in copy.
- Testimonials (Luke Targett, Ben Tanksley) are quoted verbatim. Do not reword them. Luke's title is "Former CMO, Deputy".
- `book/index.html` holds the Netlify contact form. Keep `data-netlify="true"` and `netlify-honeypot="bot-field"` on the form tag.
- `netlify.toml` was rewritten when the site moved to GitHub on 2026-10-07; the original file could not be read back from Netlify.
