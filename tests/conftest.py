from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from doc_converter.core import DocumentConverter


def pytest_configure(config):
    # Ensure libreoffice is available before running doc tests.
    soffice = subprocess.run(["which", "libreoffice"], capture_output=True, text=True).stdout.strip()
    if not soffice:
        pytest.skip("LibreOffice is required for Word .doc conversion tests")


@pytest.fixture(scope="session")
def converter() -> DocumentConverter:
    return DocumentConverter()
