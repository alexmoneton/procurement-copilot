"""Connector registry for TenderPulse."""

import os
from typing import Dict, List, Optional, Tuple

from loguru import logger

from .base import Connector
from .ted_connector import ted_connector

# Import other connectors when ready
# from .boamp_fr import boamp_connector
# from .european_platforms import german_connector, italian_connector


# Registry of all available connectors
ALL_CONNECTORS: Dict[str, Connector] = {
    "TED": ted_connector,
    # "BOAMP_FR": boamp_connector,  # Ready but disabled
    # "GERMANY": german_connector,   # Ready but disabled
    # "ITALY": italian_connector,    # Ready but disabled
    # "SPAIN": spanish_connector,    # Ready but disabled
    # "NETHERLANDS": dutch_connector, # Ready but disabled
}


def resolve_enabled() -> Tuple[List[Connector], List[Connector]]:
    """Resolve enabled and shadow connectors from environment."""
    enabled_names = os.getenv("ENABLE_CONNECTORS", "TED").split(",")
    shadow_names = os.getenv("SHADOW_CONNECTORS", "").split(",")

    # Clean up empty strings
    enabled_names = [name.strip() for name in enabled_names if name.strip()]
    shadow_names = [name.strip() for name in shadow_names if name.strip()]

    enabled_connectors = []
    shadow_connectors = []

    for name in enabled_names:
        if name in ALL_CONNECTORS:
            enabled_connectors.append(ALL_CONNECTORS[name])
            logger.info(f"✅ Enabled connector: {name}")
        else:
            logger.warning(f"❌ Unknown connector in ENABLE_CONNECTORS: {name}")

    for name in shadow_names:
        if name in ALL_CONNECTORS:
            shadow_connectors.append(ALL_CONNECTORS[name])
            logger.info(f"👻 Shadow connector: {name}")
        else:
            logger.warning(f"❌ Unknown connector in SHADOW_CONNECTORS: {name}")

    logger.info(
        f"Resolved {len(enabled_connectors)} enabled, {len(shadow_connectors)} shadow connectors"
    )
    return enabled_connectors, shadow_connectors


def enabled_source_names() -> List[str]:
    """Get list of enabled source names."""
    enabled_connectors, _ = resolve_enabled()
    return [connector.source for connector in enabled_connectors]


def shadow_source_names() -> List[str]:
    """Get list of shadow source names."""
    _, shadow_connectors = resolve_enabled()
    return [connector.source for connector in shadow_connectors]


def get_connector_by_source(source: str) -> Optional[Connector]:
    """Get connector by source name."""
    for connector in ALL_CONNECTORS.values():
        if connector.source == source:
            return connector
    return None
