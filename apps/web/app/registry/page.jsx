export const dynamic = 'force-dynamic';

async function fetchRegistry() {
  const base = process.env.OPS_API_URL || 'http://127.0.0.1:9000';
  try {
    const res = await fetch(`${base}/registry`, { cache: 'no-store' });
    if (!res.ok) return { entries: [] };
    return await res.json();
  } catch {
    return { entries: [] };
  }
}

export default async function RegistryPage() {
  const { entries } = await fetchRegistry();
  return (
    <main style={{ padding: 24 }}>
      <h1>Trustiva Registry</h1>
      <p>Recent provenance entries from on-chain and IPFS operations.</p>
      <p style={{ marginTop: 8, opacity: 0.8 }}>Click a row to export an audit bundle for that CID.</p>
      {!entries?.length ? (
        <p>No entries yet.</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={{ textAlign: 'left', borderBottom: '1px solid #333' }}>Time</th>
              <th style={{ textAlign: 'left', borderBottom: '1px solid #333' }}>CID</th>
              <th style={{ textAlign: 'left', borderBottom: '1px solid #333' }}>Gateway</th>
              <th style={{ textAlign: 'left', borderBottom: '1px solid #333' }}>XRPL</th>
              <th style={{ textAlign: 'left', borderBottom: '1px solid #333' }}>Polygon</th>
              <th style={{ textAlign: 'left', borderBottom: '1px solid #333' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {entries.slice().reverse().map((e, i) => (
              <tr key={i} onClick={async () => {
                const base = process.env.OPS_API_URL || 'http://127.0.0.1:9000';
                const res = await fetch(`${base}/registry/resolve?cid=${e.cid}`);
                if (!res.ok) return;
                const data = await res.json();
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url; a.download = `audit-bundle-${e.cid}.json`; a.click();
                URL.revokeObjectURL(url);
              }} style={{ cursor: 'pointer' }}>
                <td style={{ padding: '6px 8px' }}>{new Date((e.time||0)*1000).toISOString()}</td>
                <td style={{ padding: '6px 8px', fontFamily: 'monospace' }}>{e.cid}</td>
                <td style={{ padding: '6px 8px' }}>
                  {e.url ? <a href={e.url} target="_blank" rel="noreferrer">Gateway</a> : '—'}
                </td>
                <td style={{ padding: '6px 8px' }}>
                  {e.xrpl ? (
                    typeof e.xrpl === 'string' ? e.xrpl : (
                      e.xrpl.tx ? <a href={`https://testnet.xrpl.org/transactions/${e.xrpl.tx}`} target="_blank" rel="noreferrer">{e.xrpl.tx.slice(0,10)}…</a> : '—'
                    )
                  ) : '—'}
                </td>
                <td style={{ padding: '6px 8px' }}>
                  {e.polygon ? (
                    typeof e.polygon === 'string' ? e.polygon : (
                      e.polygon.tx ? <a href={`https://polygonscan.com/tx/${e.polygon.tx}`} target="_blank" rel="noreferrer">{e.polygon.tx.slice(0,10)}…</a> : '—'
                    )
                  ) : '—'}
                </td>
                <td style={{ padding: '6px 8px' }}>
                  <a href={`/registry/verify`} onClick={(ev)=>ev.stopPropagation()}>Verify</a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
