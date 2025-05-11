## 주요 구성

### 1. Default Agent (`defaultagent`)

`defaultagent`는 LangGraph를 기반으로 구축된 에이전트로, A2A 프로토콜을 통해 동작합니다. 이 에이전트는 텍스트 기반의 입력/출력을 지원하며, 다중 턴 대화와 스트리밍 응답을 제공합니다.

#### 실행 방법

1. `defaultagent` 디렉토리로 이동합니다:

   ```bash
   cd models/agents/default/defaultagent
   ```

2. 에이전트를 실행합니다:
   ```bash
   uv run .
   ```

3. 기본적으로 포트 10000번에서 실행됩니다.
   커스텀 호스트/포트를 지정하려면 다음 명령어를 사용하세요:
   ```bash
   uv run . --host 0.0.0.0 --port 8080
   ```


### 1. Services

`services`는 에이전트와 상호작용할 수 있는 UI 및 API를 제공합니다. FastAPI를 기반으로 구축되었으며, 다양한 의존성을 포함합니다.

#### 실행 방법

1. `services` 디렉토리로 이동합니다:

   ```bash
   cd services
   ```

2. 서비스를 실행합니다:
   ```bash
   uv run main.py
   ```

기본적으로 포트 12000번에서 실행됩니다.