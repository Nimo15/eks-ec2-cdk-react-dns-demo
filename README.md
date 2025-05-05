# EKS EC2 React Demo with DNS (Powered by Amazon CDK)

This project demonstrates how to provision a full **Amazon EKS cluster using EC2 nodes** with **infrastructure as code** via the **AWS CDK (Cloud Development Kit)**. It deploys two containerized applications on the cluster and configures **Route 53 DNS records** to expose them under custom subdomains.

---

## 📦 Stack Overview

- **Cluster Infrastructure**: Amazon EKS using EC2 worker nodes (Spot instances)
- **Provisioning Tool**: [AWS CDK (Python)](https://docs.aws.amazon.com/cdk/v2/guide/home.html)
- **Containerized Apps**:
  - A basic **Nginx demo app**
  - A custom **React + Vite** dashboard using Material UI
- **DNS**: Route 53 with subdomain mapping to Load Balancer via CNAME record

---

## ✅ What This Project Does

- Creates a VPC with public/private subnets
- Provisions an EKS cluster with Spot EC2 nodes
- Deploys containerized workloads to the cluster
- Integrates with AWS Route 53 to expose apps via:
  - `demo-v7.tiphareth.com.br`
  - `react-v7.tiphareth.com.br`

---

## 📂 Project Structure

```
.
├── app.py / main.py           # CDK app entry points
├── stacks/                    # CDK stack definitions
│   ├── eks_cluster_stack.py   # VPC + EKS + NodeGroup
│   ├── eks_app_stack.py       # Deploys Nginx app
│   ├── eks_react_app_stack.py # Deploys React + Vite app
│   ├── eks_dns_stack.py       # Route53 records for apps
│   └── version.py             # Global version identifier
├── scripts/                   # Utility and cleanup scripts
├── requirements.txt           # Python dependencies
├── Makefile                   # Common CDK targets
├── trust-policy.json          # IAM assume-role trust doc
└── README.md
```

---

## 🚀 Quick Start

> Make sure you have AWS credentials configured and [AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/cli.html) installed.

```bash
# Install dependencies
pip install -r requirements.txt

# Bootstrap the environment (only once per account/region)
cdk bootstrap

# Deploy cluster stack (EKS + VPC + Nodegroup)
cdk deploy EksClusterStackV7 --exclusively

# Deploy Nginx app + DNS
cdk deploy EksAppStackV7 EksDnsStackV7

# Deploy React app + DNS
cdk deploy EksReactAppStackV7
```

---

## 🌐 Resulting DNS

- Nginx App → `http://demo-v7.tiphareth.com.br`
- React App → `http://react-v7.tiphareth.com.br`

---

## 🧹 Utilities

Use these scripts for diagnostics or cleanup:

```bash
./scripts/rollback-watch.zsh
./scripts/delete_vpn.zsh
./scripts/force-destroy.zsh
```

---

## 🧠 Future Improvements

- Add **NGINX Ingress Controller**
- Integrate **cert-manager** + **Let's Encrypt**
- Automate SSL provisioning and DNS validation
- Enable auto-deploy for multiple React apps with DNS

---

## 📘 License

MIT or your license of choice.

---

## 👨‍💼 Author

Built with ❤️ by [Davi Luiz Guides](http://daviguides.github.io)
