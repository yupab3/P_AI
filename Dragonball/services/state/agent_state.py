import asyncio
import mesop as me
from subprocess import Popen
from dataclasses import field
from typing import Optional, Dict, Any

@me.stateclass
class AgentState:
  """Agents List State"""
  agent_dialog_open: bool = False
  agent_address: str = ""
  agent_name: str = ""
  agent_description: str = ""
  input_modes: list[str]
  output_modes: list[str]
  stream_supported: bool = False
  push_notifications_supported: bool = False
  error: str = ""
  agent_framework_type: str = ""
  tags: list[str]
  create_dialog_open: bool = False
  agent_model: str = ""
  system_message: str = ""
  api_key: str = ""
  port_forwards: Dict[str, int] = field(default_factory=dict)
  use_mcp: bool = False
  mcp_api_key: str = ""
  mcp_tool_config: Dict[str, Any] = field(default_factory=dict)