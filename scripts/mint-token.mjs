#!/usr/bin/env node
import { ethers } from "ethers";

// Minimal ERC-721 soulbound ABI: mint to owner with tokenURI, no transfers (enforced by contract)
const SBT_ABI = [
  "function safeMint(address to, string tokenURI) public returns (uint256)",
  "function owner() view returns (address)",
  "event Transfer(address indexed from, address indexed to, uint256 indexed tokenId)"
];

const rpc = process.env.POLYGON_RPC || "https://polygon-rpc.com";
const key = process.env.POLYGON_PRIVATE_KEY;
if (!key) {
  console.error("POLYGON_PRIVATE_KEY not set; dry-run only");
}

const args = Object.fromEntries(process.argv.slice(2).map(a=>{
  const [k,v] = a.split("=");
  return [k.replace(/^--/, ''), v??true];
}));

const provider = new ethers.JsonRpcProvider(rpc);
const wallet = key ? new ethers.Wallet(key, provider) : null;

// Require either --contract <addr> to use an existing deployed soulbound ERC721,
// or support a pure dry-run when POLYGON_PRIVATE_KEY is missing or --send not given.
async function main(){
  const tokenURI = args.note || args.tokenURI || (args.cid ? `ipfs://${args.cid}` : "");
  const to = args.to || (wallet ? wallet.address : "0x0000000000000000000000000000000000000000");
  const contractAddr = args.contract;
  const send = !!args.send && !!key && !!contractAddr;

  const out = { network: rpc, to, tokenURI, contract: contractAddr || null, dryRun: !send };
  if (!send) {
    console.log(JSON.stringify(out, null, 2));
    return;
  }

  const contract = new ethers.Contract(contractAddr, SBT_ABI, wallet);
  const tx = await contract.safeMint(to, tokenURI);
  const receipt = await tx.wait();
  // Find Transfer event with tokenId
  let tokenId = null;
  const iface = new ethers.Interface(SBT_ABI);
  for (const log of receipt.logs) {
    try {
      const parsed = iface.parseLog({ topics: log.topics, data: log.data });
      if (parsed?.name === 'Transfer') {
        tokenId = parsed.args[2]?.toString?.() ?? null;
        break;
      }
    } catch {}
  }
  console.log(JSON.stringify({ hash: receipt.transactionHash, to, tokenURI, contract: contractAddr, tokenId }, null, 2));
}

main().catch(e=>{ console.error(e); process.exit(1); });
