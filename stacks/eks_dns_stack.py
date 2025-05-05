from aws_cdk import (
    Stack,
    aws_route53 as route53,
    aws_eks as eks,
    Environment,
)
from constructs import Construct
from .version import VERSION

lower_VERSION = VERSION.lower()


class EksDnsStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        cluster: eks.Cluster,
        env: Environment,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, env=env, **kwargs)

        # Hosted Zone for the domain (must already exist in Route 53)
        hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone", domain_name="tiphareth.com.br"
        )

        # Retrieve LoadBalancer hostname dynamically from the Service
        lb_hostname = eks.KubernetesObjectValue(
            self,
            f"HelloWorldLB{VERSION}",
            cluster=cluster,
            object_type="service",
            object_name=f"hello-world-{lower_VERSION}",
            object_namespace="default",
            json_path=".status.loadBalancer.ingress[0].hostname",
        )

        # Create a CNAME record pointing demo-v7.tiphareth.com.br → LoadBalancer hostname
        route53.CnameRecord(
            self,
            f"DnsRecordForHelloWorld{VERSION}",
            zone=hosted_zone,
            record_name=f"demo-{lower_VERSION}",  # e.g., demo-v7
            domain_name=lb_hostname.value,
        )
