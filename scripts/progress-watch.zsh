#!/bin/zsh

source ~/.zshrc

REGION=us-east-1
CLUSTER=fargate-demo

print_header() {
  echo "\n🔍 $1"
  echo "──────────────────────────────────────────────"
}

while true; do
  clear
  print_header "EKS Cluster Status"
  aws eks describe-cluster --region $REGION --name $CLUSTER \
    --query "cluster.{Name:name, Status:status, CreatedAt:createdAt, Endpoint:endpoint}" \
    --output table || echo "Cluster not found or not ready yet."

  print_header "Fargate Profile"
  aws eks list-fargate-profiles --cluster-name $CLUSTER --region $REGION \
    --output table || echo "No Fargate profiles (yet)."

#   print_header "Pods in all namespaces"
#   kubectl get pods -A --no-headers 2>/dev/null || echo "kubectl not ready or kubeconfig not set."
#
#   print_header "Recent Cluster Events"
#   kubectl get events -A --sort-by=.lastTimestamp | tail -n 20 2>/dev/null || echo "Waiting for events..."

  echo "\n🔄 Refreshing every 20 seconds — press Ctrl+C to stop."
  sleep 20
done
