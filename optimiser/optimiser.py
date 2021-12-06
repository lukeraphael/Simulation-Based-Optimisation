import time
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.factory import get_sampling, get_crossover, get_mutation, get_termination
from pymoo.optimize import minimize

import matplotlib.pyplot as plt
import numpy as np
import json
from requests_futures.sessions import FuturesSession

import sys

# get server ports from arguments (docker / argo)
server_ports = sys.argv[1].split(', ')
session = FuturesSession()


class MyProblem(Problem):
    def __init__(self):
        self.count = 0
        super().__init__(n_var=2,
                         n_obj=2,
                         n_constr=2,
                         xl=np.array([1, 1]),
                         xu=np.array([200, 500]))

    def _evaluate(self, x, out, *args, **kwargs):
        length = len(x)
        promises = []
        i = 0

        while i < length:
            temp = []

            # send requests to all workers
            for endpoint in server_ports:
                wolves, regrowth = x[i]
                test = ['test', 'test']
                temp.append(session.post(endpoint, json={'wolves': wolves, 'regrowth': regrowth, 'payload': test}))
                i += 1

                if i == length:
                    break

            # convert the futures to a list of results
            for j, promise in enumerate(temp):
                temp[j] = json.loads(promise.result().content)['answer']

            promises.extend(temp)

        # out['F'] = [x[0], x[1]]
        # out['G'] = [x[0], x[1]]

        # minimise the number of wolves and regrowth time while keeping the number of sheep
        # within the bounds
        out['F'] = x
        out['G'] = np.array([[10 - promise, promise - 50] for promise in promises])


# create the problem
problem = MyProblem()
termination = get_termination("n_gen", 50)

# create the algorithm
algorithm = NSGA2(
    pop_size=40,
    n_offsprings=10,
    sampling=get_sampling("real_random"),
    crossover=get_crossover("real_sbx", prob=0.9, eta=15),
    mutation=get_mutation("real_pm", eta=20),
    eliminate_duplicates=True,
    seed=1,
    termination=termination
)


time_start = time.time()
# run the algorithm, all optimizations are run as minimization in Mesa
res = minimize(problem,
               algorithm,
               seed=1,
               save_history=True,
               verbose=True)

# Design and objective space
X = res.X
F = res.F

print(res.X)
print(res.F)
time_end = time.time() - time_start

print(f'time elapsed: {time_end}')

xl, xu = problem.bounds()
plt.figure(figsize=(7, 5))
plt.scatter(X[:, 0], X[:, 1], s=30, facecolors='none', edgecolors='r')
plt.xlim(min(X[:, 0]) - 20, max(X[:, 0]) + 20)
plt.ylim(min(X[:, 1]) - 20, max(X[:, 1]) + 20)
plt.title("Design Space")
plt.show()

plt.figure(figsize=(7, 5))
plt.scatter(F[:, 0], F[:, 1], s=30, facecolors='none', edgecolors='blue')
plt.title("Objective Space")
plt.show()

print(problem.count)
