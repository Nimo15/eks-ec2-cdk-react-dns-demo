import boto3
from botocore.exceptions import ClientError
from keysentinel import retrieve_and_decrypt_fields

VPC_ID = "vpc-00beb5856fd1ca4ac"


def load_session():
    fields = retrieve_and_decrypt_fields("My AWS Token - eks-deployer")
    return boto3.Session(
        aws_access_key_id=fields["aws_access_key_id"],
        aws_secret_access_key=fields["aws_secret_access_key"],
        region_name=fields.get("region", "us-east-1"),
    )


session = load_session()
ec2 = session.client("ec2")


def release_elastic_ips():
    eips = ec2.describe_addresses().get("Addresses", [])
    for eip in eips:
        allocation_id = eip.get("AllocationId")
        assoc_id = eip.get("AssociationId")

        if not allocation_id:
            continue  # skip entries without allocation id

        if assoc_id:
            print(
                f"[SKIP] EIP {allocation_id} still associated (AssociationId: {assoc_id})"
            )
            continue

        print(f"[DELETE] Releasing EIP: {allocation_id}")
        try:
            ec2.release_address(AllocationId=allocation_id)
        except ClientError as e:
            if "AuthFailure" in str(e):
                print(
                    f"[SKIP] Cannot release {allocation_id} — not owned or managed: {e}"
                )
            elif "InvalidAllocationID.NotFound" in str(e):
                print(f"[SKIP] Allocation {allocation_id} already deleted.")
            else:
                print(f"[WARN] Could not release EIP {allocation_id}: {e}")


def delete_vpc_endpoints(vpc_id):
    eps = ec2.describe_vpc_endpoints(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])[
        "VpcEndpoints"
    ]
    for ep in eps:
        ep_id = ep["VpcEndpointId"]
        print(f"[DELETE] Deleting VPC endpoint: {ep_id}")
        try:
            ec2.delete_vpc_endpoints(VpcEndpointIds=[ep_id])
        except Exception as e:
            print(f"[WARN] Could not delete VPC endpoint {ep_id}: {e}")


def delete_internet_gateways(vpc_id):
    igws = ec2.describe_internet_gateways(
        Filters=[{"Name": "attachment.vpc-id", "Values": [vpc_id]}]
    )["InternetGateways"]
    for igw in igws:
        igw_id = igw["InternetGatewayId"]
        print(f"[DELETE] Detaching and deleting IGW: {igw_id}")
        try:
            ec2.detach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
            ec2.delete_internet_gateway(InternetGatewayId=igw_id)
        except Exception as e:
            print(f"[WARN] Failed IGW {igw_id}: {e}")


def delete_route_tables(vpc_id):
    rts = ec2.describe_route_tables(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])[
        "RouteTables"
    ]
    for rt in rts:
        associations = rt.get("Associations", [])
        for assoc in associations:
            if not assoc.get("Main", False):
                assoc_id = assoc["AssociationId"]
                print(f"[DELETE] Disassociating route table association: {assoc_id}")
                try:
                    ec2.disassociate_route_table(AssociationId=assoc_id)
                except Exception as e:
                    print(f"[WARN] Could not disassociate {assoc_id}: {e}")
        if not any(a.get("Main", False) for a in associations):
            rt_id = rt["RouteTableId"]
            print(f"[DELETE] Deleting route table: {rt_id}")
            try:
                ec2.delete_route_table(RouteTableId=rt_id)
            except Exception as e:
                print(f"[WARN] Could not delete route table {rt_id}: {e}")


def delete_subnets(vpc_id):
    subnets = ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])[
        "Subnets"
    ]
    for subnet in subnets:
        subnet_id = subnet["SubnetId"]
        print(f"[DELETE] Deleting subnet: {subnet_id}")
        try:
            ec2.delete_subnet(SubnetId=subnet_id)
        except Exception as e:
            print(f"[WARN] Could not delete subnet {subnet_id}: {e}")


def delete_network_acls(vpc_id):
    acls = ec2.describe_network_acls(Filters=[{"Name": "vpc-id", "Values": [vpc_id]}])[
        "NetworkAcls"
    ]
    for acl in acls:
        if acl["IsDefault"]:
            print(f"[SKIP] Default NACL: {acl['NetworkAclId']}")
            continue
        acl_id = acl["NetworkAclId"]
        print(f"[DELETE] Deleting NACL: {acl_id}")
        try:
            ec2.delete_network_acl(NetworkAclId=acl_id)
        except Exception as e:
            print(f"[WARN] Could not delete NACL {acl_id}: {e}")


def delete_security_groups(vpc_id):
    sgs = ec2.describe_security_groups(
        Filters=[{"Name": "vpc-id", "Values": [vpc_id]}]
    )["SecurityGroups"]
    for sg in sgs:
        sg_id = sg["GroupId"]
        if sg["GroupName"] == "default":
            print(f"[SKIP] Default SG: {sg_id}")
            continue
        print(f"[DELETE] Deleting SG: {sg_id}")
        try:
            ec2.delete_security_group(GroupId=sg_id)
        except Exception as e:
            print(f"[WARN] Could not delete SG {sg_id}: {e}")


def delete_vpc(vpc_id):
    print(f"[FINAL] Attempting to delete VPC: {vpc_id}")
    try:
        ec2.delete_vpc(VpcId=vpc_id)
        print(f"[SUCCESS] VPC {vpc_id} deleted.")
    except ClientError as e:
        if "DependencyViolation" in str(e):
            print(f"[BLOCKED] VPC {vpc_id} still has dependencies.")
        else:
            print(f"[ERROR] Failed to delete VPC: {e}")


if __name__ == "__main__":
    print(f"[START] Cleaning up VPC: {VPC_ID}")
    release_elastic_ips()
    delete_vpc_endpoints(VPC_ID)
    delete_internet_gateways(VPC_ID)
    delete_route_tables(VPC_ID)
    delete_subnets(VPC_ID)
    delete_network_acls(VPC_ID)
    delete_security_groups(VPC_ID)
    delete_vpc(VPC_ID)
