#!/usr/bin/env node
import process from 'process';

const cid = process.argv[2];
if (!cid) {
  console.error('usage: xrpl-anchor-cid.mjs <CID> [sha256]');
  process.exit(1);
}
const payloadHash = process.argv[3] || '';

async function main() {
  const xrpl = await import('xrpl').catch(() => null);
  if (!xrpl) {
    console.log(JSON.stringify({ cid, anchored: false, dryRun: true, reason: 'xrpl package not installed' }));
    return;
  }
  const { Client, Wallet } = xrpl;
  const url = process.env.XRPL_NET === 'mainnet' ? 'wss://xrplcluster.com' : 'wss://s.altnet.rippletest.net:51233';
  const seed = process.env.XRPL_SEED;
  if (!seed) {
    console.log(JSON.stringify({ cid, anchored: false, dryRun: true, reason: 'XRPL_SEED missing' }));
    return;
  }

  const client = new Client(url);
  await client.connect();
  const wallet = Wallet.fromSeed(seed);

  // Use a no-op Payment with memos (common anchoring pattern)
  const memoPayload = JSON.stringify({ cid, sha256: payloadHash });
  const tx = {
    TransactionType: 'Payment',
    Account: wallet.classicAddress,
    Destination: wallet.classicAddress,
    Amount: '1', // 1 drop
    Memos: [
      {
        Memo: {
          MemoType: Buffer.from('trustiva').toString('hex'),
          MemoData: Buffer.from(memoPayload).toString('hex')
        }
      }
    ]
  };
  const result = await client.submitAndWait(tx, { wallet });
  await client.disconnect();
  const txHash = result?.result?.hash || result?.tx_json?.hash || null;
  console.log(JSON.stringify({ cid, anchored: true, tx_hash: txHash, explorer: `https://testnet.xrpl.org/transactions/${txHash}` }));
}

main().catch(e => {
  console.log(JSON.stringify({ cid, anchored: false, error: String(e) }));
  process.exit(1);
});
