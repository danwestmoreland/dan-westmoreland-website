# danwestmoreland.com

Static HTML site for Dan Westmoreland's fractional marketing business. Hosted on Netlify (site id 67d8729f-ba0c-45fc-b93d-41393418ef9d). No build step: the repository root is the published site.

## Working rules
- Pushing to `main` deploys to production once Netlify is linked to this repository. Get Dan's approval before pushing changes he has not seen.
- The homepage (`index.html`) and `/writing/` pages are hand-edited HTML with inline CSS. Other pages share `/assets/site.css` and `/assets/site.js`.
- Palette: paper #F6F5F1, elevated #FDFDFB, ink #15171A, ink-soft #4A4D52, rule #E2E1DB, accent #B8431F, pine green #1F3D36. Fonts: Fraunces (display) and Inter (body).
- Never use em dashes in copy.
- Testimonials (Luke Targett, Ben Tanksley) are quoted verbatim. Do not reword them. Luke's title is "Former CMO, Deputy".
- `book/index.html` holds the Netlify contact form. Keep `data-netlify="true"` and `netlify-honeypot="bot-field"` on the form tag.
- `netlify.toml` was rewritten when the site moved to GitHub on 2026-10-07; the original file could not be read back from Netlify.
