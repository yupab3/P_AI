from autogen.coding import CodeBlock
from autogen.coding.jupyter import JupyterCodeExecutor, JupyterConnectionInfo, DockerJupyterServer

### 아래는 정석적인 방법이며, 실제로 Jupyter 서버를 켜고 host, token을 수정한 뒤 테스트 해야 한다. ###
# executor = JupyterCodeExecutor(
#     jupyter_server=JupyterConnectionInfo(host='example.com', use_https=True, port=7893, token='mytoken')
# )

### 따라서 간단한 테스트는 아래 방법으로 도커를 활용해 해볼 수 있다. ###
server = DockerJupyterServer()
executor = JupyterCodeExecutor(jupyter_server=server)
print(
        executor.execute_code_blocks(
            code_blocks=[
                CodeBlock(language="python", code="print('Hello, World!')"),
            ]
        )
    )