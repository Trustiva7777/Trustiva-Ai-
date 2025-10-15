import { ethers } from "hardhat";

async function main() {
  const root = process.env.ROOT as string;
  const cid = process.env.CID as string;
  const poiAddr = process.env.POI as string;
  const registryAddr = process.env.PROOFCHAIN_REGISTRY as string;
  if (!root || !cid || !poiAddr || !registryAddr) {
    throw new Error("Missing env: ROOT, CID, POI, PROOFCHAIN_REGISTRY");
  }

  const poi = await ethers.getContractAt("ProofChain", poiAddr);
  const reg = await ethers.getContractAt("AuditRegistry", registryAddr);

  const tx1 = await poi.finalize(root);
  await tx1.wait();
  const tx2 = await reg.registerBundle(root, cid);
  await tx2.wait();
  console.log(JSON.stringify({ finalizedTx: tx1.hash, registerTx: tx2.hash, cid, root }));
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
