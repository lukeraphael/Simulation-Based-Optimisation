from pprint import pprint

import argo_workflows
import yaml
from argo_workflows.api import workflow_service_api
from argo_workflows.model.container import Container
from argo_workflows.model.volume import Volume
from argo_workflows.model.volume_mount import VolumeMount
from argo_workflows.model.persistent_volume_claim_volume_source import PersistentVolumeClaimVolumeSource
from argo_workflows.model.io_argoproj_workflow_v1alpha1_template import IoArgoprojWorkflowV1alpha1Template
from argo_workflows.model.io_argoproj_workflow_v1alpha1_workflow import IoArgoprojWorkflowV1alpha1Workflow
from argo_workflows.model.io_argoproj_workflow_v1alpha1_workflow_create_request import (
    IoArgoprojWorkflowV1alpha1WorkflowCreateRequest,
)
from argo_workflows.model.io_argoproj_workflow_v1alpha1_workflow_spec import (
    IoArgoprojWorkflowV1alpha1WorkflowSpec,
)
from argo_workflows.model.object_meta import ObjectMeta

configuration = argo_workflows.Configuration(host="https://127.0.0.1:2746")
configuration.verify_ssl = False

def submit_workflow(input_file: str, output_file: str) -> None:

    manifest = IoArgoprojWorkflowV1alpha1Workflow(
        metadata=ObjectMeta(generate_name='minifab-argo-test'),
        spec=IoArgoprojWorkflowV1alpha1WorkflowSpec(
            entrypoint='whalesay',
            volumes= [
                Volume(
                    name='argo-pv-volume',
                    persistent_volume_claim=PersistentVolumeClaimVolumeSource(
                        claim_name='argo-pv-claim'),
                    )
            ],
            templates=[
                IoArgoprojWorkflowV1alpha1Template(
                    name='whalesay',
                    container=Container(
                        image='lukeraphael/minifab', 
                        command=['python3', './main.py', input_file, output_file], 
                        volume_mounts=[
                            VolumeMount(
                                name='argo-pv-volume',
                                mount_path='/minifab/',
                            )
                        ]                       
                    ),
                )
            ]
        )
    )

    api_client = argo_workflows.ApiClient(configuration)
    api_instance = workflow_service_api.WorkflowServiceApi(api_client)

    api_instance.create_workflow(
        namespace='argo',
        body=IoArgoprojWorkflowV1alpha1WorkflowCreateRequest(workflow=manifest),
        _check_return_type=False)
 
 
def submit_yaml():
    configuration = argo_workflows.Configuration(host="https://127.0.0.1:2746")
    configuration.verify_ssl = False

    f = open("output.yaml", "r")
    manifest = yaml.safe_load(f)

    api_client = argo_workflows.ApiClient(configuration)
    api_instance = workflow_service_api.WorkflowServiceApi(api_client)
    api_response = api_instance.create_workflow(
        namespace="argo",
        body=IoArgoprojWorkflowV1alpha1WorkflowCreateRequest(workflow=manifest, _check_type=False),
        _check_return_type=False)
    pprint(api_response)