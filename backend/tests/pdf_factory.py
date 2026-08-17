from typing import cast

import pymupdf


def make_pdf(*page_texts: str) -> bytes:
    with pymupdf.open() as document:  # type: ignore[no-untyped-call]
        for text in page_texts:
            page = document.new_page()
            if text:
                page.insert_text((72, 72), text)
        return cast(bytes, document.tobytes())


def make_encrypted_pdf(text: str = "Confidential complaint") -> bytes:
    with pymupdf.open() as document:  # type: ignore[no-untyped-call]
        page = document.new_page()
        page.insert_text((72, 72), text)
        return cast(
            bytes,
            document.tobytes(
                encryption=pymupdf.PDF_ENCRYPT_AES_256,  # type: ignore[attr-defined]
                owner_pw="owner-password",
                user_pw="user-password",
            ),
        )
