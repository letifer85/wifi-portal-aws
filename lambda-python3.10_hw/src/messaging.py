from __future__ import annotations

import json
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Iterator, Optional, Protocol, TypedDict

import requests


class TemplateType(TypedDict):
    name: str
    language: dict[str, str]


class WhatsAppMessageRequestBody(TypedDict):
    messaging_product: str
    to: str
    type: str
    template: TemplateType

class Message(Protocol):
    @cached_property
    def payload(self) -> dict[str, Any]:
        ...

@dataclass(frozen=True)
class WhatsAppAuthMessage:
    recipient: str
    verification_code: str
    template_name: str = "test_auth"
    template_locale: str = "en_US"
        
    @cached_property
    def payload(self) -> dict[str, Any]:
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": f"+{self.recipient.strip('+')}",
            "type": "template",
            "template": {
                "name": self.template_name,
                "language": {
                "code": self.template_locale
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                    {
                        "type": "text",
                        "text": self.verification_code
                    }
                    ]
                },
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": "0",
                    "parameters": [
                    {
                        "type": "text",
                        "text": self.verification_code
                    }
                    ]
                }
                ]
            }
        }
        

@dataclass
class CTAWhatsAppMessage:
    
    recipient: str
    place_name: str
    
    @cached_property
    def payload(self) -> dict[str, Any]:
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": f"+{self.recipient.strip('+')}",
            "type": "interactive",
            "interactive": {
                "type": "cta_url",

                "header": {
                    "type": "text",
                    "text": f"Welcome To {self.place_name}"
                },

                "body": {
                    "text": "To get wifi access please join the group."
                },

                "footer": {
                    "text": "<FOOTER_TEXT>"
                },
                "action": {
                    "name": "cta_url",
                    "parameters": {
                        "display_text": "Google",
                        "url": "google.com"
                    }
                }
            }
        }
    


class MessageService(Protocol):
    def send(self, message: Message) -> requests.Response:
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
        return requests.post(
            url=self.config.url,
            headers=self.headers,
            json=message.payload
        )

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.access_token}",
            "Content-Type": "application/json",
        }

