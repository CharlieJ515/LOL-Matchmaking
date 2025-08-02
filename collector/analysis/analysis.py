import json
from typing import Optional


def filter_logs(
    file_path: str,
    *,
    level: Optional[str] = None,
    event: Optional[str] = None,
    contains: Optional[dict] = None,
):
    """
    Filter structlog JSON logs.

    Args:
        file_path (str): Path to log file.
        level (str): Log level to filter by (e.g., "info", "debug").
        event (str): Event name to filter by.
        contains (dict): Dictionary of key-value pairs that must be present in the log.

    Yields:
        dict: Log entries matching filters.
    """
    with open(file_path) as f:
        for line in f:
            try:
                log = json.loads(line)
                if level and log.get("level") != level:
                    continue
                if event and log.get("event") != event:
                    continue
                if contains and not all(log.get(k) == v for k, v in contains.items()):
                    continue
                yield log
            except json.JSONDecodeError:
                continue


def get_platform_logs(log_file, platform):
    for log in filter_logs(log_file):
        if log.get("platform", "") != platform:
            continue

        yield log


log_file = "app.log"

# rate_limit_exceeded_servers = set()
# for log in filter_logs(log_file, level="critical"):
#     if log.get("platform", "")[:3] == "ph2" or log.get("platform", "")[:3] == "th2":
#         continue
#     if log.get("msg", "").startswith("Server side rate limit exceeded."):
#         rate_limit_exceeded_servers.add(log.get("platform", ""))
#     print(json.dumps(log, indent=2))
# print(rate_limit_exceeded_servers)

platform = "jp1.api.riotgames.com"
for log in get_platform_logs(log_file, platform):
    if log.get("msg", "").startswith(("Worker started", "Added Rate Limit")):
        continue
    print(json.dumps(log, indent=2))
