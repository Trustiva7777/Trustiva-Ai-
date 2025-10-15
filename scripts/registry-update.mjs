#!/usr/bin/env node
import fs from 'fs';

const args = Object.fromEntries(process.argv.slice(2).map(a=>{
  const [k,v] = a.split('=');
  return [k.replace(/^--/, ''), v??true];
}));

const entry = {
  time: Math.floor(Date.now()/1000),
  cid: args.cid || '',
  xrpl: args.xrpl || '',
  polygon: args.polygon || '',
  url: args.url || '',
  sha: args.sha || args.sha256 || ''
};

if (!entry.cid) {
  console.error('usage: registry-update.mjs --cid=<CID> [--xrpl=<TX>] [--polygon=<TX>] [--url=<URL>]');
  process.exit(1);
}

const path = args.file || 'trustiva-registry.ndjson';
fs.appendFileSync(path, JSON.stringify(entry) + '\n');
console.log(JSON.stringify({ ok: true, path }));
