class ArcServiceError(Exception):
    """Base exception for ArcAgent Pay blockchain service errors."""


class ArcConnectionError(ArcServiceError):
    """Raised when Arc RPC is unavailable or the wrong chain is connected."""


class ArcConfigurationError(ArcServiceError):
    """Raised when local Arc or Agent configuration is invalid."""


class PaymentPolicyRejected(ArcServiceError):
    """Raised when the smart contract rejects a requested payment."""


class PaymentExecutionError(ArcServiceError):
    """Raised when an approved transaction fails to execute successfully."""