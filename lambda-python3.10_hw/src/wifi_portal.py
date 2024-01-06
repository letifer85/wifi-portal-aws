from __future__ import annotations

import json
import random
import string
from datetime import datetime
from functools import cached_property
from typing import Any, Callable, Mapping, Sequence

import boto3
from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext
from messaging import (CTAWhatsAppMessage, Message, MessageService,
                       WhatsAppAPIConfig, WhatsAppAuthMessage,
                       WhatsAppMessageService)
from requests import Response


class WifiPortal:
    def handle_request(self, event: APIGatewayProxyEvent, context: LambdaContext):
        return self.dispatch_event(event, context)

    def root(self, event: APIGatewayProxyEvent, context: LambdaContext):
        try:
            with open("html/auth_index.html", "r") as file:
                html_content = file.read()
        except Exception as e:
            print(f"Error reading HTML file: {e}")
            return {
                "statusCode": 500,
                "body": f"Internal Server Error\nException:\n{e}",
            }
        html_content = html_content.replace("<ap>", event.query_string_parameters.get("ap", "null"))
        html_content = html_content.replace("<id>", event.query_string_parameters.get("id", "null"))
        html_content = html_content.replace("<t>", datetime.utcnow().isoformat())
        html_content = html_content.replace("<url>", event.query_string_parameters.get("url", "null"))
        html_content = html_content.replace("<ssid>", event.query_string_parameters.get("ssid", "null"))
        return {
            "headers": {"Content-Type": "text/html"},
            "body": html_content,
            "statusCode": 200,
        }

    def generate_code(self, num_digits: int) -> str:
        characters = string.digits
        random_string = ''.join(random.choice(characters) for _ in range(num_digits))
        return random_string
    
    def auth(self, event: APIGatewayProxyEvent, context: LambdaContext):
        dynamo_client = boto3.resource("dynamodb", region_name='eu-central-1')
        client_table = dynamo_client.Table("ClientTable")
        
        code = self.generate_code(6)
        data = event.query_string_parameters | {"code": code}
        dynamo_response = client_table.put_item(Item=data)
        self.send_message(
            WhatsAppMessageService(WhatsAppAPIConfig.from_json_file("whatsapp_api_config.json")), 
            WhatsAppAuthMessage(event.query_string_parameters.get("phone_number"), code)
        )
        try:
            with open("html/auth_code_input.html", "r") as file:
                html_content = file.read()
        except Exception as e:
            print(f"Error reading HTML file: {e}")
            return {
                "statusCode": 500,
                "body": f"Internal Server Error\nException:\n{e}",
            }
        html_content = html_content.replace("<phone_number>", event.query_string_parameters.get("phone_number"))
        return {
            "headers": {"Content-Type": "text/html"},
            "body": html_content,
            "statusCode": 200,
        }

    def auth_callback(self, event: APIGatewayProxyEvent, context: LambdaContext):
        dynamo_client = boto3.resource("dynamodb", region_name='eu-central-1')
        client_table = dynamo_client.Table("ClientTable")
        dynamo_response = client_table.get_item(Key={"phone_number": event.query_string_parameters.get("phone_number")})
        print(dynamo_response)
        if dynamo_response["Item"]["code"] == event.query_string_parameters.get("code"):
            # TODO: authorize wifi client
            return {
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": "authorized"}),
                "statusCode": 200,
            }
        else:
            return {
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": {"db_code": dynamo_response["Item"]["code"], "sent_code": event.query_string_parameters.get("code")}}),
                "statusCode": 401,
            }


    def not_found(*args, **kwargs):
        return {
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Not Found"}),
            "statusCode": 404,
        }

    @cached_property
    def event_map(
        self,
    ) -> Mapping[str, Callable[[APIGatewayProxyEvent, LambdaContext], dict[Any]]]:
        return {
            "GET:/guest/s/default": self.root,
            "GET:/auth": self.auth,
            "GET:/auth/callback": self.auth_callback,
        }

    def dispatch_event(
        self, event: APIGatewayProxyEvent, context: LambdaContext
    ) -> dict[str, Any]:
        return self.event_map.get(f"{event.http_method}:{event.path}", self.not_found)(
            event, context
        )

    def send_message(self, service_provider: MessageService, message: Message) -> Response:
        return service_provider.send(message)