import { ethers } from "hardhat";

async function main() {
  const [deployer] = await ethers.getSigners();

  const agentAddress = process.env.AGENT_ADDRESS;
  const usdcAddress = process.env.ARC_USDC_ADDRESS;

  if (!agentAddress) {
    throw new Error("AGENT_ADDRESS is missing from .env");
  }

  if (!usdcAddress) {
    throw new Error("ARC_USDC_ADDRESS is missing from .env");
  }

  console.log("Deploying ArcAgentVault...");
  console.log("Owner:", deployer.address);
  console.log("Agent:", agentAddress);
  console.log("USDC:", usdcAddress);

  const perTransactionLimit = 2_000_000n; // 2 USDC
  const dailyLimit = 5_000_000n;          // 5 USDC
  const policyExpiresAt = 0;               // no expiry for now

  const Vault = await ethers.getContractFactory("ArcAgentVault");

  const vault = await Vault.deploy(
    usdcAddress,
    agentAddress,
    perTransactionLimit,
    dailyLimit,
    policyExpiresAt
  );

  await vault.waitForDeployment();

  const vaultAddress = await vault.getAddress();

  console.log("");
  console.log("ArcAgentVault deployed!");
  console.log("Contract address:", vaultAddress);
  console.log("Per transaction limit: 2 USDC");
  console.log("Daily limit: 5 USDC");
  console.log("Initial state: PAUSED");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});