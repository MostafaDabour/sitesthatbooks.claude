# SitesThatBook website

Live site for sitesthatbook.com. Websites for US home service businesses.

- `site/` is the finished website. Hosting (Vercel or Cloudflare Pages) publishes this folder. No build command needed.
- `src/` is the generator: page copy (`build.py`, `trades.py`, `posts.py`), styles, images and the form script.
- `build.sh` regenerates `site/` from `src/`.

## Hosting setup
- Vercel: Import this repo. Framework preset: Other. Build command: leave empty. Output directory: `site`.
- Cloudflare Pages: Connect this repo. Build command: leave empty. Build output directory: `site`.

Every push to `main` goes live automatically.

## Adding a blog post
Add an entry to `src/posts.py`, run `./build.sh`, commit and push. The blog index, sitemap and llms.txt update automatically.

## Forms
Forms send to a GHL inbound webhook, with logo and photo uploads going to Cloudinary. Set `GHL_WEBHOOK`, `CLOUDINARY_CLOUD` and `CLOUDINARY_PRESET` at the top of `src/build.py`, then rebuild.

## Copy rules
US English. No em dashes anywhere. Plain, confident, outcome first.
