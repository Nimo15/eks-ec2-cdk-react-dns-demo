# Makefile - EKS CDK Stack Utilities (Sanitized)

REGION ?= us-east-1
ACCOUNT_ID ?= YOUR_ACCOUNT_ID
TRUST_USER ?= cdk-deployer-eks
TRUST_ARN := arn:aws:iam::$(ACCOUNT_ID):user/$(TRUST_USER)
AWS ?= op plugin run -- aws
VERSION ?= $(or $(VERSION_ENV),V1)
STACK_NAME ?= $(or $(STACK_ENV),EksClusterStack)
CLUSTER_NAME ?= $(or $(STACK_NAME_ENV),eks-ec2-demo)
STACK := $(STACK_NAME)$(VERSION)
CLUSTER := $(CLUSTER_NAME)-$(shell echo $(VERSION) | tr A-Z a-z)
CDK_OUT := cdk.out.$(VERSION)

echo-stack:
	@echo "Stack: $(STACK)"

echo-cluster:
	@echo "Cluster: $(CLUSTER)"

echo: echo-stack echo-cluster

ls-stacks:
	@$(AWS) cloudformation list-stacks \
		--query "StackSummaries[?StackStatus!='DELETE_COMPLETE'].[StackName, StackStatus]" \
		--output table

ls-clusters:
	@$(AWS) eks list-clusters --output table

ls-all: ls-stacks ls-clusters

get-cluster-vpc-id:
	@$(AWS) eks describe-cluster --name $(CLUSTER) --query "cluster.resourcesVpcConfig.vpcId" --output text

get-vpc-subnets-id:
	@$(AWS) eks describe-cluster --name $(CLUSTER) --query "cluster.resourcesVpcConfig.vpcId" --output text

bootstrap:
	@echo "Bootstrapping CDK with trust for $(TRUST_ARN)..."
	cdk bootstrap \
		--output $(CDK_OUT) \
		--cloudformation-execution-policies arn:aws:iam::aws:policy/AdministratorAccess \
		--trust $(TRUST_ARN) \
		aws://$(ACCOUNT_ID)/$(REGION)

kubeconfig:
	aws_wrapper eks update-kubeconfig --region $(REGION) --name $(CLUSTER)

pods:
	kubectl get pods -A -o wide

events:
	kubectl get events -A --watch

ingress:
	kubectl get ingress -n dev

certs:
	kubectl get certificate -A

certs-describe:
	kubectl describe certificate demo-tls -n dev

dns:
	$(AWS) route53 list-resource-record-sets \
		--hosted-zone-id $$($(AWS) route53 list-hosted-zones \
		--query "HostedZones[?Name=='tiphareth.com.br.'].Id" --output text) \
		--query "ResourceRecordSets[?starts_with(Name, 'demo.tiphareth.com.br')]" \
		--output table

watch-events:
	@$(AWS) cloudformation describe-stack-events \
		--stack-name EksNodegroupStackV6 \
		--region $(REGION) \
		--query "StackEvents[].[ResourceStatus,ResourceType,LogicalResourceId,Timestamp]" \
		--output table

rollback-watch:
	@zsh ./scripts/rollback-watch.zsh

rollback-errors:
	@$(AWS) cloudformation describe-stack-events \
		--stack-name $(STACK) \
		--region $(REGION) \
		--query "StackEvents[?ResourceStatus=='CREATE_FAILED' || ResourceStatus=='DELETE_FAILED' || ResourceStatus=='ROLLBACK_IN_PROGRESS' || ResourceStatus=='ROLLBACK_COMPLETE' || ResourceStatus=='DELETE_IN_PROGRESS'].[ResourceStatus,ResourceType,LogicalResourceId,Timestamp]" \
		--output table

destroy:
	cdk destroy $(STACK) --output $(CDK_OUT)

deploy-first:
	@echo ""
	@echo "cdk deploy $(STACK) --concurrency 1 --exclusively --output $(CDK_OUT)"

deploy:
	cdk deploy --all --output $(CDK_OUT)

synth:
	cdk synth --output $(CDK_OUT)

progress:
	@./scripts/progress-watch.zsh

force-destroy:
	@zsh ./scripts/force-destroy.zsh

stay-awake:
	@echo "🟡 Keeping the system awake. Press Ctrl+C to stop."
	@pmset noidle

watch-deploy:
	watch -n 5 "$(AWS) cloudformation describe-stack-events --stack-name $(STACK) \
	  --query 'StackEvents[?ResourceStatus==\`CREATE_IN_PROGRESS\` || ResourceStatus==\`UPDATE_IN_PROGRESS\`]' \
	  --output json | jq -r '.[] | [.LogicalResourceId, .ResourceType, .ResourceStatus, .Timestamp] | map(tostring | .[0:40]) | @tsv'"

cluster-status:
	$(AWS) eks describe-cluster --name $(CLUSTER) --query "cluster.status"

diff:
	cdk diff --all --output $(CDK_OUT)

describe-stack-remaining:
	@echo "[INFO] Listing non-deleted resources in stack: $(STACK)"
	@$(AWS) cloudformation describe-stack-resources \
	  --stack-name $(STACK) \
	  --query "StackResources[?ResourceStatus != 'DELETE_COMPLETE'].[LogicalResourceId, PhysicalResourceId, ResourceType, ResourceStatus]" \
	  --output table 2>/dev/null || echo "[DONE] Stack '$(STACK)' no longer exists."