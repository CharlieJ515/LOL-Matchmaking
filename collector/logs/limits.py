from datetime import datetime

import structlog
import httpx
from riot_api import RateLimitClient

from execution.query_job import QueryJob


def limit_str(rate, period, count):
    return f"{count}({rate})/{period}"


def log_header_limits(logger: structlog.BoundLogger, headers: httpx.Headers):
    def parse_limit_string(s: str):
        try:
            return [tuple(map(int, part.split(":"))) for part in s.split(",") if part]
        except Exception:
            return []

    route_limit = parse_limit_string(headers.get("X-App-Rate-Limit", ""))
    route_count = parse_limit_string(headers.get("X-App-Rate-Limit-Count", ""))
    endpoint_limit = parse_limit_string(headers.get("X-Method-Rate-Limit", ""))
    endpoint_count = parse_limit_string(headers.get("X-Method-Rate-Limit-Count", ""))

    log_data = {}
    log_data["route_long"] = limit_str(
        route_limit[0][0], route_limit[0][1], route_count[0][0]
    )
    log_data["route_short"] = limit_str(
        route_limit[1][0], route_limit[1][1], route_count[1][0]
    )
    log_data["endpoint"] = limit_str(
        endpoint_limit[0][0], endpoint_limit[0][1], endpoint_count[0][0]
    )

    # time of server when response was sent
    date_str = headers["date"]
    dt = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S GMT")
    response_time = dt.strftime("%Y-%m-%d %H:%M.%S")

    logger.debug(
        "Riot server rate limit status", response_time=response_time, **log_data
    )


async def log_client_limits(
    logger: structlog.BoundLogger, client: RateLimitClient, query_job: QueryJob
):
    route = query_job.params.get("region") or query_job.params.get("platform")
    if route is None:
        raise ValueError
    route_name = route.name

    # Endpoint window
    keys = (route_name, query_job.method_name)
    endpoint_limit = client.limits[keys]
    endpoint_window = await client.limiter.get_window_stats(endpoint_limit, *keys)
    endpoint_limit_str = limit_str(
        endpoint_limit.amount,
        endpoint_limit.multiples,
        endpoint_limit.amount - endpoint_window.remaining,
    )

    # Route long window
    keys = (route_name, "route_long")
    route_long_limit = client.limits[keys]
    route_long_window = await client.limiter.get_window_stats(route_long_limit, *keys)
    route_long_limit_str = limit_str(
        route_long_limit.amount,
        route_long_limit.multiples,
        route_long_limit.amount - route_long_window.remaining,
    )

    # Route short window
    keys = (route_name, "route_short")
    route_short_limit = client.limits[keys]
    route_short_window = await client.limiter.get_window_stats(route_short_limit, *keys)
    route_short_limit_str = limit_str(
        route_short_limit.amount,
        route_short_limit.multiples,
        route_short_limit.amount - route_short_window.remaining,
    )

    # logging
    logger.debug(
        "Client rate limit status",
        endpoint=endpoint_limit_str,
        route_long=route_long_limit_str,
        route_short=route_short_limit_str,
    )
