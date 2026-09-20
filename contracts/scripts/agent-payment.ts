import { ethers } from "hardhat";

async function main() {
  const [owner] = await ethers.getSigners();

  const vaultAddress = process.env.ARC_AGENT_VAULT_ADDRESS;
  const agentPrivateKey = process.env.AGENT_PRIVATE_KEY;
  const usdcAddress = process.env.ARC_USDC_ADDRESS;

  if (!vaultAddress || !ethers.isAddress(vaultAddress)) {
    throw new Error("ARC_AGENT_VAULT_ADDRESS is missing or invalid");
  }

  if (!agentPrivateKey) {
    throw new Error("AGENT_PRIVATE_KEY is missing");
  }

  if (!usdcAddress || !ethers.isAddress(usdcAddress)) {
    throw new Error("ARC_USDC_ADDRESS is missing or invalid");
  }

  const agent = new ethers.Wallet(
    agentPrivateKey,
    ethers.provider
  );

  const vault = await ethers.getContractAt(
    "ArcAgentVault",
    vaultAddress,
    agent
  );

  const usdc = await ethers.getContractAt(
    [
      "function balanceOf(address account) view returns (uint256)"
    ],
    usdcAddress
  );

  console.log("Agent:", agent.address);
  console.log("Recipient:", owner.address);
  console.log("Vault:", vaultAddress);

  const vaultBefore = await usdc.balanceOf(vaultAddress);

  console.log(
    "Vault balance before:",
    ethers.formatUnits(vaultBefore, 6),
    "USDC"
  );

  console.log("");
  console.log("Attempting allowed payment: 1 USDC...");

  const paymentTx = await vault.executePayment(
    owner.address,
    1_000_000n
  );

  await paymentTx.wait();

  console.log("✅ 1 USDC payment SUCCESS");
  console.log(
    "Explorer:",
    `https://explorer.testnet.arc.io/tx/${paymentTx.hash}`
  );

  const vaultAfter = await usdc.balanceOf(vaultAddress);

  console.log(
    "Vault balance after:",
    ethers.formatUnits(vaultAfter, 6),
    "USDC"
  );

  console.log("");
  console.log("Attempting forbidden payment: 2.5 USDC...");

  try {
    const forbiddenTx = await vault.executePayment(
      owner.address,
      2_500_000n
    );

    await forbiddenTx.wait();

    console.log("❌ ERROR: forbidden payment unexpectedly succeeded");
  } catch (error: any) {
    console.log("✅ 2.5 USDC payment REJECTED");
    console.log("Reason: exceeds 2 USDC per-transaction limit");
  }

  console.log("");
  console.log("ArcAgent Pay policy enforcement test complete.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});