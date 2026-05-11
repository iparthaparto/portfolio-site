# website-final

Static portfolio site: open [`index.html`](index.html) in a browser or deploy the folder to any static host (Netlify, Cloudflare Pages, GitHub Pages, Vercel static, etc.).

## Local preview

From this directory:

```bash
python3 -m http.server 8080
```

Then visit `http://localhost:8080/index.html`.

## Media hosting (Supabase)

Images are currently inlined as `data:image/...;base64,...` in `index.html`. You will upload each file to **Supabase Storage** and replace **only** the `src="..."` value with the public object URL (layout and CSS stay the same).

### One-time Supabase setup

1. Create a project at [https://supabase.com](https://supabase.com).
2. **Storage → New bucket**  
   - Name: `portfolio-media`  
   - Turn on **Public bucket** (so each object gets a stable public URL).
3. **SQL → New query** — paste and run [`supabase/storage-policies.sql`](supabase/storage-policies.sql). That allows public read for `anon` and `authenticated` on that bucket only. Do not grant anonymous **write** if uploads are manual in the dashboard.
4. **Storage → portfolio-media → Upload** — add JPEG, PNG, WebP, or MP4 (and similar) only. Use folders if you like, for example `home/hero.jpg`, `logos/jio.webp`, `projects/wpl-1.jpg`.

### Public URL shape

After upload, Supabase shows a link like:

`https://<project-ref>.supabase.co/storage/v1/object/public/portfolio-media/<path/to/file>`

Use that full string as `src="..."` on `<img>` (or on `<video src="...">` / `poster="..."` when you add video).

### Where to paste URLs (25 images today)

Use this list when you send URLs (or when editing `index.html`): replace the entire `data:image/...;base64,...` value with your Supabase URL, keeping the same tag and classes.

| # | Approx. line | Hint |
|---|----------------|------|
| 1 | 913 | Home grid hero photo (`hg-photo` cell) |
| 2 | 1064 | Standalone image block |
| 3 | 1087 | Client logo — JioCinema (`title="JioCinema"`) |
| 4 | 1089 | Client logo — Mumbai Indians |
| 5 | 1091 | Client logo — TATA IPL |
| 6 | 1098 | Standalone image block |
| 7 | 1135 | Project strip — WPL card (`data-detail='wpl'`) |
| 8–16 | 1136–1144 | Project card images (cricket gallery) |
| 17 | 1177 | Image in page content |
| 18–20 | 1211–1213 | Gallery / content images |
| 21–23 | 1220–1222 | Gallery / content images |
| 24–25 | 1229–1230 | Gallery / content images |

When you have a URL for a row, share: **line (or #) + full Supabase URL** and we can patch `index.html` without changing design.

## License

Add a license file if you publish the repo publicly.
