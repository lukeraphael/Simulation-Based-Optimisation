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

def create_pod_object(app_name, image):
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
            name="task-pv-storage", 
            mount_path="/minifab"
        )]
    )

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
                name="task-pv-storage",
                persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(claim_name="task-pv-claim"),
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

    print(f"\n[INFO] pod {resp.metadata.name} created.")

def delete_pod(namespace):
    # wait for minifab pods to complete
    v1 = client.CoreV1Api()
    pods = v1.list_namespaced_pod(namespace=namespace)

    while True:
        for pod in pods.items:
            if pod.status.phase != "Succeeded":
                print(f"[INFO] pod {pod.metadata.name} is not completed yet.")
                time.sleep(5)
                continue

        print(f"[INFO] all pods completed.")
        break

    client = docker.from_env()
    container = client.containers.get("onebox-control-plane")
    cmd = [
        "bash", 
        "-c",
        "cat /mnt/data/dict.json",
    ]
    container.exec_run(cmd)
    print(f"[INFO] {container.exec_run(cmd).output.decode('utf-8')}")
    
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