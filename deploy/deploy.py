from typing import List
from kubernetes import client
import time
import docker

def create_namespace(namespace):
    # Create namespace
    api = client.CoreV1Api()
    body = client.V1Namespace(
        api_version="v1",
        kind="Namespace",
        metadata=client.V1ObjectMeta(name=namespace),
    )
    resp = api.create_namespace(body=body)

    print(f"[INFO] namespace {resp.metadata.name} created.")

def delete_namespace(namespace):
    # Delete namespace
    api = client.CoreV1Api()
    api.delete_namespace(name=namespace)

    print(f"\n[INFO] namespace {namespace} deleted.\n")

# todo: remove hardcode
def create_pod_object(app_name: str, image: str, command: List[str], pv: str, pv_claim: str, mount: str) -> client.V1Pod:
    # Configureate Pod template container
    container = client.V1Container(
        name=app_name,
        image=image,
        image_pull_policy="Never",
        resources=client.V1ResourceRequirements(
            requests={"cpu": "100m", "memory": "200Mi"},
            limits={"cpu": "500m", "memory": "500Mi"},
        ),
        volume_mounts=[client.V1VolumeMount(
            name=pv,
            mount_path=mount
        )],
    )

    if command:
        container.command = command

    gen_name = f"{app_name}-"
    # Create and configure a spec section
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(
            labels={"app": app_name}, 
            generate_name=gen_name
        ),
        spec=client.V1PodSpec(
            containers=[container],
            restart_policy="OnFailure",
            volumes=[client.V1Volume(
                name=pv,
                persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(claim_name=pv_claim),
            )],
        )
    )

    # return pod object
    return client.V1Pod(
        api_version="v1",
        kind="Pod",
        metadata=template.metadata,
        spec=template.spec
    )

def create_pod(pod, namespace):
    # Create deployement
    api = client.CoreV1Api()
    resp = api.create_namespaced_pod(
        body=pod, 
        namespace=namespace
    )

    print(f"[INFO] pod {resp.metadata.name} created.")

def store_input_file(path: str, content: str, docker_name: str) -> None:
    '''
    store input file to persistent volume
    content is data in json format
    path is the path to the file where the data will be stored
    '''
    docker_client = docker.from_env()
    container = docker_client.containers.get(docker_name)
    cmd = [
        "bash", 
        "-c",
        f"echo {content} > {path}",
    ]
    container.exec_run(cmd)

# returns the contents of the output files as an array
def delete_pod_and_get_results(namespace: str, docker_name: str, output_paths: List[str]) -> List[str]:
    # wait for minifab pods to complete
    v1 = client.CoreV1Api()

    timeout = 60*10
    start_time = time.time()
    finished_pods = set()
    pods = v1.list_namespaced_pod(namespace=namespace)
    while len(finished_pods) < len(pods.items):
        if time.time() - start_time > timeout:
            raise TimeoutError("Timeout waiting for pods to complete")

        time.sleep(5)
        for pod in pods.items:
            if pod.metadata.name in finished_pods:
                continue
            if pod.status.phase == "Succeeded":
                finished_pods.add(pod.metadata.name)
                print(f"[INFO] pod {pod.metadata.name} completed.")
        pods = v1.list_namespaced_pod(namespace=namespace)

    docker_client = docker.from_env()
    container = docker_client.containers.get(docker_name)

    def get_output_file(path: str) -> str:
        cmd = [
            "bash", 
            "-c",
            f"cat {path}",
        ]
        output = container.exec_run(cmd)
        return output.output.decode("utf-8")
    
    res = [get_output_file(path) for path in output_paths]
    print(f"[INFO] {res}")
    
    # Delete pods
    for pod in pods.items:
        print(f"[INFO] deleting pod {pod.metadata.name}")
        v1.delete_namespaced_pod(name=pod.metadata.name, namespace=namespace)

    # wait for the pods to be deleted
    while True:
        pods = v1.list_namespaced_pod(namespace=namespace)
        if len(pods.items) == 0:
            print("[INFO] all pods deleted.")
            break
        time.sleep(5)

    return res