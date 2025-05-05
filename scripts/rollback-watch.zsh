#!/bin/zsh
source ~/.zshrc
set -euo pipefail

STACK_NAME="FargateProfilesStack"
#
# rollback-watch:
# 	@$(AWS) cloudformation describe-stack-events \
# 		--stack-name $(STACK) \
# 		--region $(REGION) \
# 		--query "StackEvents[?ResourceStatus=='DELETE_IN_PROGRESS'].[ResourceStatus,ResourceType,LogicalResourceId,Timestamp]" \
# 		--output table

while true; do
  echo ""
  echo "🔍 Watching stack events for: $STACK_NAME"
  echo "────────────────────────────────────────────"

  aws cloudformation describe-stack-events --stack-name "$STACK_NAME" \
    --query "StackEvents[?ResourceStatus.ends_with(@, '_IN_PROGRESS') || ResourceStatus.ends_with(@, '_FAILED')].[ResourceStatus, ResourceType, LogicalResourceId, Timestamp]" \
    --output table || {
      echo "✅ Stack [$STACK_NAME] no longer exists. Exiting watch."
      break
    }

  sleep 10
done