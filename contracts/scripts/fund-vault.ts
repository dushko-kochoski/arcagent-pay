import { ethers } from "hardhat";

async function main() {
  const [owner] = await ethers.getSigners();

  const vaultAddress = process.env.ARC_AGENT_VAULT_ADDRESS;
  const usdcAddress = process.env.ARC_USDC_ADDRESS;

  if (!vaultAddress || !ethers.isAddress(vaultAddress)) {
    throw new Error("ARC_AGENT_VAULT_ADDRESS is missing or invalid");
  }

  if (!usdcAddress || !ethers.isAddress(usdcAddress)) {
    throw new Error("ARC_USDC_ADDRESS is missing or invalid");
  }

  const amount = 3_000_000n; // 3 USDC - ERC20 interface uses 6 decimals

  const usdc = await ethers.getContractAt(
    [
      "function approve(address spender, uint256 amount) returns (bool)",
      "function balanceOf(address account) view returns (uint256)",
    ],
    usdcAddress
  );

  const vault = await ethers.getContractAt(
    "ArcAgentVault",
    vaultAddress
  );

  const ownerBalanceBefore = await usdc.balanceOf(owner.address);

  console.log("Owner:", owner.address);
  console.log("Vault:", vaultAddress);
  console.log(
    "Owner ERC20 USDC balance:",
    ethers.formatUnits(ownerBalanceBefore, 6)
  );

  console.log("");
  console.log("Approving vault for 3 USDC...");

  const approveTx = await usdc.approve(vaultAddress, amount);
  await approveTx.wait();

  console.log("Approval confirmed.");

  console.log("Depositing 3 USDC into vault...");

  const depositTx = await vault.deposit(amount);
  await depositTx.wait();

  const vaultBalance = await usdc.balanceOf(vaultAddress);

  console.log("");
  console.log("Deposit successful!");
  console.log(
    "Vault USDC balance:",
    ethers.formatUnits(vaultBalance, 6)
  );
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});