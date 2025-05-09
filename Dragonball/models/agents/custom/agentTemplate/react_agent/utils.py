"""Utility & helper functions."""

import json
from pathlib import Path
from typing import Dict, Any
import aiofiles

from langchain_core.messages import BaseMessage


def get_message_text(msg: BaseMessage) -> str:
    """Get the text content of a message."""
    content = msg.content
    if isinstance(content, str):
        return content
    elif isinstance(content, dict):
        return content.get("text", "")
    else:
        txts = [c if isinstance(c, str) else (c.get("text") or "") for c in content]
        return "".join(txts).strip()


def process_mcp_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    process the configuration.

    This function:
    1. For each server in mcpServers that doesn't already have a transport field:
       - Adds "transport": "stdio" if the command is "npx"
       - Adds "transport": "sse" otherwise

    Returns:
        Dict[str, Any]: The processed configuration dictionary

    Raises:
        json.JSONDecodeError: If input config is invalid JSON
    """
    try:
        # Process each server configuration
        if "mcpServers" in config:
            for server_name, server_config in config["mcpServers"].items():
                # Skip if transport is already defined
                if "transport" in server_config:
                    continue

                # Add the appropriate transport based on the command
                # command 파라미터가 없는 경우 무시하고 기본값으로 "sse" 사용
                if "command" in server_config and server_config["command"] == "npx":
                    server_config["transport"] = "stdio"
                else:
                    server_config["transport"] = "sse"

        return config
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON config", config)