from kubernetes import client, config

config.load_kube_config()

v1 = client.CoreV1Api()

print("Listing pods in the default namespace:")
pods = v1.list_namespaced_pod(namespace='default')
for pod in pods.items:
    print(f"Pod Name: {pod.metadata.name}, Status: {pod.status.phase}")