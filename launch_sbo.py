import deploy.deploy as deploy
from kubernetes import client, config
import time
import os
# generations, workers, population size
params = [
    # [1,1,10],
    # [20, 10, 100],
    # [40, 10, 100],
    # [60, 10, 100], 
    # [80, 10, 100],
    # [100, 10, 100],
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
    # server vs standalone
    # [10, 20, 20],
    # [20, 20, 20],
    # [30, 20, 20],
    # [40, 20, 20],
    [50, 20, 20],
    ]    


config.load_kube_config()
v1 = client.CoreV1Api()
namespace = "argo"
server_standalone = "standalone"
image = "lukeraphael/sbo"
app_name = "sbo"
output_path = "experiments/argo_standalone_kubernetes_output.csv"
token = "Bearer 2764ff3c24659a11cf79a3fb128221abcf11ff4f2ab0a58620793bc27689d7513d9dd12ee3e5f49f836a52ff3c3c1197b6d5001c7434222f300ad091986d2b05"

for gen, workers, pop_size in params:
    command = ["python3", "parallelisation.py", 
        "--workers", str(workers), 
        "--n_gen", str(gen), 
        "--pop_size", str(pop_size), 
        "--choice", "argo",
        "--token", token,
    ]
    if server_standalone == "server":
        image = "lukeraphael/sbo:server"
        command[1] = "server_parallelisation.py"
        command.append("--host")
        command.append("10.0.22.243")
        command.append("--port")
        command.append("5001")
        app_name = "sbo-server"
        output_path = "experiments/server_kubernetes_output.csv"

    pod = deploy.create_pod_object(
        app_name, 
        image, 
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
    with open(output_path, "a") as f:
        # if not empty, insert newline
        if os.stat(output_path).st_size != 0:
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