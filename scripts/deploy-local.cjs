const { ethers } = require("hardhat");

async function main() {
  const ProofChain = await ethers.getContractFactory("ProofChain");
  const proof = await ProofChain.deploy();
  await proof.waitForDeployment();

  const AuditRegistry = await ethers.getContractFactory("AuditRegistry");
  const reg = await AuditRegistry.deploy();
  await reg.waitForDeployment();

  const tx = await reg.setProofOfIntegrity(await proof.getAddress());
  await tx.wait();

  console.log(
    JSON.stringify({ poi: await proof.getAddress(), registry: await reg.getAddress() })
  );
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
