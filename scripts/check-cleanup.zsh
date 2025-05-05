source ~/.zshrc

REGION=us-east-1
STACK_NAME=EksClusterStackV3
DOMAIN=tiphareth.com.br
ZONE_ID=$(aws route53 list-hosted-zones \
  --query "HostedZones[?Name=='${DOMAIN}.'].Id" --output text)

print_header() {
  echo "\n🔍 $1"
  echo "────────────────────────────────────────────────────"
}

print_header "Checking CloudFormation stack"
aws cloudformation describe-stacks \
  --region $REGION \
  --query "Stacks[?StackName=='$STACK_NAME']" || echo "✅ Stack $STACK_NAME not found."

print_header "Checking EKS clusters"
aws eks list-clusters --region $REGION

print_header "Checking Load Balancers"
aws elbv2 describe-load-balancers --region $REGION \
  --query "LoadBalancers[?contains(DNSName, '$DOMAIN') || contains(DNSName, 'nginx')]" --output table

print_header "Checking ECR repos"
aws ecr describe-repositories --region $REGION \
  --query "repositories[?starts_with(repositoryName, 'cdk-hnb659fds')]" --output table

print_header "Checking SSM parameter version"
aws ssm get-parameter --name /cdk-bootstrap/hnb659fds/version --region $REGION || echo "✅ Parameter not found."

print_header "Checking Lambda functions related to CDK/EKS"
aws lambda list-functions --region $REGION \
  --query "Functions[?contains(FunctionName, 'cdk') || contains(FunctionName, 'eks')]" --output table

print_header "Checking Route 53 DNS Records"
if [[ -n "$ZONE_ID" ]]; then
  aws route53 list-resource-record-sets \
    --hosted-zone-id $ZONE_ID \
    --query "ResourceRecordSets[?contains(Name, '$DOMAIN')]" --output table
else
  echo "❌ Hosted zone for $DOMAIN not found."
fi

echo "\n✅ Cleanup check complete."