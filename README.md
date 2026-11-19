# 💩 Poop Tracker

Live at **https://poop.davidp.dev**

A tiny installable PWA for logging poop days on a calendar. No build step, no backend, no accounts. Everything is stored in your browser's `localStorage` under the key `poop-tracker:v1`:

```json
{ "onboarded": true, "poops": { "2026-11-18": true } }
```

Because nothing leaves your device, clearing browser storage erases your history.

## Run locally

```bash
npm run dev
```

Then open http://localhost:5180. (It's just `python3 -m http.server` serving `public/`.) Service workers, and so offline use and install, need `localhost` or HTTPS.

## Deploy

Hosted on Cloudflare as an assets-only Worker, configured in `cloudflare.config.ts` (Worker `poop-tracker`, custom domain `poop.davidp.dev`). Deploy with the [`cf` CLI](https://developers.cloudflare.com/cf/):

```bash
npm install
npm run deploy
```

When you change any file in `public/`, bump `CACHE` in `public/sw.js` so installed copies pick up the update.

## Files

- `public/index.html`: markup for the header, calendar, confirm modal and onboarding
- `public/styles.css`: brown theme, with dark mode via `prefers-color-scheme`
- `public/app.js`: calendar rendering, storage, modals, onboarding
- `public/sw.js`: offline cache (network first, falls back to cache)
- `public/manifest.webmanifest` + `public/icons/`: PWA install metadata (PNGs rendered from `icons/icon.svg`)
- `public/og-image.png`: 1200×630 social share image, rendered from `assets/og-image.svg`:
  ```bash
  rsvg-convert -w 1200 -h 630 assets/og-image.svg -o public/og-image.png
  ```
- `public/robots.txt`, `public/sitemap.xml`: crawler basics. Open Graph, Twitter and JSON-LD tags live in `index.html`.
