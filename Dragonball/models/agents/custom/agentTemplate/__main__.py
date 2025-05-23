from common.server import A2AServer
from common.types import AgentCard, AgentCapabilities, AgentSkill, MissingAPIKeyError
from common.utils.push_notification_auth import PushNotificationSenderAuth
from task_manager import AgentTaskManager
from agent import UserDefinedAgent
import click
import os
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_csv(ctx, param, value):
    if value:
        return [tag.strip() for tag in value.split(",")]
    return []

def parse_json(ctx, param, value):
    try:
        return json.loads(value)
    except json.JSONDecodeError as e:
        raise click.BadParameter(f"Invalid JSON for `{param.name}`: {e}")

@click.command()
@click.option("--host", "host", default="localhost")
@click.option("--port", "port", default=10000)
@click.option("--name", "inputname", default="")
@click.option("--desc", "inputdesc", default="")
@click.option("--model", "inputmodel", default="")
@click.option("--tags", "inputtags", default=[], callback=parse_csv)
@click.option("--system", "inputsystem", default="")
@click.option("--examples", "inputexamples", default=[], callback=parse_csv)
@click.option("--key", "inputkey", default="")
@click.option("--mcpkey", "mcpkey", default="")
@click.option("--mcp-tools", "mcp_tools", default="{}", callback=parse_json, help="MCP tools configuration as a JSON string")
def main(host, port, inputname, inputdesc, inputmodel, inputtags, inputsystem, inputexamples, inputkey, mcpkey, mcp_tools):
    f"""Starts the {inputname} Agent server."""
    try:
        print("**** mcp_tools ****")
        print(mcp_tools)
        if not inputkey:
            raise MissingAPIKeyError("No api key.")
        prefix = inputmodel.split("-", 1)[0].lower()
        if mcpkey:
            os.environ["SMITHERY_API_KEY"] = mcpkey
        if prefix == "gpt":
            os.environ["OPENAI_API_KEY"] = inputkey
        elif prefix == "gemini":
            os.environ["GOOGLE_API_KEY"] = inputkey
        else:
            MissingAPIKeyError("This model is not supported.")

        capabilities = AgentCapabilities(streaming=True, pushNotifications=True)
        skill = AgentSkill(
            id=inputname,
            name=inputname,
            description=inputdesc,
            tags=inputtags,
            examples=inputexamples, # 현재 사용하지 않지만 추후 개선 가능
        )
        agent = UserDefinedAgent(inputmodel, inputsystem, mcp_tools)
        agent_card = AgentCard(
            name=inputname,
            description=inputdesc,
            url=f"http://{host}:{port}/",
            version="1.0.0",
            model=agent.MODEL_NAME,
            systemMessage=agent.SYSTEM_INSTRUCTION,
            defaultInputModes=UserDefinedAgent.SUPPORTED_CONTENT_TYPES,
            defaultOutputModes=UserDefinedAgent.SUPPORTED_CONTENT_TYPES,
            capabilities=capabilities,
            skills=[skill],
        )

        notification_sender_auth = PushNotificationSenderAuth()
        notification_sender_auth.generate_jwk()
        server = A2AServer(
            agent_card=agent_card,
            task_manager=AgentTaskManager(agent=agent, notification_sender_auth=notification_sender_auth),
            host=host,
            port=port,
        )

        server.app.add_route(
            "/.well-known/jwks.json", notification_sender_auth.handle_jwks_endpoint, methods=["GET"]
        )

        logger.info(f"Starting server on {host}:{port}")
        server.start()
    except MissingAPIKeyError as e:
        logger.error(f"Error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")
        exit(1)


if __name__ == "__main__":
    main()
