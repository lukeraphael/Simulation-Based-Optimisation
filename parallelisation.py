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
image = "minifab:local-latest1"
# deploy.create_namespace(namespace)
class MyProblem(Problem):

    def __init__(self, **kwargs):
        self.count = 0
        super().__init__(n_var=3, n_obj=1, n_ieq_constr=0, xl=100, xu=700, **kwargs)

    def _evaluate(self, X, out, *args, **kwargs):
        self.count += 1

        # def my_eval(x):
        #     return np.sum(x ** 2)

        # prepare the parameters for the pool
        params = [X[k] for k in range(len(X))]
        F = []

        for val in params:
            # add inputs as files to the persistent volume
            print(val)
            deploy.store_input_file(json.dumps(val.tolist()))

            # Create pods with client-python API.
            pod = deploy.create_pod_object(app_name, image)
            deploy.create_pod(pod, namespace)
            res_str = deploy.delete_pod_and_get_results(namespace)

            # decode json string into dict
            res = json.loads(res_str)

            # perform application specific data extraction and store the necessary output into F
            output = []
            for i in range(self.n_obj):
                output.append(res["results"][i]["throughput"])

            print(res)

        # store the function values and return them.
        out["F"] = np.array(F)

problem = MyProblem()
res = minimize(problem, GA(), termination=("n_gen", 3), seed=1)
print('Threads:', res.exec_time)
print('Count:', problem.count)

# plt res.F
print(res.F)

# deploy.store_input_file(json.dumps([540, 541, 542]))
# pod = deploy.create_pod_object(app_name, image)
# deploy.create_pod(pod, namespace) 
# # sleep for 5 seconds
# sleep(20)
# res_str = deploy.delete_pod_and_get_results(namespace)

# deploy.delete_namespace(namespace)
