import { ethers } from "hardhat";

async function main() {
  const [deployer] = await ethers.getSigners();

  const network = await ethers.provider.getNetwork();
  const balance = await ethers.provider.getBalance(deployer.address);

  console.log("Connected chain ID:", network.chainId.toString());
  console.log("Deployer address:", deployer.address);
  console.log("Native USDC balance:", ethers.formatEther(balance));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});