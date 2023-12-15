from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__file__)

from aws_lambda_powertools.utilities.data_classes import (APIGatewayProxyEvent,
                                                          event_source)
from aws_lambda_powertools.utilities.typing import LambdaContext
from wifi_portal import WifiPortal


@event_source(data_class=APIGatewayProxyEvent)
def root(event: APIGatewayProxyEvent, context: LambdaContext) -> dict[str, Any]:
    # logger.warning(event)
    portal = WifiPortal()
    return portal.handle_request(event, context)
