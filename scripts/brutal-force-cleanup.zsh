#!/bin/zsh

source ~/.zshrc
set -euo pipefail

print_header() {
  echo ""
  echo "🔻 $1"
  echo "────────────────────────────────────────────"
}

# Define target stack name
STACK_NAME="EksClusterStackV5"

print_header "Fetching VPCs tagged with stack name: $STACK_NAME"
VPCS=("${(@f)$(aws ec2 describe-vpcs --query "Vpcs[?Tags[?Key=='aws:cloudformation:stack-name' && Value=='$STACK_NAME']].VpcId" --output text)}")

for VPC_ID in "${VPCS[@]}"; do
  echo "➡️  Processing VPC: $VPC_ID"

  print_header "Deleting subnets"
  SUBNET_IDS=("${(z)$(aws ec2 describe-subnets --filters Name=vpc-id,Values=$VPC_ID --query 'Subnets[].SubnetId' --output text)}")
  for SUBNET_ID in "${SUBNET_IDS[@]}"; do
    echo "  - Deleting subnet: $SUBNET_ID"
    aws ec2 delete-subnet --subnet-id "$SUBNET_ID" || true
  done

  print_header "Detaching and deleting route tables"
  RTB_IDS=("${(@f)$(aws ec2 describe-route-tables --filters Name=vpc-id,Values=$VPC_ID --query 'RouteTables[].RouteTableId' --output text)}")
  for RTB_ID in "${RTB_IDS[@]}"; do
    MAIN=$(aws ec2 describe-route-tables --route-table-ids "$RTB_ID" --query 'RouteTables[0].Associations[0].Main' --output text)
    if [[ "$MAIN" == "False" ]]; then
      echo "  - Deleting route table: $RTB_ID"
      aws ec2 delete-route-table --route-table-id "$RTB_ID"
    fi
  done

  print_header "Deleting security groups (non-default)"
  SG_IDS=("${(@f)$(aws ec2 describe-security-groups --filters Name=vpc-id,Values=$VPC_ID --query 'SecurityGroups[?GroupName!=`default`].GroupId' --output text)}")
  for SG_ID in "${SG_IDS[@]}"; do
    echo "  - Deleting security group: $SG_ID"
    aws ec2 delete-security-group --group-id "$SG_ID"
  done

  print_header "Detaching Internet Gateways"
  IGWS=("${(@f)$(aws ec2 describe-internet-gateways --query 'InternetGateways[*].[InternetGatewayId,VpcAttachments[0].VpcId]' --output text)}")
  for IGW in "${IGWS[@]}"; do
    IGW_ID="${IGW%%$'\t'*}"
    IGW_VPC="${IGW##*$'\t'}"
    if [[ "$IGW_VPC" == "$VPC_ID" ]]; then
      echo "  - Detaching and deleting IGW: $IGW_ID"
      aws ec2 detach-internet-gateway --internet-gateway-id "$IGW_ID" --vpc-id "$VPC_ID" || true
      aws ec2 delete-internet-gateway --internet-gateway-id "$IGW_ID"
    fi
  done

  print_header "Deleting VPC"
  echo "  - Deleting VPC: $VPC_ID"
  aws ec2 delete-vpc --vpc-id "$VPC_ID"
done

echo "✅ Brutal force cleanup complete."