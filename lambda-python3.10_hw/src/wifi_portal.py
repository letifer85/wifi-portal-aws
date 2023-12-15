from __future__ import annotations

import json
from functools import cached_property
from typing import Any, Callable, Mapping, Sequence

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext
from messaging import (Message, MessageService, WhatsAppAPIConfig,
                       WhatsAppMessageService)
from requests import Response


class WifiPortal:
    def handle_request(self, event: APIGatewayProxyEvent, context: LambdaContext):
        return self.dispatch_event(event, context)

    def root(self, event: APIGatewayProxyEvent, context: LambdaContext):
        try:
            with open("index.html", "r") as file:
                html_content = file.read()
        except Exception as e:
            print(f"Error reading HTML file: {e}")
            return {
                "statusCode": 500,
                "body": f"Internal Server Error\nException:\n{e}",
            }
        return {
            "headers": {"Content-Type": "text/html"},
            "body": html_content,
            "statusCode": 200,
        }

    def auth(self, event: APIGatewayProxyEvent, context: LambdaContext):
        provider = WhatsAppMessageService(WhatsAppAPIConfig.from_json_file("whatsapp_api_config.json"))
        message = Message(["420777938821"])
        return {
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": [r.json() for r in self.send_message(provider, message)]}),
            "statusCode": 200,
        }

    @cached_property
    def event_map(
        self,
    ) -> Mapping[str, Callable[[APIGatewayProxyEvent, LambdaContext], dict[Any]]]:
        return {
            "GET:/guest/s/default": self.auth,
            "GET:/": self.root,
        }

    def dispatch_event(
        self, event: APIGatewayProxyEvent, context: LambdaContext
    ) -> dict[str, Any]:
        return self.event_map.get(f"{event.http_method}:{event.path}", self.root)(
            event, context
        )

    def send_message(self, service_provider: MessageService, message: Message) -> Sequence[Response]:
        return service_provider.send(message)