from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import cached_property
from typing import Iterator, Optional, Protocol, Sequence, TypedDict

import requests


class TemplateType(TypedDict):
    name: str
    language: dict[str, str]


class WhatsAppMessageRequestBody(TypedDict):
    messaging_product: str
    to: str
    type: str
    template: TemplateType


@dataclass(frozen=True)
class Message:
    recipients: Sequence[str]
    content: Optional[str] = None
    message_type: str = "template"
    messaging_product: str = "whatsapp"
    template_name: str = "hello_world"
    template_locale: str = "en_US"

    def __post_init__(self) -> None:
        if self.content is None and self.message_type != "template":
            raise ValueError(f"content can not be None for non template message types.")


class MessageService(Protocol):
    def send(self, message: Message) -> Iterator[requests.Response]:
        ...


@dataclass(frozen=True)
class WhatsAppAPIConfig:
    business_id: str
    whatsapp_business_id: str
    phone_number_id: str
    access_token: str
    version: str
    api_url: str

    @cached_property
    def url(self) -> str:
        api_url = self.api_url.strip("/")
        return f"{api_url}/{self.version}/{self.phone_number_id}/messages"

        
    @classmethod
    def from_json_file(cls, path: str) -> WhatsAppAPIConfig:
        with open(path, "r") as fn:
            config = json.load(fn)

        return cls(**config)

class WhatsAppMessageService:
    def __init__(self, config: WhatsAppAPIConfig) -> None:
        self.config = config


    def send(self, message: Message) -> Iterator[requests.Response]:
        return (requests.post(
            url=self.config.url,
            headers=self.headers,
            json=body
        )for body in self.generate_message_request_bodies(message))

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.access_token}",
            "Content-Type": "application/json",
        }

    def generate_message_request_bodies(
        self, message: Message
    ) -> Iterator[WhatsAppMessageRequestBody]:
        return (
            {
                "messaging_product": message.messaging_product,
                "to": number,
                "type": message.message_type,
                "template": {
                    "name": message.template_name,
                    "language": {"code": message.template_locale},
                },
            }
            for number in message.recipients
        )
