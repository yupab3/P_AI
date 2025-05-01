import click
import os
import logging
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_csv(ctx, param, value):
    if value:
        return [tag.strip() for tag in value.split(",")]
    return []

@click.command()
@click.option("--host", "host", default="0.0.0.0")
@click.option("--port", "port", default=10000)
@click.option("--name", "inputname", default="")
@click.option("--desc", "inputdesc", default="")
@click.option("--model", "inputmodel", default="")
@click.option("--tags", "inputtags", default=[], callback=parse_csv)
@click.option("--system", "inputsystem", default="")
@click.option("--examples", "inputexamples", default=[], callback=parse_csv)
@click.option("--key", "inputkey", default="")
def main(host, port, inputname, inputdesc, inputmodel, inputtags, inputsystem, inputexamples, inputkey):
    try:
        # 헬름 차트 배포 명령어 구성
        helm_command = [
            "helm", "install", inputname, "./mychart",
            "--set", f"host={host}",
            "--set", f"port={port}",
            "--set", f"description={inputdesc}",
            "--set", f"model={inputmodel}",
            "--set", f"tags={','.join(inputtags)}",
            "--set", f"system={inputsystem}",
            "--set", f"examples={','.join(inputexamples)}",
            "--set", f"key={inputkey}"
        ]

        # 헬름 명령어 실행
        result = subprocess.run(helm_command, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("Helm chart deployed successfully!")
            logger.info(result.stdout)
        else:
            logger.error("Error deploying Helm chart:")
            logger.error(result.stderr)
    except Exception as e:
        logger.error(f"Exception occurred: {e}")

if __name__ == "__main__":
    main()