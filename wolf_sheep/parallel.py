from random import seed
from pymoo.core.problem import ElementwiseProblem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.factory import get_sampling, get_crossover, get_mutation, get_termination
from pymoo.optimize import minimize

import matplotlib.pyplot as plt
from wolf_sheep.agents import Sheep, Wolf
from wolf_sheep.model import WolfSheep
import numpy as np


def run_simulation(wolves: int, regrowth: int):
    model = WolfSheep()
    model._seed = 1
    model.initial_wolves = wolves
    model.initial_sheep = 100
    model.grass_regrowth_time = regrowth
    model.run_model(step_count=70)

    # Store the results
    return model.schedule.get_breed_count(Wolf), model.schedule.get_breed_count(Sheep)


class MyProblem(ElementwiseProblem):

    def __init__(self):
        self.count = 0
        super().__init__(n_var=2,
                         n_obj=2,
                         n_constr=2,
                         xl=np.array([1, 1]),
                         xu=np.array([200, 500]))

    def _evaluate(self, x, out, *args, **kwargs):
        f1, f2 = run_simulation(int(x[0]), int(x[1]))
        '''
        if worker is available, start running simulation
        otherwise, stall and wait for an available worker
        '''

        f2 > 20
        f2 < 50
        out["F"] = [x[0], x[1]]
        out["G"] = [10 - f2, f2 - 50]


problem = MyProblem()


algorithm = NSGA2(
    pop_size=40,
    n_offsprings=10,
    sampling=get_sampling("real_random"),
    crossover=get_crossover("real_sbx", prob=0.9, eta=15),
    mutation=get_mutation("real_pm", eta=20),
    eliminate_duplicates=True,
    seed=1
)


res = minimize(problem,
               algorithm,
               seed=1,
               save_history=True,
               verbose=True)

X = res.X
F = res.F

print(res.X)
print(res.F)

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
