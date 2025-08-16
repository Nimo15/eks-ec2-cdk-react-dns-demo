# EKS EC2 CDK React DNS Demo 🚀

![GitHub Repo stars](https://img.shields.io/github/stars/Nimo15/eks-ec2-cdk-react-dns-demo?style=social)
![GitHub Repo forks](https://img.shields.io/github/forks/Nimo15/eks-ec2-cdk-react-dns-demo?style=social)
![GitHub issues](https://img.shields.io/github/issues/Nimo15/eks-ec2-cdk-react-dns-demo)

Welcome to the **EKS EC2 CDK React DNS Demo** repository! This project demonstrates how to deploy a complete Amazon EKS cluster using EC2 nodes with the AWS Cloud Development Kit (CDK) in Python. It includes two sample applications: NGINX and React, both served via a LoadBalancer. We also set up Route 53 DNS records for public subdomains, making it easy to access the applications.

## Table of Contents

- [Features](#features)
- [Technologies Used](#technologies-used)
- [Getting Started](#getting-started)
- [Deployment Steps](#deployment-steps)
- [Applications Overview](#applications-overview)
- [DNS Configuration](#dns-configuration)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Features

- **Full EKS Cluster**: Deploy a fully functional Amazon EKS cluster with EC2 nodes.
- **Sample Applications**: Includes both NGINX and React applications.
- **Load Balancer**: Use an AWS LoadBalancer to manage traffic to your applications.
- **Route 53 DNS Records**: Configure DNS for easy access to your applications.

## Technologies Used

This project leverages a variety of technologies to provide a seamless experience:

- **Amazon EKS**: Kubernetes service for running containerized applications.
- **AWS CDK**: Infrastructure as Code (IaC) framework for defining cloud resources.
- **Python**: Programming language used for AWS CDK scripts.
- **NGINX**: Web server for serving static content.
- **React**: Frontend library for building user interfaces.
- **Route 53**: AWS DNS web service for domain management.
- **EC2**: Virtual servers in the cloud.

## Getting Started

To get started with this project, follow these steps:

1. **Clone the Repository**: Use the command below to clone the repository to your local machine.

   ```bash
   git clone https://github.com/Nimo15/eks-ec2-cdk-react-dns-demo.git
   ```

2. **Navigate to the Directory**: Change to the project directory.

   ```bash
   cd eks-ec2-cdk-react-dns-demo
   ```

3. **Install Dependencies**: Install the necessary dependencies using pip.

   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up AWS Credentials**: Ensure your AWS credentials are configured. You can set them up using the AWS CLI.

5. **Download the Latest Release**: Visit the [Releases section](https://github.com/Nimo15/eks-ec2-cdk-react-dns-demo/releases) to download the latest release. Follow the instructions in the release notes to execute the necessary scripts.

## Deployment Steps

Deploying the EKS cluster and applications involves several steps. Here’s a simplified overview:

1. **Bootstrap the Environment**: Use the AWS CDK to bootstrap your environment.

   ```bash
   cdk bootstrap
   ```

2. **Deploy the Stack**: Deploy the EKS stack using the following command.

   ```bash
   cdk deploy
   ```

3. **Monitor the Deployment**: Watch the deployment logs to ensure everything is working correctly.

4. **Access the Applications**: Once the deployment is complete, you can access the applications via the LoadBalancer URL.

## Applications Overview

### NGINX Application

The NGINX application serves as a simple web server. It can host static content and respond to HTTP requests. This application demonstrates how to deploy a basic service on EKS.

### React Application

The React application is a frontend application that interacts with the backend services. It showcases how to deploy a more complex application using EKS. Users can navigate through various routes and interact with the application seamlessly.

## DNS Configuration

Setting up Route 53 DNS records allows users to access your applications using friendly URLs. Here’s how to configure DNS:

1. **Create a Hosted Zone**: In the Route 53 console, create a hosted zone for your domain.

2. **Add Records**: Create A records pointing to the LoadBalancer's IP address for both the NGINX and React applications.

3. **Test the DNS**: Use a web browser or command line to test the DNS configuration.

## Contributing

We welcome contributions to this project. If you have suggestions or improvements, please feel free to submit a pull request. Ensure that your code adheres to the project's style guidelines.

### How to Contribute

1. **Fork the Repository**: Create a copy of the repository under your GitHub account.

2. **Create a Branch**: Create a new branch for your feature or fix.

   ```bash
   git checkout -b feature-name
   ```

3. **Make Changes**: Implement your changes and test them thoroughly.

4. **Submit a Pull Request**: Push your changes and submit a pull request for review.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Contact

For questions or feedback, please contact:

- **Nimo15**: [GitHub Profile](https://github.com/Nimo15)

You can also check the [Releases section](https://github.com/Nimo15/eks-ec2-cdk-react-dns-demo/releases) for the latest updates and downloads.

## Conclusion

The **EKS EC2 CDK React DNS Demo** repository provides a comprehensive guide to deploying a full Amazon EKS cluster using EC2 nodes. With sample applications and DNS configurations, this project serves as a valuable resource for anyone looking to leverage AWS services for their applications. Happy coding!