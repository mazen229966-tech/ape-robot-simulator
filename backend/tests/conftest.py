"""Shared fixtures for the backend test-suite."""

from __future__ import annotations

import numpy as np
import pytest

from app.models.parameters import parameter_store


@pytest.fixture(autouse=True)
def restore_default_parameters():
    """Every test runs against the default educational parameter set."""
    parameter_store.reset()
    yield
    parameter_store.reset()


@pytest.fixture
def rng():
    return np.random.default_rng(12345)
