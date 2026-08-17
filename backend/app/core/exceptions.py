class ApplicationError(Exception):
    def __init__(self, code: str, message: str, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class InputProcessingError(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__("INVALID_COMPLAINT_TEXT", message, 422)


class MissingAIConfigurationError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("AI_NOT_CONFIGURED", "AI processing is not configured", 503)


class ProviderAuthenticationError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            "AI_AUTHENTICATION_FAILED", "AI provider authentication failed", 502
        )


class ProviderTimeoutError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("AI_TIMEOUT", "AI provider timed out", 504)


class ProviderRateLimitError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("AI_RATE_LIMITED", "AI provider rate limit reached", 429)


class MalformedProviderResponseError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            "AI_INVALID_RESPONSE", "AI provider returned an invalid response", 502
        )


class ProviderUnavailableError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("AI_UNAVAILABLE", "AI provider is unavailable", 503)
