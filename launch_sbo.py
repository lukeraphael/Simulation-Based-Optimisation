import deploy.deploy as deploy
from kubernetes import client, config
import time
import os
# generations, workers, population size
params = [
    # [1,1,10],
    # [20, 10, 50],
    # [40, 10, 50],
    # [60, 10, 50],
    # [80, 10, 50],
    # [100, 10, 50],
    # [120, 10, 50],
    # [140, 10, 50],
    # [160, 10, 50],
    # [50, 10, 20],
    # [50, 10, 40],
    # [50, 10, 60],
    # [50, 10, 80],
    # [50, 10, 100],
    # [50, 10, 120],
    # [50, 10, 140],
    # [50, 10, 160],
    [5, 10, 50],
    [5, 20, 50],
    # [5, 30, 50],
    # [5, 40, 50],
    # [5, 50, 50]
]

config.load_kube_config()
v1 = client.CoreV1Api()
namespace = "argo"

for gen, workers, pop_size in params:
    command = ["python3", "parallelisation.py", 
        "--workers", str(workers), 
        "--n_gen", str(gen), 
        "--pop_size", str(pop_size), 
        "--choice", "kubernetes"
    ]
    pod = deploy.create_pod_object(
        "sbo", 
        "lukeraphael/sbo:latest", 
        command, 
        "argo-pv-volume", 
        "argo-pv-claim", 
        "/minifab/"
    )
    resp = deploy.create_pod(pod, namespace)
    pod_name = resp.metadata.name
    
    # wait for pod to finish
    while True:
        pod = v1.read_namespaced_pod_status(pod_name, namespace)
        if pod.status.phase == "Succeeded":
            break
        time.sleep(10)

    # read the logs
    logs = v1.read_namespaced_pod_log(pod_name, namespace)
    print(logs, workers, gen, pop_size)
    
    # save into csv
    with open("experiments/standalone_kubernetes_output.csv", "a") as f:
        # if not empty, insert newline
        if os.stat("experiments/standalone_kubernetes_output.csv").st_size != 0:
            f.write("\n")
        f.write(f"{workers},{gen},{pop_size},{logs}")


    # delete the pod
    v1.delete_namespaced_pod(pod_name, namespace)

    # wait for pod to be deleted
    while True:
        try:
            pod = v1.read_namespaced_pod_status(pod_name, namespace)
        except:
            break
        time.sleep(2)