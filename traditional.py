import argparse
import json
from typing import List
import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.core.problem import Problem
from pymoo.termination.default import DefaultMultiObjectiveTermination
from requests_futures.sessions import FuturesSession
from minifab.main import simulate
from concurrent.futures import ThreadPoolExecutor


# parse args number of workers, number of generations, population size
args = argparse.ArgumentParser()
args.add_argument("--workers", type=int, required=True)
args.add_argument("--n_gen", type=int, required=True)
args.add_argument("--pop_size", type=int, required=True)
parsed_args = args.parse_args()

class MyProblem(Problem):

    def __init__(self, **kwargs):
        self.workers = kwargs["workers"]
        super().__init__(n_var=3, n_obj=3, n_ieq_constr=0, xl=100, xu=700, **kwargs)

    def _evaluate(self, X, out, *args, **kwargs):
        params = [X[k].tolist() for k in range(len(X))]
        F = []

        def task(dispatch):
            res = simulate(dispatch)
            output = [-res["results"][i]["throughput"] for i in range(self.n_obj)]
            return output

        with ThreadPoolExecutor(max_workers = parsed_args.workers) as executor:
            F = executor.map(task, params)

        out["F"] = np.array(list(F))



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