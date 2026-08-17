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


class DocumentProcessingError(ApplicationError):
    def __init__(self, code: str, message: str, status_code: int = 422) -> None:
        super().__init__(code, message, status_code)


class MissingDocumentError(DocumentProcessingError):
    def __init__(self) -> None:
        super().__init__("DOCUMENT_REQUIRED", "A PDF document is required")


class UnsupportedDocumentTypeError(DocumentProcessingError):
    def __init__(self) -> None:
        super().__init__(
            "UNSUPPORTED_DOCUMENT_TYPE", "Only PDF documents are supported", 415
        )


class EmptyDocumentError(DocumentProcessingError):
    def __init__(self) -> None:
        super().__init__("EMPTY_DOCUMENT", "The uploaded PDF is empty")


class DocumentTooLargeError(DocumentProcessingError):
    def __init__(self, maximum_mb: int) -> None:
        super().__init__(
            "DOCUMENT_TOO_LARGE", f"PDF must not exceed {maximum_mb} MB", 413
        )


class InvalidPdfSignatureError(DocumentProcessingError):
    def __init__(self) -> None:
        super().__init__(
            "INVALID_PDF_SIGNATURE", "The uploaded file is not a valid PDF"
        )


class UnreadablePdfError(DocumentProcessingError):
    def __init__(self) -> None:
        super().__init__("UNREADABLE_PDF", "The PDF could not be read")


class EncryptedPdfError(DocumentProcessingError):
    def __init__(self) -> None:
        super().__init__("ENCRYPTED_PDF", "Password-protected PDFs are not supported")


class ExcessivePdfPagesError(DocumentProcessingError):
    def __init__(self, maximum_pages: int) -> None:
        super().__init__(
            "PDF_PAGE_LIMIT_EXCEEDED", f"PDF must not exceed {maximum_pages} pages"
        )


class NoExtractableTextError(DocumentProcessingError):
    def __init__(self) -> None:
        super().__init__(
            "NO_EXTRACTABLE_TEXT",
            "No readable text was found. Upload a text-based PDF or paste the "
            "complaint text.",
        )


class ExtractedTextTooLargeError(DocumentProcessingError):
    def __init__(self, maximum_characters: int) -> None:
        super().__init__(
            "EXTRACTED_TEXT_TOO_LARGE",
            f"Extracted PDF text must not exceed {maximum_characters} characters",
        )
