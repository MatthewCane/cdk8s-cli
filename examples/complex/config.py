from dataclasses import dataclass
from typing import Optional


@dataclass
class ApplicationConfig:
    replicas: Optional[int] = 1
