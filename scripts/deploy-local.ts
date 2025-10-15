import { ethers } from "hardhat";

async function main() {
  const ProofChain = await ethers.getContractFactory("ProofChain");
  const proof = await ProofChain.deploy();
  await proof.deployed();

  const AuditRegistry = await ethers.getContractFactory("AuditRegistry");
  const reg = await AuditRegistry.deploy();
  await reg.deployed();

  const tx = await reg.setProofOfIntegrity(proof.address);
  await tx.wait();

  console.log(JSON.stringify({ poi: proof.address, registry: reg.address }));
}

main().catch((e) => { console.error(e); process.exit(1); });
