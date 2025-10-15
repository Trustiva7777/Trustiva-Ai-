require("@nomicfoundation/hardhat-ethers");

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.20",
  paths: {
    tests: "test",
    sources: "contracts",
    cache: "cache",
    artifacts: "artifacts",
  },
  networks: {
    localhost: {
      url: process.env.HARDHAT_RPC || "http://127.0.0.1:8545",
    },
  },
};
