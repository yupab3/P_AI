import mesop as me
import pandas as pd
from typing import List, Tuple

from state.state import AppState
from state.agent_state import AgentState
from common.types import AgentCard

@me.component
def agents_list(
    agents: list[AgentCard],
):
  """Agents list component"""
  df_data = {
      "Address": [],
      "Name": [],
      "Description": [],
      "Model": [],
      "Input Modes": [],
      "Output Modes": [],
      "Streaming": [],
  }
  for agent_info in agents:
    df_data["Address"].append(agent_info.url)
    df_data["Name"].append(agent_info.name)
    df_data["Description"].append(agent_info.description)
    df_data["Model"].append(agent_info.model)
    df_data["Input Modes"].append(", ".join(agent_info.defaultInputModes))
    df_data["Output Modes"].append(", ".join(agent_info.defaultOutputModes))
    df_data["Streaming"].append(agent_info.capabilities.streaming)
  df = pd.DataFrame(
      pd.DataFrame(df_data),
      columns=[
          "Address",
          "Name",
          "Description",
          "Model",
          "Input Modes",
          "Output Modes",
          "Streaming",
      ],
  )
  with me.box(
      style=me.Style(
          display="flex",
          justify_content="space-between",
          flex_direction="column",
      )
  ):
    me.table(
        df,
        header=me.TableHeader(sticky=True),
        columns={
            "Address": me.TableColumn(sticky=True),
            "Name": me.TableColumn(sticky=True),
            "Description": me.TableColumn(sticky=True),
        },
    )
    with me.content_button(
        type="raised",
        on_click=add_agent,
        key="new_agent",
        style=me.Style(
            display="flex",
            flex_direction="row",
            gap=5,
            align_items="center",
            margin=me.Margin(top=10),
        ),
    ):
      me.icon(icon="upload")


def add_agent(e: me.ClickEvent):  # pylint: disable=unused-argument
    """import agent button handler"""
    state = me.state(AgentState)
    state.agent_dialog_open = True
