import boto3
import time
import sys
from botocore.exceptions import ClientError
from keysentinel import retrieve_and_decrypt_fields

STACK_NAME = "EksClusterStackV5"


def load_aws_session_from_keysentinel():
    fields = retrieve_and_decrypt_fields("My AWS Token - eks-deployer")
    return boto3.Session(
        aws_access_key_id=fields["aws_access_key_id"],
        aws_secret_access_key=fields["aws_secret_access_key"],
        region_name=fields.get("region", "us-east-1"),
    )


session = load_aws_session_from_keysentinel()
cf = session.client("cloudformation")
ec2 = session.client("ec2")
elb = session.client("elb")  # Classic ELBs


def get_failed_subnets_from_stack(stack_name: str):
    print(f"[INFO] Searching DELETE_FAILED subnets in stack: {stack_name}")
    response = cf.describe_stack_resources(StackName=stack_name)
    subnets = []
    for resource in response["StackResources"]:
        if (
            resource["ResourceStatus"] == "DELETE_FAILED"
            and resource["ResourceType"] == "AWS::EC2::Subnet"
        ):
            subnet_id = resource["PhysicalResourceId"]
            subnets.append(subnet_id)
    return subnets


def terminate_instance(instance_id):
    print(f"[INFO] Terminating EC2 instance: {instance_id}")
    try:
        ec2.terminate_instances(InstanceIds=[instance_id])
        print("[WAIT] Waiting for instance to terminate...")
        waiter = ec2.get_waiter("instance_terminated")
        waiter.wait(InstanceIds=[instance_id])
        print(f"[DONE] Instance {instance_id} terminated.")
    except Exception as e:
        print(f"[ERROR] Could not terminate instance {instance_id}: {e}")


def delete_nat_gateways(subnet_id):
    print(f"[INFO] Checking for NAT Gateways in {subnet_id}...")
    response = ec2.describe_nat_gateways(
        Filters=[{"Name": "subnet-id", "Values": [subnet_id]}]
    )
    for nat in response.get("NatGateways", []):
        nat_id = nat["NatGatewayId"]
        print(f"[DELETE] NAT Gateway: {nat_id}")
        ec2.delete_nat_gateway(NatGatewayId=nat_id)
        while True:
            nat_status = ec2.describe_nat_gateways(NatGatewayIds=[nat_id])
            state = nat_status["NatGateways"][0]["State"]
            if state == "deleted":
                break
            print(f"[WAIT] NAT Gateway {nat_id} still in {state} state...")
            time.sleep(5)


def delete_network_interfaces(subnet_id):
    print(f"[INFO] Checking for network interfaces in {subnet_id}...")
    response = ec2.describe_network_interfaces(
        Filters=[{"Name": "subnet-id", "Values": [subnet_id]}]
    )
    for eni in response["NetworkInterfaces"]:
        eni_id = eni["NetworkInterfaceId"]
        description = eni.get("Description", "")
        attachment = eni.get("Attachment")

        if "ELB" in description:
            print(
                f"[INFO] ENI {eni_id} is associated with an ELB ({description}). Attempting to delete related ELB."
            )
            try:
                elbs = elb.describe_load_balancers()
                for lb in elbs["LoadBalancerDescriptions"]:
                    if subnet_id in lb.get("Subnets", []):
                        lb_name = lb["LoadBalancerName"]
                        print(f"[DELETE] Deleting Classic ELB: {lb_name}")
                        elb.delete_load_balancer(LoadBalancerName=lb_name)
                        time.sleep(10)
                        break
            except Exception as e:
                print(f"[WARN] Failed to delete ELB for ENI {eni_id}: {e}")

        if attachment:
            instance_id = attachment.get("InstanceId")
            if instance_id:
                print(f"[INFO] ENI {eni_id} is attached to instance {instance_id}.")
                terminate_instance(instance_id)
                time.sleep(5)
            else:
                try:
                    ec2.detach_network_interface(
                        AttachmentId=attachment["AttachmentId"], Force=True
                    )
                    time.sleep(2)
                except Exception as e:
                    print(f"[WARN] Could not detach ENI {eni_id}: {e}")
                    continue

        print(f"[DELETE] ENI: {eni_id}")
        try:
            ec2.delete_network_interface(NetworkInterfaceId=eni_id)
        except ClientError as e:
            if "InvalidNetworkInterfaceID.NotFound" in str(e):
                print(f"[SKIP] ENI {eni_id} already deleted.")
            else:
                print(f"[WARN] Could not delete ENI {eni_id}: {e}")


def delete_route_table_associations(subnet_id):
    print(f"[INFO] Checking route table associations in {subnet_id}...")
    rts = ec2.describe_route_tables()["RouteTables"]
    for rt in rts:
        for assoc in rt.get("Associations", []):
            if assoc.get("SubnetId") == subnet_id and not assoc.get("Main", False):
                print(
                    f"[DELETE] Route Table Association: {assoc['RouteTableAssociationId']}"
                )
                ec2.disassociate_route_table(
                    RouteTableAssociationId=assoc["RouteTableAssociationId"]
                )


def delete_subnet(subnet_id):
    print(f"[DELETE] Subnet: {subnet_id}")
    try:
        ec2.delete_subnet(SubnetId=subnet_id)
        print("[SUCCESS] Subnet deleted.")
    except ClientError as e:
        if "InvalidSubnetID.NotFound" in str(e):
            print(f"[SKIP] Subnet {subnet_id} already deleted.")
        else:
            print(f"[ERROR] Failed to delete subnet {subnet_id}: {e}")


if __name__ == "__main__":
    subnets = get_failed_subnets_from_stack(STACK_NAME)
    if not subnets:
        print("[DONE] No DELETE_FAILED subnets found.")
        sys.exit(0)

    print(f"[INFO] Subnets to process: {subnets}")
    for subnet_id in subnets:
        print(f"\n=== Processing {subnet_id} ===")
        delete_nat_gateways(subnet_id)
        delete_network_interfaces(subnet_id)
        delete_route_table_associations(subnet_id)
        delete_subnet(subnet_id)
