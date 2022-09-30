from calendar import c
from typing import List
from kubernetes import client
from kubernetes.stream import stream
import time
import docker
import os

def create_namespace(namespace):
    # Create namespace
    api = client.CoreV1Api()
    body = client.V1Namespace(
        api_version="v1",
        kind="Namespace",
        metadata=client.V1ObjectMeta(name=namespace),
    )
    resp = api.create_namespace(body=body)

    # print(f"[INFO] namespace {resp.metadata.name} created.")

def delete_namespace(namespace):
    # Delete namespace
    api = client.CoreV1Api()
    api.delete_namespace(name=namespace)

    # print(f"\n[INFO] namespace {namespace} deleted.\n")

# todo: remove hardcode
def create_pod_object(app_name: str, image: str, command: List[str], pv: str, pv_claim: str, mount: str) -> client.V1Pod:
    # Configureate Pod template container
    container = client.V1Container(
        name=app_name,
        image=image,
        image_pull_policy="IfNotPresent",
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

    # print(f"[INFO] pod {resp.metadata.name} created.")

def store_input_file(path: str, content: str, docker_name: str) -> None:
    '''
    store input file to persistent volume
    content is data in json format
    path is the path to the file where the data will be stored
    '''
    # docker_client = docker.from_env()
    # container = docker_client.containers.get(docker_name)
    # cmd = [
    #     "bash", 
    #     "-c",
    #     f"echo {content} > {path}",
    # ]
    # container.exec_run(cmd)
    
    # save file to persistent volume, if it doesn't exist, create it
    if not os.path.exists(path):
        open(path, "w").close()
    with open(path, "w") as f:
        f.write(content)

# returns the contents of the output files as an array
def delete_pods_and_get_results(namespace: str, docker_name: str, output_paths: List[str]) -> List[str]:
    # wait for minifab pods to complete
    v1 = client.CoreV1Api()

    timeout = 60*10
    start_time = time.time()
    finished_pods = set()
    pods = v1.list_namespaced_pod(namespace=namespace)
    while len(finished_pods) < len(output_paths):
        if time.time() - start_time > timeout:
            raise TimeoutError("Timeout waiting for pods to complete")

        time.sleep(5)
        for pod in pods.items:
            if pod.metadata.name in finished_pods:
                continue
            if pod.status.phase == "Succeeded":
                finished_pods.add(pod.metadata.name)
                # print(f"[INFO] pod {pod.metadata.name} completed.")
        pods = v1.list_namespaced_pod(namespace=namespace)

    docker_client = docker.from_env()
    container = docker_client.containers.get(docker_name)

    def get_output_file(path: str) -> str:
        # cmd = [
        #     "bash", 
        #     "-c",
        #     f"cat {path}",
        # ]
        # output = container.exec_run(cmd)
        # return output.output.decode("utf-8")
        return open(path, "r").read()
    
    res = [get_output_file(path) for path in output_paths]
    # print(f"[INFO] {res}")

    # delete_pods(namespace)
    delete_pods_prefix(namespace, "minifab")
    return res

def delete_pods_prefix(namespace: str, prefix: str) -> None:
    v1 = client.CoreV1Api()
    pods = v1.list_namespaced_pod(namespace=namespace)
    for pod in pods.items:
        if pod.metadata.name.startswith(prefix):
            try:
                v1.delete_namespaced_pod(name=pod.metadata.name, namespace=namespace)
            except Exception as e:
                pass
                print(f"[ERROR] {e}")
            # print(f"[INFO] deleting pod {pod.metadata.name}")
            # v1.delete_namespaced_pod(name=pod.metadata.name, namespace=namespace)

def delete_pods(namespace: str) -> None:
    v1 = client.CoreV1Api()
    pods = v1.list_namespaced_pod(namespace=namespace)
    for pod in pods.items:
        # print(f"[INFO] deleting pod {pod.metadata.name}")
        v1.delete_namespaced_pod(name=pod.metadata.name, namespace=namespace)

    # wait for the pods to be deleted
    while True:
        pods = v1.list_namespaced_pod(namespace=namespace)
        if len(pods.items) == 0:
            # print("[INFO] all pods deleted.")
            break
        time.sleep(5)

def read_file_from_k8_pod(namespace: str, pod_name: str, path: str) -> str:
    v1 = client.CoreV1Api()
    # resp = v1.read_namespaced_pod(name=pod_name, namespace=namespace)

    # bash into the pod and read the file
    command = [
        "bash",
        "-c",
        f"cat {path}",
    ]
    resp = stream(v1.connect_get_namespaced_pod_exec, pod_name, namespace,
              command=command,
              stderr=True, stdin=True,
              stdout=True, tty=False,
              _preload_content=False
    )
    
    while resp.is_open():
        resp.update(timeout=1)
        if resp.peek_stdout():
            # print("STDOUT: %s" % resp.read_stdout())
            return resp.read_stdout()
        if resp.peek_stderr():
            # print("Error: %s" % resp.read_stderr())
            os.exit(1)

        if command:
            c = command.pop(0)
            # print("Running command... %s\n" % c)
            resp.write_stdin(c)
