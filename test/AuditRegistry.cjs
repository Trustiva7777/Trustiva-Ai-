const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("AuditRegistry Finalization Gate", function () {
  it("reverts before finalize and succeeds after", async function () {
    const POI = await ethers.deployContract("ProofChain");
    await POI.waitForDeployment();

    const REGF = await ethers.getContractFactory("AuditRegistry");
    const REG = await REGF.deploy();
    await REG.waitForDeployment();

    const tx0 = await REG.setProofOfIntegrity(await POI.getAddress());
    await tx0.wait();

    const root = ethers.keccak256(ethers.toUtf8Bytes("bundle-test"));
    const CID = "QmDemoCID";

    let reverted = false;
    try {
      await REG.registerBundle(root, CID);
    } catch (e) {
      reverted = true;
    }
    expect(reverted).to.equal(true);

  const tx1 = await POI.finalize(root);
  await tx1.wait();

  const tx2 = await REG.registerBundle(root, CID);
  const receipt = await tx2.wait();
  // check at least one log exists
  expect(receipt.logs.length > 0).to.equal(true);
  });
});
