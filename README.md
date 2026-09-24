# tells-legal

Published legal pages and App Store copy for **Tells** (the iOS app), kept as
their own project so this content has a history independent of the app's code
repo, and so it can be hosted on GitHub Pages directly from this repo's root.

## Layout

- **Repo root** — the published pages, exactly as GitHub Pages serves them:
  `index.html`, `privacy-policy.html`, `terms-of-use.html`, `support.html`,
  `terms-of-use.txt` (pasted into App Store Connect's EULA field), plus
  `.nojekyll`.
- **`source/`** — the editable templates (still carrying `[PLACEHOLDER]`
  values and editorial comments — never publish these directly) and
  `fill-placeholders.py`, which fills them and writes the result to
  `source/dist/`. Copy `source/dist/*` up to the repo root to republish.
  **Never copy `source/*.html` to the root** — that ships the templates with
  their placeholders still in them.
- **`store/`** — `description.txt`, `review-notes.txt`, `beta-description.txt`:
  App Store Connect / TestFlight copy, versioned here for reference. Not
  served by Pages; nothing links to this folder.

## Publishing a change

```bash
cd source
python3 fill-placeholders.py
cp dist/*.html dist/*.txt dist/.nojekyll ..
cd ..
git add -A && git commit -m "..." && git push
```

## GitHub Pages

Settings → Pages → Source: Deploy from a branch → `main` → `/ (root)`.
