STACK_NAME=EksHelloWorldStack

aws cloudformation describe-stack-resources --stack-name $STACK_NAME \
  --query "StackResources[?ResourceStatus=='DELETE_FAILED' && ResourceType=='AWS::EC2::Subnet'].[LogicalResourceId, PhysicalResourceId, ResourceStatus]" \
  --output table