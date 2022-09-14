import json
from multiprocessing.pool import ThreadPool
from time import sleep
from kubernetes import client, config
import numpy as np

# import GA
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.optimize import minimize
from pymoo.core.problem import Problem

# import module
import deploy.deploy as deploy
pool = ThreadPool(8)

# kubernetes api
config.load_kube_config()
apps_v1 = client.AppsV1Api()

app_name = "minifab"
namespace = "default"
docker_name = "kind-control-plane"
image = "minifab:local-latest1"
base_path = "/mnt/data/" # set this to the mount path specified in the persistent volume claim
mount_path = "/minifab/" # set this to the mount path specified in the pod spec

pv_name = "task-pv-volume"
pv_claim_name = "task-pv-claim"

# deploy.create_namespace(namespace)
class MyProblem(Problem):

    def __init__(self, **kwargs):
        self.workers = 10
        super().__init__(n_var=3, n_obj=1, n_ieq_constr=0, xl=100, xu=700, **kwargs)

    def _evaluate(self, X, out, *args, **kwargs):
        # prepare the parameters for the pool
        # X: [self.pop_size, self.n_var]] 
        params = [X[k] for k in range(len(X))]
        print("params: ", len(params))
        F = []

        start = 0
        while start < len(params):
            output_paths = []
            for i in range(self.workers):
                if start >= len(params):
                    break

                # store inputs in persistent volume
                content = json.dumps(params[start].tolist())
                deploy.store_input_file(f"{base_path}{i}.txt", content, docker_name)

                # set output paths for the simulation
                output_paths.append(f"{base_path}{i}.json")

                # write custom command for the pods. This allows us to input the input and output paths
                command = ["python3", "./main.py", f"{mount_path}{i}.txt", f"{mount_path}{i}.json"]
                pod = deploy.create_pod_object(app_name, image, command, pv_name, pv_claim_name, mount_path) 
                deploy.create_pod(pod, namespace)
                start += 1

            # wait for pods to complete and retrieve results
            results = deploy.delete_pod_and_get_results(namespace, docker_name, output_paths)

            for res in results:
                # decode json string into dict
                res = json.loads(res)

                # perform application specific data extraction and store the necessary output into F
                # the values that one would like to minimise should be stored in F
                # to maximise, simply multiply the value by -1
                output = []
                for i in range(self.n_obj):
                    output.append(res["results"][i]["throughput"])

                F.append(output)

        # store the function values and return them.
        # print(f"[INFO] {F}")
        out["F"] = np.array(F)

problem = MyProblem()
res = minimize(problem, GA(pop_size=50), termination=("n_gen", 3), seed=1)
print('Threads:', res.exec_time)
print('Count:', problem.count)

# plt res.F
print(res.F)

# deploy.store_input_file(f"{base_path}{1}.txt", json.dumps([540, 541, 542]), docker_name)
# command = ["python3", "./main.py", f"{mount_path}{1}.txt", f"{mount_path}{1}.json"]
# pod = deploy.create_pod_object(app_name, image, command, pv_name, pv_claim_name, mount_path)
# deploy.create_pod(pod, namespace) 
# sleep(20)
# res_str = deploy.delete_pod_and_get_results(namespace)

# deploy.delete_namespace(namespace)
