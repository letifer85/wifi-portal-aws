from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class UnifiAuthRequest:
    ap: str = "ap_mac"
    id: str = "client_mac"
    t: datetime = field(default_factory=datetime.utcnow)
    url: str = "http://origin_url.com"
    ssid: str = "ssid"