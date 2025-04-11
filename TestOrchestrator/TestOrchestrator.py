import os
from dotenv import load_dotenv
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager, ConversableAgent
import logging

# 환경변수 불러오기
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# LLM 설정
config_list = [
    {
        "model": "gpt-3.5-turbo",
        "api_key": api_key,
    }
]

frontend_team = [
    AssistantAgent(
        name="frontend_dev",
        llm_config={"config_list": config_list},
        system_message="You are a frontend developer specializing in HTML, CSS, and JavaScript."
    ),
    AssistantAgent(
        name="frontend_reviewer",
        llm_config={"config_list": config_list},
        system_message="You are a frontend code reviewer focused on quality and best practices."
    )
]

backend_team = [
    AssistantAgent(
        name="backend_api",
        llm_config={"config_list": config_list},
        system_message="You are a backend developer specializing in API development using Java and Spring Boot."
    ),
    AssistantAgent(
        name="backend_db",
        llm_config={"config_list": config_list},
        system_message="You are a backend developer specializing in database schema design and optimization."
    )
]

design_team = [
    AssistantAgent(
        name="designer_ui",
        llm_config={"config_list": config_list},
        system_message="You are a UI designer who creates clean and user-friendly interfaces."
    ),
    AssistantAgent(
        name="designer_ux",
        llm_config={"config_list": config_list},
        system_message="You are a UX designer focused on usability and flow."
    )
]

class LLMTeamBroker(ConversableAgent):
    def __init__(self, name, team_map, llm_config):
        super().__init__(name=name, llm_config=llm_config)
        self.team_map = team_map  # 이 브로커가 관리하는 팀 목록

    def decide_and_run(self, task_plan, shared_context=""):
        system_prompt = (
            f"You are the {self.name} broker. "
            "Based on the task plan and shared context, decide:\n"
            "1. Should this task be executed now?\n"
            "2. Which agents from your team should be used?\n"
            "3. Do you need input from other teams first?\n"
            "Reply with your decision and reasoning in JSON."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Task Plan: {task_plan}\n\nContext: {shared_context}"}
        ]
        response = self.chat(messages)
        decision = self.extract_decision_from_response(response)

        if decision["execute"]:
            selected_agents = [self.team_map[name] for name in decision["agents"]]
            return self.execute_team(selected_agents, decision["task"])
        else:
            return {"status": "deferred", "reason": decision["reason"]}

def run_team(team_name, agent_list, task_desc, extra_context=""):
    full_task = f"{task_desc}\n\nContext:\n{extra_context}" if extra_context else task_desc
    groupchat = GroupChat(
        agents=agent_list,
        messages=[{"role": "user", "content": full_task}],
        max_round=5
    )
    manager = GroupChatManager(
        groupchat=groupchat,
        llm_config={"config_list": config_list},
    )
    print(f"[Orchestrator] Running {team_name} team...")
    return agent_list[0].initiate_chat(manager)

# --- Step 4: Define Orchestrator ---
class OrchestratorAgent(UserProxyAgent):
    def decompose_tasks(self, user_input):
        # Simple task split for demo purposes
        return {
            "frontend": f"Create the UI for: {user_input}",
            "backend": f"Develop backend logic and API for: {user_input}",
            "design": f"Design UI/UX for: {user_input}"
        }

    def initiate_workflow(self, user_input):
        print("[Orchestrator] Decomposing task...")
        tasks = self.decompose_tasks(user_input)

        frontend_result = run_team("frontend", frontend_team, tasks["frontend"])

        backend_result = run_team("backend", backend_team, tasks["backend"])

        design_result = run_team("design", design_team, tasks["design"])

        print("[Orchestrator] Aggregating results...")
        return {
            "frontend": frontend_result,
            "backend": backend_result,
            "design": design_result
        }

# --- Step 5: Run the whole system ---
orchestrator = OrchestratorAgent(name="orchestrator")

if __name__ == "__main__":
    user_request = "Build a login page with authentication."
    result = orchestrator.initiate_workflow(user_request)
    print("\n--- Final Aggregated Result ---")
    print(result)