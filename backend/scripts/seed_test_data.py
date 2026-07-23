# backend/scripts/seed_test_data.py
"""Seed CI / local test database — extend when integration tests need fixtures."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger.info("seed_test_data: no fixtures yet (tests/unit/ uses mocks)")


if __name__ == "__main__":
    main()
