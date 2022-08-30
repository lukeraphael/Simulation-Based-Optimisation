from multiprocessing.pool import ThreadPool
from kubernetes import client, config
import numpy as np
import time

# import GA
from pymoo.algorithms.soo.nonconvex.ga import GA
from pymoo.optimize import minimize
from pymoo.core.problem import Problem

pool = ThreadPool(8)

def create_pod_object(deployment_name, app_name, image, num_replicas):
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

    '''
    create a deployment object with the following spec

    apiVersion: v1
    kind: Pod
    metadata:
    name: minifab
    spec:
    restartPolicy: OnFailure
    volumes:
        - name: task-pv-storage
        persistentVolumeClaim:
            claimName: task-pv-claim
    containers:
        - name: minifab
        image: minifab:local-latest
        imagePullPolicy: Never
        volumeMounts:
            # mountpath has to be same directory that the main program will save the output to
            - mountPath: "/minifab"
            name: task-pv-storage
    '''

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

    # # Create the specification of deployment
    # spec = client.V1DeploymentSpec(
    #     replicas=num_replicas, template=template, selector={
    #         "matchLabels":
    #         {"app": app_name}})

    # # Instantiate the deployment object
    # deployment = client.V1Deployment(
    #     api_version="apps/v1",
    #     kind="Deployment",
    #     metadata=client.V1ObjectMeta(name=deployment_name),
    #     spec=spec,
    # )

    # return pod object
    return client.V1Pod(
        api_version="v1",
        kind="Pod",
        metadata=template.metadata,
        spec=template.spec
    )


def create_pod(api, pod):
    # Create deployement
    api = client.CoreV1Api()
    resp = api.create_namespaced_pod(
        body=pod, namespace="default"
    )

    print(f"\n[INFO] pod {resp.metadata.name} created.\n")


# def update_deployment(api, deployment):
#     # Update container image
#     deployment.spec.template.spec.containers[0].image = "nginx:1.16.0"

#     # patch the deployment
#     resp = api.patch_namespaced_deployment(
#         name=DEPLOYMENT_NAME, namespace="default", body=deployment
#     )

#     print("\n[INFO] deployment's container image updated.\n")
#     print("%s\t%s\t\t\t%s\t%s" % ("NAMESPACE", "NAME", "REVISION", "IMAGE"))
#     print(
#         "%s\t\t%s\t%s\t\t%s\n"
#         % (
#             resp.metadata.namespace,
#             resp.metadata.name,
#             resp.metadata.generation,
#             resp.spec.template.spec.containers[0].image,
#         )
#     )


# def restart_deployment(api, deployment):
#     # update `spec.template.metadata` section
#     # to add `kubectl.kubernetes.io/restartedAt` annotation
#     deployment.spec.template.metadata.annotations = {
#         "kubectl.kubernetes.io/restartedAt": datetime.datetime.utcnow()
#         .replace(tzinfo=pytz.UTC)
#         .isoformat()
#     }

#     # patch the deployment
#     resp = api.patch_namespaced_deployment(
#         name=DEPLOYMENT_NAME, namespace="default", body=deployment
#     )

#     print("\n[INFO] deployment `nginx-deployment` restarted.\n")
#     print("%s\t\t\t%s\t%s" % ("NAME", "REVISION", "RESTARTED-AT"))
#     print(
#         "%s\t%s\t\t%s\n"
#         % (
#             resp.metadata.name,
#             resp.metadata.generation,
#             resp.spec.template.metadata.annotations,
#         )
#     )


def delete_pod(api, pod_name):
    # wait for minifab pods to complete
    v1 = client.CoreV1Api()
    pods = v1.list_namespaced_pod(namespace="default")

    while True:
        for pod in pods.items:
            if pod.status.phase != "Succeeded":
                print(f"[INFO] pod {pod.metadata.name} is not completed yet.")
                time.sleep(5)
                continue

        print(f"[INFO] all pods completed.")
        for pod in pods.items:
            try:
                print(pod.metadata.name)
                api_response = v1.read_namespaced_pod_log(name=pod.metadata.name , namespace='default')
                print(api_response)
            except client.ApiException as e:
                print('Found exception in reading the logs')
        break

    # Delete pods
    for pod in pods.items:
        print(f"[INFO] deleting pod {pod.metadata.name}")
        v1.delete_namespaced_pod(name=pod.metadata.name, namespace="default")
    # resp = api.delete_namespaced_pods(
    #     name=pod_name,
    #     namespace="default",
    #     body=client.V1DeleteOptions(
    #         propagation_policy="Foreground", grace_period_seconds=5
    #     ),
    # )

    # wait for the pods to be deleted
    while True:
        pods = v1.list_namespaced_pod(namespace="default")
        if len(pods.items) == 0:
            print("[INFO] all pods deleted.")
            break
        time.sleep(5)

# kubernetes api
config.load_kube_config()
apps_v1 = client.AppsV1Api()

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

        # Create a deployment object with client-python API.
        deployment_name = "minifab"

        deployment = create_pod_object(deployment_name, deployment_name, "minifab:local-latest", 1)

        create_pod(apps_v1, deployment)

        # check if status is completed


        delete_pod(apps_v1, deployment_name)

        # store the function values and return them.
        out["F"] = np.array(F)


problem = MyProblem()
res = minimize(problem, GA(), termination=("n_gen", 5), seed=1)
print('Threads:', res.exec_time)
print('Count:', problem.count)

# plt res.F
print(res.F)

# Create a deployment object with client-python API.
# deployment_name = "minifab"

# deployment = create_pod_object(deployment_name, deployment_name, "minifab:local-latest", 1)

# create_pod(apps_v1, deployment)