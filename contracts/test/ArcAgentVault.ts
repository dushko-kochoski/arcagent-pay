import { expect } from "chai";
import { ethers } from "hardhat";

describe("ArcAgentVault", function () {
  async function deployFixture() {
    const [owner, agent, recipient, stranger] = await ethers.getSigners();

    const USDC = await ethers.getContractFactory("MockUSDC");
    const usdc = await USDC.deploy();

    const oneUSDC = 1_000_000n;
    const Vault = await ethers.getContractFactory("ArcAgentVault");
    const vault = await Vault.deploy(
      await usdc.getAddress(),
      agent.address,
      100n * oneUSDC,
      250n * oneUSDC,
      0
    );

    await usdc.mint(owner.address, 1_000n * oneUSDC);
    await usdc.approve(await vault.getAddress(), 500n * oneUSDC);
    await vault.deposit(500n * oneUSDC);

    await vault.setRecipient(recipient.address, true);
    await vault.setPaused(false);

    return { owner, agent, recipient, stranger, usdc, vault, oneUSDC };
  }

  it("allows the authorised agent to pay an allowlisted recipient", async function () {
    const { agent, recipient, usdc, vault, oneUSDC } = await deployFixture();

    await expect(
      vault.connect(agent).executePayment(recipient.address, 25n * oneUSDC)
    ).to.emit(vault, "PaymentExecuted");

    expect(await usdc.balanceOf(recipient.address)).to.equal(25n * oneUSDC);
  });

  it("rejects a non-agent", async function () {
    const { stranger, recipient, vault, oneUSDC } = await deployFixture();

    await expect(
      vault.connect(stranger).executePayment(recipient.address, 5n * oneUSDC)
    ).to.be.revertedWithCustomError(vault, "NotAgent");
  });

  it("rejects a recipient that is not allowlisted", async function () {
    const { agent, stranger, vault, oneUSDC } = await deployFixture();

    await expect(
      vault.connect(agent).executePayment(stranger.address, 5n * oneUSDC)
    ).to.be.revertedWithCustomError(vault, "RecipientNotAllowed");
  });

  it("enforces the per-transaction limit", async function () {
    const { agent, recipient, vault, oneUSDC } = await deployFixture();

    await expect(
      vault.connect(agent).executePayment(recipient.address, 101n * oneUSDC)
    ).to.be.revertedWithCustomError(vault, "PerTransactionLimitExceeded");
  });

  it("enforces the daily limit", async function () {
    const { agent, recipient, vault, oneUSDC } = await deployFixture();

    await vault.connect(agent).executePayment(recipient.address, 100n * oneUSDC);
    await vault.connect(agent).executePayment(recipient.address, 100n * oneUSDC);

    await expect(
      vault.connect(agent).executePayment(recipient.address, 51n * oneUSDC)
    ).to.be.revertedWithCustomError(vault, "DailyLimitExceeded");
  });

  it("can be paused by the owner", async function () {
    const { owner, agent, recipient, vault, oneUSDC } = await deployFixture();

    await vault.connect(owner).setPaused(true);

    await expect(
      vault.connect(agent).executePayment(recipient.address, 1n * oneUSDC)
    ).to.be.revertedWithCustomError(vault, "VaultPaused");
  });
});
