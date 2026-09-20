// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/// @title ArcAgentVault
/// @notice Holds USDC and lets one authorised agent make payments subject to
///         owner-defined limits that are enforced on-chain.
contract ArcAgentVault is Ownable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    error ZeroAddress();
    error ZeroAmount();
    error VaultPaused();
    error NotAgent();
    error PolicyExpired();
    error RecipientNotAllowed();
    error PerTransactionLimitExceeded();
    error DailyLimitExceeded();

    IERC20 public immutable usdc;

    address public agent;
    uint256 public perTransactionLimit;
    uint256 public dailyLimit;
    uint256 public policyExpiresAt;

    bool public allowlistEnabled = true;
    bool public paused = true;

    mapping(address => bool) public allowedRecipients;
    mapping(uint256 => uint256) public spentByDay;

    event AgentUpdated(address indexed agent);
    event LimitsUpdated(uint256 perTransactionLimit, uint256 dailyLimit);
    event PolicyExpiryUpdated(uint256 policyExpiresAt);
    event AllowlistModeUpdated(bool enabled);
    event RecipientUpdated(address indexed recipient, bool allowed);
    event PauseUpdated(bool paused);
    event Deposited(address indexed from, uint256 amount);
    event PaymentExecuted(
        address indexed agent,
        address indexed recipient,
        uint256 amount,
        uint256 indexed day
    );
    event EmergencyWithdrawal(address indexed recipient, uint256 amount);

    modifier onlyAgent() {
        if (msg.sender != agent) revert NotAgent();
        _;
    }

    constructor(
        address usdcAddress,
        address initialAgent,
        uint256 initialPerTransactionLimit,
        uint256 initialDailyLimit,
        uint256 initialPolicyExpiresAt
    ) Ownable(msg.sender) {
        if (usdcAddress == address(0) || initialAgent == address(0)) {
            revert ZeroAddress();
        }
        if (
            initialPerTransactionLimit == 0 ||
            initialDailyLimit == 0 ||
            initialPerTransactionLimit > initialDailyLimit
        ) {
            revert DailyLimitExceeded();
        }

        usdc = IERC20(usdcAddress);
        agent = initialAgent;
        perTransactionLimit = initialPerTransactionLimit;
        dailyLimit = initialDailyLimit;
        policyExpiresAt = initialPolicyExpiresAt;
    }

    function currentDay() public view returns (uint256) {
        return block.timestamp / 1 days;
    }

    function dailySpent() public view returns (uint256) {
        return spentByDay[currentDay()];
    }

    function remainingDailyLimit() public view returns (uint256) {
        uint256 spent = dailySpent();
        if (spent >= dailyLimit) return 0;
        return dailyLimit - spent;
    }

    function deposit(uint256 amount) external nonReentrant {
        if (amount == 0) revert ZeroAmount();
        usdc.safeTransferFrom(msg.sender, address(this), amount);
        emit Deposited(msg.sender, amount);
    }

    function executePayment(
        address recipient,
        uint256 amount
    ) external onlyAgent nonReentrant {
        _validatePayment(recipient, amount);

        uint256 day = currentDay();
        spentByDay[day] += amount;

        usdc.safeTransfer(recipient, amount);

        emit PaymentExecuted(msg.sender, recipient, amount, day);
    }

    function validatePayment(
        address recipient,
        uint256 amount
    ) external view returns (bool) {
        _validatePayment(recipient, amount);
        return true;
    }

    function _validatePayment(address recipient, uint256 amount) internal view {
        if (paused) revert VaultPaused();
        if (recipient == address(0)) revert ZeroAddress();
        if (amount == 0) revert ZeroAmount();

        if (policyExpiresAt != 0 && block.timestamp > policyExpiresAt) {
            revert PolicyExpired();
        }

        if (allowlistEnabled && !allowedRecipients[recipient]) {
            revert RecipientNotAllowed();
        }

        if (amount > perTransactionLimit) {
            revert PerTransactionLimitExceeded();
        }

        if (spentByDay[currentDay()] + amount > dailyLimit) {
            revert DailyLimitExceeded();
        }
    }

    function setAgent(address newAgent) external onlyOwner {
        if (newAgent == address(0)) revert ZeroAddress();
        agent = newAgent;
        emit AgentUpdated(newAgent);
    }

    function setLimits(
        uint256 newPerTransactionLimit,
        uint256 newDailyLimit
    ) external onlyOwner {
        if (
            newPerTransactionLimit == 0 ||
            newDailyLimit == 0 ||
            newPerTransactionLimit > newDailyLimit
        ) {
            revert DailyLimitExceeded();
        }

        perTransactionLimit = newPerTransactionLimit;
        dailyLimit = newDailyLimit;

        emit LimitsUpdated(newPerTransactionLimit, newDailyLimit);
    }

    function setPolicyExpiresAt(uint256 timestamp) external onlyOwner {
        policyExpiresAt = timestamp;
        emit PolicyExpiryUpdated(timestamp);
    }

    function setAllowlistEnabled(bool enabled) external onlyOwner {
        allowlistEnabled = enabled;
        emit AllowlistModeUpdated(enabled);
    }

    function setRecipient(address recipient, bool allowed) external onlyOwner {
        if (recipient == address(0)) revert ZeroAddress();
        allowedRecipients[recipient] = allowed;
        emit RecipientUpdated(recipient, allowed);
    }

    function setPaused(bool value) external onlyOwner {
        paused = value;
        emit PauseUpdated(value);
    }

    function emergencyWithdraw(
        address recipient,
        uint256 amount
    ) external onlyOwner nonReentrant {
        if (recipient == address(0)) revert ZeroAddress();
        if (amount == 0) revert ZeroAmount();

        usdc.safeTransfer(recipient, amount);
        emit EmergencyWithdrawal(recipient, amount);
    }
}
