from multiprocessing.pool import ThreadPool
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
namespace = "minifab"
image = "minifab:local-latest"
deploy.create_namespace(namespace)
class MyProblem(Problem):

    def __init__(self, **kwargs):
        self.count = 0
        super().__init__(n_var=10, n_obj=1, n_ieq_constr=0, xl=-5, xu=5, **kwargs)

    def _evaluate(self, X, out, *args, **kwargs):
        self.count += 1

        # define the function
        def my_eval(x):
            return (x ** 2).sum()

        # prepare the parameters for the pool
        params = [[X[k]] for k in range(len(X))]

        # calculate the function values in a parallelized manner and wait until done
        F = pool.starmap(my_eval, params)

        # Create pods with client-python API.
        pod = deploy.create_pod_object(app_name, image)
        deploy.create_pod(pod, namespace)
        deploy.delete_pod(namespace)

        # store the function values and return them.
        out["F"] = np.array(F)


problem = MyProblem()
res = minimize(problem, GA(), termination=("n_gen", 3), seed=1)
print('Threads:', res.exec_time)
print('Count:', problem.count)

# plt res.F
print(res.F)

deploy.delete_namespace(namespace)

# Create a deployment object with client-python API.
# deployment_name = "minifab"

# deployment = create_pod_object(deployment_name, deployment_name, "minifab:local-latest", 1)

# create_pod(apps_v1, deployment)