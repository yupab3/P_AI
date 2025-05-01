# Tiller(Helm 서버) 연결 (높은 버전의 Helm과 호환되도록 수정)
class HelmClient:
    def __init__(self, namespace='default'):
        self.namespace = namespace

    def install_chart(self, chart_path, release_name):
        import subprocess
        try:
            result = subprocess.run(
                ["helm", "install", release_name, chart_path, "--namespace", self.namespace],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("Helm chart deployed successfully!")
                print(result.stdout)
            else:
                print("Error deploying Helm chart:")
                print(result.stderr)
        except Exception as e:
            print(f"Exception occurred: {e}")

# 헬름 차트 배포
helm_client = HelmClient(namespace='default')
helm_client.install_chart('./mychart', 'mychart')