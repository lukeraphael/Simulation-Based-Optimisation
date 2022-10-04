
import argparse
import json
from kubernetes import client, config
import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.core.problem import Problem
from pymoo.termination.default import DefaultMultiObjectiveTermination
import urllib3
from requests_futures.sessions import FuturesSession

# import module
import deploy.deploy as deploy
import deploy.argo as argo

# kubernetes api
config.load_kube_config("~/.kube/config")
# config.load_incluster_config()
# apps_v1 = client.AppsV1Api()
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
session = FuturesSession()

# parse args number of workers, number of generations, population size
args = argparse.ArgumentParser()
args.add_argument("--workers", type=int, required=True)
args.add_argument("--n_gen", type=int, required=True)
args.add_argument("--pop_size", type=int, required=True)
args.add_argument("--choice", type=str, required=True, choices=["kubernetes", "argo"], default="argo")
parsed_args = args.parse_args()

# check that choice is valid
if parsed_args.choice not in {"kubernetes", "argo"}:
    raise ValueError("Choice must be either 'kubernetes' or 'argo'")

# deploy.create_namespace(namespace)
class MyProblem(Problem):

    def __init__(self, **kwargs):
        self.workers = kwargs["workers"]
        super().__init__(n_var=3, n_obj=3, n_ieq_constr=0, xl=100, xu=700, **kwargs)

    def _evaluate(self, X, out, *args, **kwargs):
        # prepare the parameters for the pool
        # X: [self.pop_size, self.n_var]] 
        params = [X[k] for k in range(len(X))]
        # print("params: ", len(params))
        F = []
        futures = []
        for i in range(len(params)):
            payload = {
                "dispatch": params[i].tolist(),
                "seed": 0
            }

            if parsed_args.choice == "kubernetes":
                futures.append(session.post("http://localhost:30001/simulate", json=payload))
                
            elif parsed_args.choice == "argo":
                # argo.submit_workflow(app_name, argo_pv_name,argo_pv_claim, argo_image, mount_path, command, "argo")
                pass

        # convert the futures to a list of results
        for promise in futures:
            res = json.loads(promise.result().content)

            # perform application specific data extraction and store the necessary output into F
            # the values that one would like to minimise should be stored in F
            # to maximise, simply multiply the value by -1
            output = []
            for i in range(self.n_obj):
                output.append(-res["results"][i]["throughput"])

            F.append(output)

        # store the function values and return them.
        # print(f"[INFO] {F}")
        out["F"] = np.array(F)


problem = MyProblem(workers=parsed_args.workers)

multi_term = DefaultMultiObjectiveTermination(
    xtol=1e-8,
    cvtol=1e-6,
    ftol=0.0025,
    period=30,
    n_max_gen=parsed_args.n_gen,
    n_max_evals=100000
)

res = minimize(problem, 
    NSGA2(pop_size=parsed_args.pop_size), 
    termination=multi_term,
    seed=1,
    verbose=False)

# append results to csv
print(res.exec_time)