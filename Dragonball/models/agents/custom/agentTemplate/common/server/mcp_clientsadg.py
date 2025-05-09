# mixed_servers_mcp_sync.py
import threading
import asyncio
import os
from queue import Queue, Empty
from typing import Dict, Any

from . import mcp_utilsaewrha
from langchain_mcp_adapters.client import MultiServerMCPClient

_notified = False  # 알림 여부 플래그

async def run_mcp_client(ready_event: asyncio.Event, ready_queue: Queue, config: Dict[str, Any]):
    global _notified
    mcp_tools = {}
    # 1) 설정 JSON 로드
    if config:
        cfg = mcp_utilsaewrha.process_mcp_config(config)
        mcp_tools = cfg.get("mcpServers", {})
        print(f"✅ Loaded MCP tools from {config}")
    else:
        print(f"⚠️ Warning: MCP config not found at {config}")
        # 에러 상황도 큐에 None 을 보내서 메인 스레드가 알 수 있게
        ready_queue.put(None)
        return

    # 2) 비동기 컨텍스트 매니저 진입
    async with MultiServerMCPClient(mcp_tools) as client:
        # 첫 실행 시에만 큐에 담고, 이후엔 무시
        if not _notified:
            tools = client.get_tools()
            ready_queue.put(tools)
            _notified = True
        print("🚀 MCP client is running; tools ready →", tools)

        # (필요하면 실제 invoke loop 등 수행)
        await asyncio.Event().wait()

# ─── 사용 예 ───
if __name__ == "__main__":
    tool_list = start_mcp_client_thread()
    print("✔️ 최종 tool_list:", tool_list)
    
    # 이후에 tool_list를 가지고 에이전트 초기화 등 진행
