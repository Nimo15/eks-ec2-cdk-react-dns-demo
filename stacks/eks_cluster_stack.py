from constructs import Construct
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ssm as ssm,
    aws_iam as iam,
    aws_eks as eks,
    CfnOutput,
    Aws,
)
from aws_cdk.lambda_layer_kubectl_v31 import KubectlV31Layer
from .version import VERSION

lower_VERSION = VERSION.lower()
env_name = f"poc{lower_VERSION}"


class EksClusterStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        eks_admin_rolename: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create VPC with public and private (egress) subnets
        self.vpc = ec2.Vpc(
            self,
            f"EksVpc{VERSION}",
            ip_addresses=ec2.IpAddresses.cidr("192.168.50.0/24"),
            max_azs=2,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public-Subnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=26,
                ),
                ec2.SubnetConfiguration(
                    name="Private-Subnet",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=26,
                ),
            ],
            nat_gateways=1,
        )

        # Store private subnet IDs into SSM Parameter Store
        priv_subnets = [subnet.subnet_id for subnet in self.vpc.private_subnets]
        for count, psub in enumerate(priv_subnets, start=1):
            ssm.StringParameter(
                self,
                f"private-subnet-{count}",
                string_value=psub,
                parameter_name=f"/{env_name}/private-subnet-{count}",
            )

        # IAM Role for EKS cluster admin
        admin_role_arn = f"arn:aws:iam::{Aws.ACCOUNT_ID}:role/{eks_admin_rolename}"
        eks_role = iam.Role(
            self,
            id=f"eksadmin{VERSION}",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("ec2.amazonaws.com"),
                iam.ArnPrincipal(admin_role_arn),
            ),
            role_name=f"eks-cluster-role-{lower_VERSION}",
            managed_policies=[
                iam.ManagedPolicy.from_managed_policy_arn(
                    self,
                    "CDKFullAccessEKSFargatePolicy",
                    f"arn:aws:iam::{Aws.ACCOUNT_ID}:policy/CDKFullAccessEKSFargatePolicy",
                )
            ],
        )

        # Instance profile for nodegroup
        iam.CfnInstanceProfile(
            self,
            f"InstanceProfile{VERSION}",
            roles=[eks_role.role_name],
            instance_profile_name=f"eks-cluster-role-{lower_VERSION}",
        )

        # Create EKS cluster
        self.cluster = eks.Cluster(
            self,
            f"EksCluster{VERSION}",
            cluster_name=f"eks-ec2-demo-{lower_VERSION}",
            version=eks.KubernetesVersion.V1_28,
            vpc=self.vpc,
            vpc_subnets=[
                ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)
            ],
            default_capacity=0,
            masters_role=eks_role,
            kubectl_layer=KubectlV31Layer(self, "KubectlLayer"),
        )

        # Grant kubectl access to IAM user
        deployer_user = iam.User.from_user_arn(
            self,
            f"DeployerUser{VERSION}",
            "arn:aws:iam::610739101347:user/cdk-deployer-eks",
        )

        self.cluster.aws_auth.add_user_mapping(
            deployer_user,
            username="admin-user",
            groups=["system:masters"],
        )

        # Add EC2-based nodegroup to EKS cluster
        nodegroup = self.cluster.add_nodegroup_capacity(
            f"NodeGroup{VERSION}",
            instance_types=[ec2.InstanceType("t2.medium")],
            disk_size=50,
            min_size=2,
            max_size=2,
            desired_size=2,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            capacity_type=eks.CapacityType.SPOT,
        )

        # ✅ Allow EKS nodes to pull images from ECR
        nodegroup.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonEC2ContainerRegistryReadOnly"
            )
        )

        # Outputs
        CfnOutput(
            self,
            f"EksClusterName{VERSION}",
            value=self.cluster.cluster_name,
            export_name=f"eksclustername-{lower_VERSION}",
        )
        CfnOutput(
            self,
            f"EksClusterRoleArn{VERSION}",
            value=eks_role.role_arn,
            export_name=f"eksclusteriamrole-{lower_VERSION}",
        )


class EksLambdaK8sStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, cluster: eks.Cluster, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # IAM Role for Lambda with Config and EKS permissions
        lambda_role = iam.Role(
            scope=self,
            id=f"LambdaEksRole{VERSION}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            role_name=f"cdk-lambda-role-eks-{lower_VERSION}",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
            inline_policies={
                "ConfigPutEvaluations": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "config:PutEvaluations",
                                "config:DescribeConfigRules",
                                "config:DescribeConfigRuleEvaluationStatus",
                            ],
                            resources=["*"],
                        )
                    ]
                ),
                "EKSDescribe": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "eks:ListNodegroups",
                                "eks:DescribeFargateProfile",
                                "eks:ListTagsForResource",
                                "eks:ListAddons",
                                "eks:DescribeAddon",
                                "eks:ListFargateProfiles",
                                "eks:DescribeNodegroup",
                                "eks:DescribeIdentityProviderConfig",
                                "eks:ListUpdates",
                                "eks:DescribeUpdate",
                                "eks:AccessKubernetesApi",
                                "eks:DescribeCluster",
                                "eks:ListClusters",
                                "eks:DescribeAddonVersions",
                                "eks:ListIdentityProviderConfigs",
                            ],
                            resources=["*"],
                        )
                    ]
                ),
            },
        )

        # Map Lambda role to RBAC group in Kubernetes
        cluster.aws_auth.add_role_mapping(
            role=lambda_role, groups=["lambda-read-only"], username="lambda"
        )

        # Create ClusterRole for Lambda
        cluster.add_manifest(
            f"LambdaClusterRole{VERSION}",
            {
                "apiVersion": "rbac.authorization.k8s.io/v1",
                "kind": "ClusterRole",
                "metadata": {
                    "annotations": {
                        "rbac.authorization.kubernetes.io/autoupdate": "true"
                    },
                    "name": "lambda-read-only",
                    "namespace": "default",
                },
                "rules": [
                    {
                        "apiGroups": [""],
                        "resources": ["*"],
                        "verbs": ["get", "list", "watch"],
                    },
                    {
                        "apiGroups": ["extensions"],
                        "resources": ["*"],
                        "verbs": ["get", "list", "watch"],
                    },
                    {
                        "apiGroups": ["apps"],
                        "resources": ["*"],
                        "verbs": ["get", "list", "watch"],
                    },
                    {
                        "apiGroups": ["networking.k8s.io"],
                        "resources": ["*"],
                        "verbs": ["get", "list", "watch"],
                    },
                ],
            },
        )

        # Bind the ClusterRole to the Lambda user
        cluster.add_manifest(
            f"LambdaClusterRoleBinding{VERSION}",
            {
                "kind": "ClusterRoleBinding",
                "apiVersion": "rbac.authorization.k8s.io/v1",
                "metadata": {
                    "name": "lambda-read-only-binding",
                    "namespace": "default",
                },
                "subjects": [
                    {
                        "kind": "User",
                        "name": "lambda",
                        "apiGroup": "rbac.authorization.k8s.io",
                    }
                ],
                "roleRef": {
                    "kind": "ClusterRole",
                    "name": "lambda-read-only",
                    "apiGroup": "rbac.authorization.k8s.io",
                },
            },
        )
