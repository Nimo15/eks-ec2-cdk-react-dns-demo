from datetime import datetime

from aws_cdk import (
    Stack,
    Environment,
    aws_eks as eks,
    aws_route53 as route53,
)
from constructs import Construct
from .version import VERSION

lower_VERSION = VERSION.lower()


class EksReactAppStack(Stack):
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

        service_name = f"react-app-{lower_VERSION}"

        # React app on EKS via Kubernetes manifest
        eks.KubernetesManifest(
            self,
            f"ReactApp{VERSION}",
            cluster=cluster,
            manifest=[
                {
                    "apiVersion": "v1",
                    "kind": "Service",
                    "metadata": {"name": service_name},
                    "spec": {
                        "type": "LoadBalancer",
                        "ports": [{"port": 80, "targetPort": 80}],
                        "selector": {"app": service_name},
                    },
                },
                {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "metadata": {
                        "name": service_name,
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt": datetime.utcnow().isoformat()
                        },
                    },
                    "spec": {
                        "replicas": 2,
                        "selector": {"matchLabels": {"app": service_name}},
                        "template": {
                            "metadata": {"labels": {"app": service_name}},
                            "spec": {
                                "containers": [
                                    {
                                        "name": service_name,
                                        "image": "610739101347.dkr.ecr.us-east-1.amazonaws.com/react-vite-app:latest",
                                        "ports": [{"containerPort": 80}],
                                    }
                                ]
                            },
                        },
                    },
                },
            ],
        )

        # Hosted zone
        hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone", domain_name="tiphareth.com.br"
        )

        # Dynamic LoadBalancer hostname retrieval
        lb_hostname = eks.KubernetesObjectValue(
            self,
            f"ReactAppLB{VERSION}",
            cluster=cluster,
            object_type="service",
            object_name=service_name,
            object_namespace="default",
            json_path=".status.loadBalancer.ingress[0].hostname",
        )

        # Create a DNS CNAME record for the React app
        route53.CnameRecord(
            self,
            f"ReactAppDnsRecord{VERSION}",
            zone=hosted_zone,
            record_name=f"react-{lower_VERSION}",
            domain_name=lb_hostname.value,
        )
