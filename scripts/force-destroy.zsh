#!/bin/zsh
source ~/.zshrc

STACK_NAME=EksHelloWorldStack

echo "🔴 Forcing deletion of stack: $STACK_NAME"

aws cloudformation delete-stack --stack-name $STACK_NAME
echo "🕒 Waiting for deletion to complete..."

aws cloudformation wait stack-delete-complete --stack-name $STACK_NAME
echo "✅ Stack deleted."

echo "📦 Running cleanup script..."
zsh ./scripts/check-cleanup.zsh