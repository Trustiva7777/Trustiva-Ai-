import { promises as fs } from "fs";
import path from "path";

const out = path.resolve(process.cwd(), "..", "dist");
await fs.rm(out, { recursive: true, force: true });
await fs.mkdir(out, { recursive: true });

const html = `<!doctype html>
<html><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>TRUSTIVA</title>
<style>body{font-family:system-ui,Segoe UI,Roboto,Arial,Apple Color Emoji,Noto Color Emoji;-webkit-font-smoothing:antialiased;margin:0;padding:3rem;line-height:1.5;background:#0b0b0c;color:#e9e9eb}h1{font-weight:650;letter-spacing:.3px}code{padding:.15rem .35rem;border-radius:.35rem;background:#1a1a1b}</style>
</head><body>
<h1>TRUSTIVA — Deployed via IPFS</h1>
<p>This page is served from the IPFS gateway as a smoke test.</p>
<p>Build → <code>npm run build:ipfs</code>, Publish → <code>make publish</code>.</p>
</body></html>`;
await fs.writeFile(path.join(out, "index.html"), html, "utf8");
await fs.writeFile(path.join(out, "404.html"), html, "utf8");
console.log("dist/ ready");
