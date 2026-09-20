import { ethers } from "hardhat";

async function main() {
  const [owner] = await ethers.getSigners();

  const vaultAddress = process.env.ARC_AGENT_VAULT_ADDRESS;

  if (!vaultAddress || !ethers.isAddress(vaultAddress)) {
    throw new Error("ARC_AGENT_VAULT_ADDRESS is missing or invalid");
  }

  const vault = await ethers.getContractAt(
    "ArcAgentVault",
    vaultAddress
  );

  console.log("Vault:", vaultAddress);
  console.log("Owner:", owner.address);

  console.log("");
  console.log("Allowlisting Owner as demo recipient...");

  const allowTx = await vault.setRecipient(owner.address, true);
  await allowTx.wait();

  console.log("Recipient allowlisted.");
  console.log(
    "Explorer:",
    `https://explorer.testnet.arc.io/tx/${allowTx.hash}`
  );

  console.log("");
  console.log("Unpausing vault...");

  const unpauseTx = await vault.setPaused(false);
  await unpauseTx.wait();

  console.log("Vault is now ACTIVE.");
  console.log(
    "Explorer:",
    `https://explorer.testnet.arc.io/tx/${unpauseTx.hash}`
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});