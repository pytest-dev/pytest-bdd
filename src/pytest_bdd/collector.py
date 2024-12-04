"""Feature file collector functionality."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path

from .feature import get_feature
from .parser import Feature

logger = logging.getLogger(__name__)


def collect_features(base_path: str | Path) -> Iterator[Feature]:
    """Collect all feature files recursively from base_path.

    Args:
        base_path: Base directory to search for feature files

    Returns:
        Iterator of Feature objects
    """
    base_path = Path(base_path)

    if not base_path.exists():
        logger.warning(f"Features base directory does not exist: {base_path}")
        return

    for feature_file in base_path.rglob("*.feature"):
        try:
            feature = get_feature(
                base_path=str(base_path),
                filename=str(feature_file.relative_to(base_path)),
            )
            yield feature
        except Exception as e:
            logger.warning(f"Failed to parse feature file {feature_file}: {e}")
            continue
