from autogen.coding import CodeBlock
from autogen.coding.jupyter import DockerJupyterServer, JupyterCodeExecutor

with DockerJupyterServer() as server:
    executor = JupyterCodeExecutor(server)
    print(
        executor.execute_code_blocks(
            code_blocks=[
                CodeBlock(language="python", code="print('Hello, World!')"),
            ]
        )
    )

### 기본 Dockerfile 출력 ###
print(DockerJupyterServer.DEFAULT_DOCKERFILE)