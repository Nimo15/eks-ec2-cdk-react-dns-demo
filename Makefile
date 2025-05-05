# Makefile - EKS CDK Stack Utilities

REGION=us-east-1
AWS=op plugin run -- aws
ACCOUNT_ID := 610739101347
TRUST_ARN := arn:aws:iam::$(ACCOUNT_ID):user/cdk-deployer-eks
CDK_OUT = cdk.out.$(VERSION)

VERSION = $(or $(VERSION_ENV),V1)
STACK_NAME ?= $(or $(STACK_ENV),EksClusterStack)
CLUSTER_NAME ?= $(or $(STACK_NAME_ENV),eks-ec2-demo)
STACK = $(STACK_NAME)$(VERSION)
CLUSTER= $(CLUSTER_NAME)-$(shell echo $(VERSION) | tr A-Z a-z)

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

# Atualiza o kubeconfig com o nome do cluster (ajuste se necessário)
kubeconfig:
	aws_wrapper eks update-kubeconfig --region $(REGION) --name $(CLUSTER)

# Mostra todos os pods em todos os namespaces
pods:
	kubectl get pods -A -o wide

# Mostra todos os eventos em tempo real
events:
	kubectl get events -A --watch

# Mostra os ingressos no namespace dev
ingress:
	kubectl get ingress -n dev

# Mostra os certificados TLS
certs:
	kubectl get certificate -A

# Mostra detalhes do certificado demo-tls no namespace dev
certs-describe:
	kubectl describe certificate demo-tls -n dev

# Mostra os registros DNS criados pelo external-dns
dns:
	$(AWS) route53 list-resource-record-sets \
		--hosted-zone-id $$($(AWS) route53 list-hosted-zones \
		--query "HostedZones[?Name=='tiphareth.com.br.'].Id" --output text) \
		--query "ResourceRecordSets[?starts_with(Name, 'demo.tiphareth.com.br')]" \
		--output table

watch-events:
	@$(AWS) cloudformation describe-stack-events \
		--stack-name EksNodegroupStackV6 \
		--region us-east-1 \
		--query "StackEvents[].[ResourceStatus,ResourceType,LogicalResourceId,Timestamp]" \
		--output table

rollback-watch:
	@zsh ./scriptds/rollback-watch.zsh

rollback-errors:
	@$(AWS) cloudformation describe-stack-events \
		--stack-name $(STACK) \
		--region $(REGION) \
		--query "StackEvents[?ResourceStatus=='CREATE_FAILED' || ResourceStatus=='DELETE_FAILED' || ResourceStatus=='ROLLBACK_IN_PROGRESS' || ResourceStatus=='ROLLBACK_COMPLETE' || ResourceStatus=='DELETE_IN_PROGRESS'].[ResourceStatus,ResourceType,LogicalResourceId,Timestamp]" \
		--output table


# Destroi uma stack específica
destroy:
	cdk destroy $(STACK) --output $(CDK_OUT)

deploy-first:
	@echo ""
	@echo "cdk deploy $(STACK) --concurrency 1 --exclusively --output $(CDK_OUT)"

# Faz deploy de todas as stacks
deploy:
	cdk deploy --all --output $(CDK_OUT)

# Faz synth localmente (prévia do que será criado)
synth:
	cdk synth --output $(CDK_OUT)

# Monitor progress of EKS cluster deployment
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

# watch-deploy:
# 	watch -n 5 "$(AWS) cloudformation describe-stack-events --stack-name $(STACK) \
# 	  --query 'StackEvents[?ResourceStatus==\`CREATE_IN_PROGRESS\` || ResourceStatus==\`UPDATE_IN_PROGRESS\`]' \
# 	  --output text | cut -f1-4 | cut -c1-140"

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