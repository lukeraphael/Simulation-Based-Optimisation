import argparse
from kubernetes import client, config

# delete pods that start with 'prefix'
def delete_pods(namespace: str, prefix: str) -> None:
    v1 = client.CoreV1Api()
    pods = v1.list_namespaced_pod(namespace=namespace)
    for pod in pods.items:
        if pod.metadata.name.startswith(prefix):
            print(f"[INFO] deleting pod {pod.metadata.name}")
            v1.delete_namespaced_pod(name=pod.metadata.name, namespace=namespace)

if __name__ == "__main__":
    # get prefix from args
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", type=str, required=True)
    args = parser.parse_args()
    
    config.load_kube_config()
    delete_pods("argo", args.prefix)