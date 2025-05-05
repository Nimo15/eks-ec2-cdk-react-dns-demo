from aws_cdk import (
    Stack,
    Environment,
    aws_eks as eks,
)
from constructs import Construct
from .version import VERSION

lower_VERSION = VERSION.lower()


class EksAppStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        cluster: eks.Cluster,
        env: Environment,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, env=env, **kwargs)

        eks.KubernetesManifest(
            self,
            f"HelloWorldApp{VERSION}",
            cluster=cluster,
            manifest=[
                {
                    "apiVersion": "v1",
                    "kind": "Service",
                    "metadata": {"name": f"hello-world-{lower_VERSION}"},
                    "spec": {
                        "type": "LoadBalancer",
                        "ports": [{"port": 80, "targetPort": 80}],
                        "selector": {"app": f"hello-world-{lower_VERSION}"},
                    },
                },
                {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "metadata": {"name": f"hello-world-{lower_VERSION}"},
                    "spec": {
                        "replicas": 2,
                        "selector": {
                            "matchLabels": {"app": f"hello-world-{lower_VERSION}"}
                        },
                        "template": {
                            "metadata": {
                                "labels": {"app": f"hello-world-{lower_VERSION}"}
                            },
                            "spec": {
                                "containers": [
                                    {
                                        "name": f"hello-world-{lower_VERSION}",
                                        "image": "nginxdemos/hello",
                                        "ports": [{"containerPort": 80}],
                                    }
                                ]
                            },
                        },
                    },
                },
            ],
        )
