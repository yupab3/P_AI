from autogen.coding import CodeBlock
from autogen.coding.jupyter import JupyterCodeExecutor, LocalJupyterServer

with LocalJupyterServer() as server:
    executor = JupyterCodeExecutor(server)
    print(
        executor.execute_code_blocks(
            code_blocks=[
                CodeBlock(language="python", code="print('Hello, World!')"),
            ]
        )
    )