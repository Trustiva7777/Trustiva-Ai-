#!/usr/bin/env node
import process from 'process';

const tx = process.argv[2];
const waitFlag = (process.argv.includes('--wait') || process.argv.includes('--wait=true'));
const timeoutMs = Number((process.env.XRPL_WAIT_TIMEOUT_MS || 20000));

if (!tx) {
  console.error('usage: xrpl-verify-live.mjs <TX_HASH> [--wait]');
  process.exit(1);
}

async function verifyLive() {
  const xrpl = await import('xrpl').catch(() => null);
  if (!xrpl) {
    console.log(JSON.stringify({ validated: false, reason: 'xrpl not installed', tx }));
    return;
  }
  const { Client } = xrpl;
  const url = process.env.XRPL_NET === 'mainnet' ? 'wss://xrplcluster.com' : 'wss://s.altnet.rippletest.net:51233';
  const client = new Client(url);
  await client.connect();
  const start = Date.now();
  let out = null;
  try {
    while (true) {
      const r = await client.request({ command: 'tx', transaction: tx, binary: false });
      const meta = r?.result?.meta || {};
      const validated = !!r?.result?.validated;
      out = {
        validated,
        ledger_index: r?.result?.ledger_index || null,
        result: meta?.TransactionResult || null,
        tx
      };
      if (validated || !waitFlag) break;
      if (Date.now() - start > timeoutMs) break;
      await new Promise(res => setTimeout(res, 1500));
    }
  } catch (e) {
    out = { validated: false, error: String(e), tx };
  }
  await client.disconnect();
  console.log(JSON.stringify(out));
}

verifyLive().catch(e => { console.error(e); process.exit(1); });
