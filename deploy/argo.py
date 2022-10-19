from pprint import pprint
from requests_futures.sessions import FuturesSession

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
from argo_workflows.model.toleration import Toleration
from argo_workflows.model.affinity import Affinity
from argo_workflows.model.node_affinity import NodeAffinity
from argo_workflows.model.node_selector import NodeSelector
from argo_workflows.model.node_selector_term import NodeSelectorTerm
from argo_workflows.model.node_selector_requirement import NodeSelectorRequirement

from typing import List

configuration = argo_workflows.Configuration(host="https://20.195.56.193:2746")
configuration.verify_ssl = False

def submit_workflow(app_name: str, pv: str, pv_claim: str, image: str, mount_path: str, command: List[str], namespace: str, token: str) -> None:
    configuration.api_key["BearerToken"] = token
    print(configuration.api_key["BearerToken"])
    manifest = IoArgoprojWorkflowV1alpha1Workflow(
        metadata=ObjectMeta(generate_name=f"{app_name}-"),
        spec=IoArgoprojWorkflowV1alpha1WorkflowSpec(
            entrypoint='entrypoint',
            volumes= [
                Volume(
                    name=pv,
                    persistent_volume_claim=PersistentVolumeClaimVolumeSource(
                        claim_name=pv_claim),
                    )
            ],
            templates=[
                IoArgoprojWorkflowV1alpha1Template(
                    name='entrypoint',
                    container=Container(
                        image=image, 
                        command=command, 
                        volume_mounts=[
                            VolumeMount(
                                name=pv,
                                mount_path=mount_path,
                            )
                        ],
                    ),
                    tolerations=[Toleration(
                        effect="NoSchedule", 
                        key="kubernetes.azure.com/scalesetpriority",
                        operator="Equal",
                        value="spot",
                    )],
                    affinity=Affinity(
                        node_affinity=NodeAffinity(
                            required_during_scheduling_ignored_during_execution=NodeSelector(
                                node_selector_terms=[NodeSelectorTerm(
                                    match_expressions=[NodeSelectorRequirement(
                                        key="kubernetes.azure.com/scalesetpriority",
                                        operator="In",
                                        values=["spot"],
                                    )]
                                )]
                            )
                        )        
                    )                      
                )
            ]
        )
    )

    api_client = argo_workflows.ApiClient(configuration)
    api_instance = workflow_service_api.WorkflowServiceApi(api_client)
    api_response = api_instance.create_workflow(
        namespace=namespace,
        body=IoArgoprojWorkflowV1alpha1WorkflowCreateRequest(workflow=manifest),
        _check_return_type=False,
        
        )

    pprint(api_response)
 
 
def submit_yaml():
    configuration = argo_workflows.Configuration(host="https://20.195.56.193:31847")
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

def submit_json(app_name: str, pv: str, pv_claim: str, image: str, mount_path: str, command: List[str], namespace: str, token: str, session: FuturesSession) -> None:

    headers = {
        # Already added when you pass json= but not when you pass data=
        # 'content-type': 'application/json',
        'Authorization': token,
    }

    json_data = {
        'namespace': namespace,
        'serverDryRun': False,
        'workflow': {
            'metadata': {
                'generateName': f"{app_name}-",
                'namespace': namespace,
                'labels': {
                    'workflows.argoproj.io/completed': 'false',
                },
            },
            'spec': {
                'templates': [
                    {
                        'name': 'entrypoint',
                        'container': {
                            'name': '',
                            'image': image,
                            'command': command,
                            'volumeMounts': [
                                {
                                    'name': pv,
                                    'mountPath': mount_path,
                                },
                            ],
                        },
                        'volumes': [
                            {
                                'name': pv,
                                'persistentVolumeClaim': {
                                    'claimName': pv_claim,
                                },
                            },
                        ],
                        'nodeSelector': {
                            'kubernetes.io/os': 'linux',
                        },
                        'tolerations': [
                            {
                                'key': 'kubernetes.azure.com/scalesetpriority',
                                'operator': 'Equal',
                                'value': 'spot',
                                'effect': 'NoSchedule',
                            },
                        ],
                    },
                ],
                'entrypoint': 'entrypoint',
            },
        },
    }

    # asynchronous post request
    endpoint = 'https://20.195.56.193:2746/api/v1/workflows/argo' 
    session.post(endpoint, headers=headers, json=json_data, verify=False) 
    # response = requests.post('https://20.195.56.193:2746/api/v1/workflows/argo', headers=headers, json=json_data, verify=False)