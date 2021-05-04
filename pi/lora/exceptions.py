class SerialConnectionException(ConnectionError):
    """Exception raised when encountering an error with the RN2483 serial connection"""
    def __init__(self, message: str = "RN2483 module is not responding."):
        super().__init__(message)
        self.message = message


class LoraTxTimeoutException(ConnectionError):
    """Exception raised when LoRa transmission fails due to not receiving an ACK after too many attempts."""
    def __init__(self, tries: int):
        self.message = f"LoRa transmission failed: {tries} transmissions without any response."
        super().__init__(self.message)


class LoraRxTimeoutException(ConnectionError):
    """Exception raised when LoRa reception fails due to waiting longer than timeout."""
    def __init__(self, timeout_ms: int):
        self.message = f"LoRa reception failed: Nothing received in {timeout_ms} ms."
        super().__init__(self.message)


class LoraRxRadioException(ConnectionError):
    """Exception raised when LoRa receives, but radio indicated a reception error."""
    def __init__(self):
        self.message = "LoRa reception failed: error in received data."
        super().__init__(self.message)
