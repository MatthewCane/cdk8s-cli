from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ApplicationConfig:
    replicas: Optional[int] = 1


@dataclass
class RedisConfig:
    values: Optional[dict] = field(
        default_factory=lambda: {
            "auth": {
                "enabled": False,
            },
        }
    )
