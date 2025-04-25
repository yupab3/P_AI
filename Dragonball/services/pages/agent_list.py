import stat
import asyncio
import mesop as me

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


def agent_list_page(app_state: AppState):
    """Agents List Page"""
    state = me.state(AgentState)
    with page_scaffold():
        with page_frame():
            with header("Remote Agents", "smart_toy"):
                me.button("Create Agent", on_click=open_create_dialog)

            agents = asyncio.run(ListRemoteAgents())
            agents_list(agents)

            create_agent_dialog()
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

    with dialog(state.create_dialog_open):
        with me.box(style=dialog_style):
            me.text("🔧 새로운 에이전트 생성", style=me.Style(font_size="18px", font_weight="bold"))

            me.input(
                label="Agent Name",
                value=state.agent_name or "",
                style=me.Style(width="100%"),
                on_blur=lambda e: setattr(state, "agent_name", e.value)
            )

            me.input(
                label="Description",
                value=state.agent_description or "",
                style=me.Style(width="100%"),
                on_blur=lambda e: setattr(state, "agent_description", e.value)
            )

            me.input(
                label="Model Name",
                value=state.agent_model or "",
                style=me.Style(width="100%"),
                on_blur=lambda e: setattr(state, "agent_model", e.value)
            )

            me.input(
                label="System Message",
                value=state.system_message or "",
                style=me.Style(width="100%"),
                on_blur=lambda e: setattr(state, "system_message", e.value)
            )

            state.output_modes = ["text", "text/plain"]
            state.input_modes = ["text", "text/plain"]

            # 버튼들 오른쪽 정렬
            with me.box(style=me.Style(display="flex", justify_content="end", gap=8, margin=me.Margin(top=16))):
                me.button("Save", on_click=save_agent)
                me.button("Cancel", on_click=cancel_create_dialog)


# -------------------- COMMON SAVE --------------------

async def save_agent(e: me.ClickEvent):
    state = me.state(AgentState)
    await AddRemoteAgent(state.agent_address)
    state.agent_address = ""
    state.agent_name = ""
    state.agent_description = ""
    state.agent_model = ""
    state.system_message = ""
    state.agent_dialog_open = False
    state.create_dialog_open = False


def clear_class():
    state = me.state(AgentState)
    state.agent_address = ""
    state.agent_name = ""
    state.agent_description = ""
    state.agent_model = ""
    state.system_message = ""
    state.stream_supported = False
    state.push_notifications_supported = False
    state.error = ""
