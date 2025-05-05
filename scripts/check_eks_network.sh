#!/bin/zsh
source ~/.zshrc
set -e

echo "[1] Getting VPC ID from EKS cluster..."
VPC_ID=$(aws eks describe-cluster --name eks-ec2-demo-v6 --query "cluster.resourcesVpcConfig.vpcId" --output text)

if [[ -z "$VPC_ID" ]]; then
  echo "[ERROR] Could not find VPC ID."
  exit 1
fi

echo "[✔] VPC ID: $VPC_ID"

echo "\n[2] Describing subnets with public IP mapping in VPC $VPC_ID..."
aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=${VPC_ID}" \
  --query "Subnets[*].[SubnetId, MapPublicIpOnLaunch]" \
  --output table

echo "\n[3] Listing security groups in VPC $VPC_ID..."
SG_IDS=($(aws ec2 describe-security-groups \
  --filters "Name=vpc-id,Values=${VPC_ID}" \
  --query "SecurityGroups[*].GroupId" \
  --output json | jq -r '.[]'))

echo "[✔] Found SGs: $SG_IDS"

echo "\n[4] Checking egress (outbound) rules for each SG:"
for sg in $SG_IDS; do
  echo "\n🔍 Security Group: $sg"
  aws ec2 describe-security-groups \
    --group-ids "$sg" \
    --query "SecurityGroups[*].IpPermissionsEgress" \
    --output table
done