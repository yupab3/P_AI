import stat
import yaml
import tempfile
import aiohttp
import time
import asyncio
import socket
import mesop as me
import subprocess
from pathlib import Path
from asyncio import base_subprocess, base_events
from components.agent_list import agents_list
from components.dialog import dialog, dialog_actions
from components.header import header
from components.page_scaffold import page_frame
from components.page_scaffold import page_scaffold
from state.agent_state import AgentState
from state.host_agent_service import ListRemoteAgents, AddRemoteAgent
from state.state import AppState
from utils.agent_card import get_agent_card
from common.types import JSONRPCError
from kubernetes import client, config
from kubernetes.client.rest import ApiException


# monkey-patch: 내부 __del__ 가 _closed를 참조할 때 에러 안 나도록 미리 붙여줌
base_subprocess.BaseSubprocessTransport._closed = True
base_events.BaseEventLoop._closed = True

def agent_list_page(app_state: AppState):
    """Agents List Page"""
    state = me.state(AgentState)
    with page_scaffold():
        with page_frame():
            with header("Remote Agents", "smart_toy"):
                me.button("Create Agent", on_click=open_create_dialog)

            agents = asyncio.run(ListRemoteAgents())
            agents_list(agents)

            with dialog(state.agent_dialog_open):
              with me.box(
                  style=me.Style(display="flex", flex_direction="column", gap=12)
              ):
                me.text("🤖 새로운 에이전트 등록", style=me.Style(font_size="18px", font_weight="bold"))
                me.input(
                    label="Agent Address",
                    on_blur=set_agent_address,
                    placeholder="localhost:10000",
                )

                if state.error != "":
                  me.text(state.error, style=me.Style(color="red"))
                if state.agent_name != "":
                  me.text(f"Agent Name: {state.agent_name}")
                if state.agent_description:
                  me.text(f"Agent Description: {state.agent_description}")
                if state.agent_model:
                  me.text(f"Agent Model: {state.agent_model}")
                if state.system_message:
                  me.text(f"System Message: {state.system_message}")

              with dialog_actions():
                if not state.agent_name:
                  me.button("Read", on_click=load_agent_info)
                elif not state.error:
                  me.button("Save", on_click=save_agent)
                me.button("Cancel", on_click=cancel_register_dialog)
            create_agent_dialog()


# -------------------- REGISTER DIALOG --------------------


def cancel_register_dialog(e: me.ClickEvent):
    state = me.state(AgentState)
    state.agent_dialog_open = False
    clear_class()

def set_agent_address(e: me.InputBlurEvent):
    state = me.state(AgentState)
    state.agent_address = e.value


def load_agent_info(e: me.ClickEvent):
    state = me.state(AgentState)
    try:
        state.error = None
        agent_card = get_agent_card(state.agent_address)
        state.agent_name = agent_card.name
        state.agent_description = agent_card.description
        state.agent_model = agent_card.model
        state.system_message = (
            agent_card.systemMessage[:100] + "..."
            if agent_card.systemMessage and len(agent_card.systemMessage) > 100
            else agent_card.systemMessage or ""
        )
        state.stream_supported = agent_card.capabilities.streaming
        state.push_notifications_supported = agent_card.capabilities.pushNotifications
    except Exception as e:
        print(e)
        state.agent_name = None
        state.error = f"Cannot connect to agent at {state.agent_address}"


# -------------------- CREATE DIALOG --------------------

def open_create_dialog(e: me.ClickEvent):
    state = me.state(AgentState)
    state.create_dialog_open = True
    state.agent_dialog_open = False
    # 수동 입력용 초기화
    clear_class()


def cancel_create_dialog(e: me.ClickEvent):
    state = me.state(AgentState)
    state.create_dialog_open = False
    clear_class()

def create_agent_dialog():
    state = me.state(AgentState)

    dialog_style = me.Style(
        width="600px",
        margin=me.Margin.symmetric(horizontal="auto"),
        padding=me.Padding.all(20),
        display="flex",
        flex_direction="column",
        gap=12
    )

    async def handle_save_click(e):
        missing = []
        if not state.agent_name:
            missing.append("Agent Name")
        if not state.agent_description:
            missing.append("Description")
        if not state.agent_model:
            missing.append("Model Name")
        if not state.system_message:
            missing.append("System Message")
        if not state.api_key:
            missing.append("API KEY")
        if state.use_mcp and not state.mcp_api_key:
            missing.append("MCP API KEY")
        if not state.tags:
            missing.append("Tags")

        if missing:
            return

        await save_created_agent(e)

    with dialog(state.create_dialog_open):
        with me.box(style=dialog_style):
            me.text("🔧 새로운 에이전트 생성", style=me.Style(font_size="18px", font_weight="bold"))

            # 그룹화: 왼쪽 컬럼과 오른쪽 컬럼
            with me.box(style=me.Style(display="flex", gap=12)):
                # 왼쪽 입력 필드
                with me.box(
                    style=me.Style(
                        display="flex",
                        flex_direction="column",
                        gap=12
                    )
                ):
                    me.input(
                        label="Agent Name",
                        value=state.agent_name or "",
                        style=me.Style(width="120%"),
                        on_blur=lambda e: setattr(state, "agent_name", e.value)
                    )
                    me.input(
                        label="Description",
                        value=state.agent_description or "",
                        style=me.Style(width="120%"),
                        on_blur=lambda e: setattr(state, "agent_description", e.value)
                    )
                    me.input(
                        label="System Message",
                        value=state.system_message or "",
                        style=me.Style(width="120%"),
                        on_blur=lambda e: setattr(state, "system_message", e.value)
                    )
                    me.input(
                        label="Tags",
                        value=",".join(state.tags) if state.tags else "",
                        style=me.Style(width="120%"),
                        on_blur=lambda e: setattr(
                            state,
                            "tags",
                            [s.strip() for s in e.value.split(",") if s.strip()]
                        )
                    )

            # 오른쪽 입력 필드 (오른쪽 정렬)
                with me.box(
                    style=me.Style(
                        display="flex",
                        flex_direction="column",
                        gap=12,
                        margin=me.Margin(left="80px")
                    )
                ):
                    me.select(
                        label="Model Name",
                        value=state.agent_model or "",
                        options=[
                            {"label": "GPT-3.5 Turbo", "value": "gpt-3.5-turbo"},
                            {"label": "GPT-4o", "value": "gpt-4o"},
                            {"label": "Gemini 2.5 Pro", "value": "gemini-2.5-pro-preview-03-25"},
                            {"label": "Gemini 2.5 Flash", "value": "gemini-2.5-flash-preview-04-17"}
                        ],
                        style=me.Style(width="120%"),
                        on_selection_change=lambda e: setattr(state, "agent_model", e.value)
                    )

                    # 일반 API KEY
                    me.input(
                        label="API KEY",
                        value=state.api_key or "",
                        style=me.Style(width="120%"),
                        on_blur=lambda e: setattr(state, "api_key", e.value)
                    )

                    # MCP USE 체크박스
                    me.checkbox(
                        label="MCP USE",
                        checked=state.use_mcp or False,
                        on_change=lambda e: setattr(state, "use_mcp", e.checked)
                    )

                    # MCP API KEY (조건부 표시)
                    if state.use_mcp:
                        me.input(
                            label="MCP API KEY",
                            value=state.mcp_api_key or "",
                            style=me.Style(width="120%"),
                            on_blur=lambda e: setattr(state, "mcp_api_key", e.value)
                        )
                        me.textarea(
                            label="MCP TOOL CONFIG (JSON)",
                            value=state.mcp_tool_config or "",
                            placeholder='{"duckduckgo-mcp-server": {"command": "...", "args": [...]} }',
                            style=me.Style(width="120%", height="80px", font_family="monospace"),
                            on_blur=lambda e: setattr(state, "mcp_tool_config", e.value)
                        )

            state.output_modes = ["text", "text/plain"]
            state.input_modes = ["text", "text/plain"]

            # 버튼들 오른쪽 정렬
            with me.box(style=me.Style(display="flex", justify_content="end", gap=8, margin=me.Margin(top=16))):
                me.button("Save", on_click=handle_save_click)
                me.button("Cancel", on_click=cancel_create_dialog)


# -------------------- COMMON SAVE / CLEAR --------------------

async def save_agent(e: me.ClickEvent):
    state = me.state(AgentState)
    await AddRemoteAgent(state.agent_address)
    state.agent_address = ""
    state.agent_name = ""
    state.agent_description = ""
    state.agent_model = ""
    state.system_message = ""
    state.api_key = ""
    state.tags = []
    state.agent_dialog_open = False
    state.create_dialog_open = False

async def save_created_agent(e: me.ClickEvent):
    state = me.state(AgentState)

    forwarded = await create_agent_on_k8s(state)

    state.agent_address = f"localhost:{forwarded}"

    time.sleep(2)
    await AddRemoteAgent(state.agent_address)
    state.agent_address = ""
    state.agent_name = ""
    state.agent_description = ""
    state.agent_model = ""
    state.system_message = ""
    state.api_key = ""
    state.tags = []
    state.use_mcp = False
    state.mcp_api_key = ""
    state.mcp_tool_config = {}
    state.agent_dialog_open = False
    state.create_dialog_open = False

def clear_class():
    state = me.state(AgentState)
    state.agent_address = ""
    state.agent_name = ""
    state.agent_description = ""
    state.agent_model = ""
    state.system_message = ""
    state.api_key = ""
    state.tags = []
    state.stream_supported = False
    state.push_notifications_supported = False
    state.error = ""
    state.use_mcp = False
    state.mcp_api_key = ""
    state.mcp_tool_config = {}

# ----------------- K8S -----------------------

async def create_agent_on_k8s(state):
    local_port = get_ephemeral_port()

    print ("선택된 로컬 포트: ", local_port)
    cmd_args = [
        "--host=0.0.0.0",
        f"--port={local_port}",
        f"--name={state.agent_name}",
        f"--desc={state.agent_description}",
        f"--model={state.agent_model}",
        f"--tags={",".join(state.tags or [])}",
        f"--system={state.system_message}",
        f"--examples={",".join([])}",
        f"--key={state.api_key}",
        f"--mcpkey={state.mcp_api_key}",
        f"--mcp-tools={state.mcp_tool_config}",
    ]
    create_agent_pod(
        image="dongyeuk/agent-template:latest",
        pod_name=state.agent_name,
        namespace="default",
        cmd_args=cmd_args,
        port=local_port
    )
    print ("Create_agent_on_k8s done")

    try:
        config.load_kube_config()
    except config.ConfigException:
        config.load_incluster_config()
    v1 = client.CoreV1Api()

    wait_for_service_ready(pod_name=state.agent_name, retries=120, port=local_port)
    pf_cmd = [
        "kubectl", "port-forward",
        "-n", "default",
        f"pod/{state.agent_name}",
        f"{local_port}:{local_port}"
    ]
    # state에 프로세스 저장해두면 나중에 꺼낼 수 있습니다
    proc = await asyncio.create_subprocess_exec(
        *pf_cmd,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    state.port_forwards[state.agent_name] = proc.pid
    print ("포트포워딩 프로세스 PID: ", proc.pid)
    return local_port

def get_ephemeral_port() -> int:
    """OS가 골라주는 빈 포트를 하나 가져와 반환합니다."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # '' 은 0.0.0.0 (모든 인터페이스), 포트는 0이면 OS가 임의 할당
        s.bind(('', 0))
        _, port = s.getsockname()
    return port

def wait_for_service_ready(
    pod_name: str,
    retries: int = 20,
    port: int = 10000,
) -> bool:
    """
    1) kubectl exec 를 이용해 파드 내부에서 HTTP 요청을 보냅니다.
    2) health_path 에 정상 응답(HTTP 200)이 오면 True, 아니면 재시도.
    3) 지정된 retries 만큼 재시도 후에도 안 되면 False를 반환합니다.
    """
    for attempt in range(1, retries + 1):
        # --- ① 검사할 curl 명령어 리스트 생성 ---
        # kubectl exec <pod> -n <ns> -- curl -s --fail http://localhost:<port><health_path>
        cmd = [
            "kubectl", "exec",
            f"pod/{pod_name}",
            "-n", "default",
            "--",
            "curl",
            "-s",          # Silent 모드: 진행바 등 출력 없이
            "--fail",      # HTTP 에러 코드(>=400) 면 exit code 22 반환
            f"http://localhost:{port}/health"
        ]

        print(f"[{attempt}/{retries}] Checking service on {pod_name}:{port}/health ...", end=" ")

        try:
            completed = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print("OK")
            return True

        except subprocess.CalledProcessError as e:
            print("Not Ready")

        # --- ③ 실패했으면 delay 만큼 대기 후 재시도 ---
        time.sleep(1)

    # 지정한 횟수(retries) 모두 실패하면 False 반환
    print(f"[ERROR] Service on port {port} did not become ready after {retries} attempts.")
    return False

def create_agent_pod(
    image: str,
    pod_name: str,
    namespace: str,
    cmd_args: list[str],
    port: int = 10000,
):
   # ① 쿠베 config 로드 (로컬 ↔ 클러스터)
    try:
        config.load_kube_config()
    except config.ConfigException:
        config.load_incluster_config()

    v1 = client.CoreV1Api()

    # ② 컨테이너 스펙: entrypoint(uv)와 click 인자를 args로 전달
    container = client.V1Container(
        name=pod_name,
        image=image,
        command=["uv", "run", "."],
        args=cmd_args,
        ports=[client.V1ContainerPort(container_port=port)],
    )

    # ③ 파드 스펙 & 메타데이터
    spec = client.V1PodSpec(
        containers=[container],
        restart_policy="Never",   # 필요에 따라 OnFailure, Always
    )
    meta = client.V1ObjectMeta(
        name=pod_name,
        labels={"app": pod_name},
    )
    pod = client.V1Pod(api_version="v1", kind="Pod", metadata=meta, spec=spec)

    # ④ 파드 생성 API 호출
    try:
        resp = v1.create_namespaced_pod(namespace=namespace, body=pod)
        print(f"[+] Pod 생성 요청 완료: {resp.metadata.name}")
    except ApiException as e:
        print(f"[!] 파드 생성 실패: {e.reason}\n{e.body}")
