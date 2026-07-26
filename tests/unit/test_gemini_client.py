"""Tests for gemini_client.embed_text — mocked HTTP responses, no
real API calls.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from diodati_debtors.services.external import gemini_client


def test_embed_text_returns_values_on_success():
    mock_response = MagicMock()
    mock_response.json.return_value = {"embedding": {"values": [0.1, 0.2, 0.3]}}
    mock_response.raise_for_status.return_value = None

    with patch("diodati_debtors.services.external.gemini_client.requests.post", return_value=mock_response):
        result = gemini_client.embed_text("Frankenstein by Mary Shelley")

    assert result == [0.1, 0.2, 0.3]


def test_embed_text_raises_value_error_on_missing_embedding():
    mock_response = MagicMock()
    mock_response.json.return_value = {"unexpected": "shape"}
    mock_response.raise_for_status.return_value = None

    with patch("diodati_debtors.services.external.gemini_client.requests.post", return_value=mock_response):
        with pytest.raises(ValueError):
            gemini_client.embed_text("Some text")


def test_embed_text_uses_correct_task_type_default():
    mock_response = MagicMock()
    mock_response.json.return_value = {"embedding": {"values": [0.5]}}
    mock_response.raise_for_status.return_value = None

    with patch(
        "diodati_debtors.services.external.gemini_client.requests.post", return_value=mock_response
    ) as mock_post:
        gemini_client.embed_text("Some text")

    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["json"]["task_type"] == "RETRIEVAL_DOCUMENT"