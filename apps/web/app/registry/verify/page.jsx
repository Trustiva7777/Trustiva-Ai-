"use client";
import { useEffect, useState } from 'react';
import * as openpgp from 'openpgp';

async function fetchPubkey() {
  const base = process.env.OPS_API_URL || 'http://127.0.0.1:9000';
  try {
    const r = await fetch(`${base}/audit/pubkey`, { cache: 'no-store' });
    if (!r.ok) return '';
    const j = await r.json();
    return j.pubkey || '';
  } catch { return ''; }
}

async function sha256(buf) {
  const d = await crypto.subtle.digest('SHA-256', buf);
  return Array.from(new Uint8Array(d)).map(b=>b.toString(16).padStart(2,'0')).join('');
}

export default function VerifyPage() {
  const [pubkey, setPubkey] = useState('');
  const [bundle, setBundle] = useState(null);
  const [checksum, setChecksum] = useState('');
  const [sig, setSig] = useState('');
  const [result, setResult] = useState(null);

  useEffect(()=>{ fetchPubkey().then(setPubkey); }, []);

  async function handleVerify() {
    try {
      if (!bundle) throw new Error('Bundle missing');
      const bytes = new TextEncoder().encode(JSON.stringify(bundle));
      const hash = await sha256(bytes);
      const checksumOk = !checksum || checksum.trim() === hash;
      let sigOk = false;
      if (pubkey && sig) {
        const pub = await openpgp.readKey({ armoredKey: pubkey });
        const message = await openpgp.createMessage({ text: JSON.stringify(bundle) });
        const signature = await openpgp.readSignature({ armoredSignature: sig });
        const verification = await openpgp.verify({ message, signature, verificationKeys: pub });
        sigOk = verification.signatures[0]?.verified; // promise-like
        if (sigOk?.then) sigOk = await sigOk;
      }
      setResult({ checksumOk, sigOk: !!sigOk, hash });
    } catch (e) {
      setResult({ error: String(e) });
    }
  }

  return (
    <main style={{ padding: 24 }}>
      <h1>Verify Audit Bundle</h1>
      <p>Drop your audit-bundle.json, optional .sha256, and optional .asc signature.</p>
      <div style={{ display: 'grid', gap: 12, maxWidth: 800 }}>
        <textarea placeholder="Paste audit-bundle.json" rows={10} onChange={e=>{
          try { setBundle(JSON.parse(e.target.value)); } catch { setBundle(null); }
        }} />
        <textarea placeholder="Paste audit-bundle.json.sha256 (optional)" rows={2} onChange={e=> setChecksum(e.target.value.trim()) } />
        <textarea placeholder="Paste audit-bundle.json.asc (optional)" rows={6} onChange={e=> setSig(e.target.value)} />
        <button onClick={handleVerify} style={{ padding: '8px 12px' }}>Verify</button>
      </div>
      {result && (
        <div style={{ marginTop: 16 }}>
          {result.error ? (
            <p style={{ color: 'crimson' }}>Error: {result.error}</p>
          ) : (
            <>
              <p>SHA-256: <code>{result.hash}</code></p>
              <p>Checksum: {result.checksumOk ? '✅ OK' : '⚠️ Mismatch'}</p>
              <p>Signature: {result.sigOk ? '✅ OK' : '—'}</p>
            </>
          )}
        </div>
      )}
    </main>
  );
}
