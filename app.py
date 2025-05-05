import os
import aws_cdk as cdk
from stacks import (
    EksClusterStack,
    EksDnsStack,
    EksReactAppStack,
    EksAppStack,
)

from stacks.version import VERSION

env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT", "610739101347"),
    region=os.getenv("CDK_DEFAULT_REGION", "us-east-1"),
)

eks_admin_rolename = "cdk-deployer-eks-admin"

app = cdk.App()

eks_stack = EksClusterStack(
    scope=app,
    construct_id=f"EksClusterStack{VERSION}",
    eks_admin_rolename=eks_admin_rolename,
    env=env,
)

app_stack = EksAppStack(
    app,
    f"EksAppStack{VERSION}",
    cluster=eks_stack.cluster,
    env=env,
)
app_stack.add_dependency(eks_stack)

dns_stack = EksDnsStack(
    scope=app,
    construct_id=f"EksDnsStack{VERSION}",
    cluster=eks_stack.cluster,
    env=env,
)

dns_stack.add_dependency(eks_stack)
dns_stack.add_dependency(app_stack)

react_app_stack = EksReactAppStack(
    app,
    f"EksReactAppStack{VERSION}",
    cluster=eks_stack.cluster,
    env=env,
)
app_stack.add_dependency(eks_stack)

app.synth()
