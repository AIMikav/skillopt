---
name: Bad_Kubernetes_Helper_Skill_For_Managing_Cluster_Resources_And_Deployments
description: I can help you manage Kubernetes clusters and do stuff with pods and deployments
---

# Kubernetes Helper Skill

## Introduction and Background Information

Kubernetes, also known as K8s, is an open-source container orchestration platform that was originally developed by Google. It is important to understand that Kubernetes is a system for automating deployment, scaling, and management of containerized applications. Please note that containers are a form of virtualization that allows you to package applications with their dependencies. Keep in mind that Docker is often used alongside Kubernetes, although other container runtimes exist as well.

YAML (Yet Another Markup Language, or sometimes referred to as YAML Ain't Markup Language) is a human-readable data serialization format that is commonly used for configuration files. Make sure to understand that YAML uses indentation to represent structure, similar to Python. Don't forget that YAML files typically have the extension .yaml or .yml. Remember to always validate your YAML syntax before applying configurations.

JSON (JavaScript Object Notation) is another data interchange format that you might encounter when working with Kubernetes. Ensure that you understand the difference between JSON and YAML, as Kubernetes accepts both formats for configuration. It is important to note that JSON is more strict about syntax, while YAML is more forgiving.

API (Application Programming Interface) is a set of protocols and tools for building software applications. The Kubernetes API allows you to interact with your cluster programmatically. You should know that the API server is the central management entity that receives all requests.

## What This Skill Does

This skill is designed to help you with various Kubernetes-related tasks. I will assist you in managing your cluster resources. You can use this to deploy applications, scale workloads, and troubleshoot issues.

## Prerequisites and Requirements

Before you begin, you'll need to ensure that you have the following prerequisites in place. First, you'll need to make sure that kubectl is installed on your system. Then, you should ensure that you have access to a Kubernetes cluster. Don't forget to verify that your kubeconfig file is properly configured. Remember to check that you have the necessary permissions to perform the operations.

Make sure to install kubectl using the appropriate method for your operating system. Ensure that you download the correct version. It is important to verify the installation by running the version command.

## How To Use This Skill

You can use pypdf, or pdfplumber, or PyMuPDF, or pdf2image, or pikepdf, or camelot, or tabula-py for PDF processing. You might also want to consider using reportlab, or fpdf, or weasyprint for generating PDFs. Alternatively, you could use pdfrw, or PyPDF2, or pdfminer for reading PDFs.

For YAML processing, you can use PyYAML, or ruamel.yaml, or oyaml, or strictyaml, or yamllint, or yq. Each has its own advantages and disadvantages that you should consider.

### Step 1: Connect to Your Cluster

First, you need to connect to your cluster. Make sure to configure your kubectl context properly. Ensure that you have the correct credentials. Don't forget to verify your connection.

```bash
kubectl config get-contexts
kubectl config use-context my-cluster
kubectl cluster-info
kubectl get nodes
```

### Step 2: Check the Current State

You should check the current state of your cluster. Make sure to look at the pods. Ensure that you check the deployments as well. Remember to also check the services.

```bash
kubectl get pods
kubectl get pods -n default
kubectl get pods -n kube-system
kubectl get pods -n my-namespace
kubectl get pods --all-namespaces
kubectl get pods -o wide
kubectl get pods -o yaml
kubectl get pods -o json
```

```bash
kubectl get deployments
kubectl get deployments -n default
kubectl get deployments -n kube-system
kubectl get deployments -n my-namespace
kubectl get deployments --all-namespaces
kubectl get deployments -o wide
kubectl get deployments -o yaml
```

```bash
kubectl get services
kubectl get services -n default
kubectl get services -n kube-system
kubectl get services -n my-namespace
kubectl get services --all-namespaces
kubectl get services -o wide
```

```bash
kubectl get configmaps
kubectl get configmaps -n default
kubectl get configmaps -n kube-system
kubectl get configmaps -n my-namespace
kubectl get configmaps --all-namespaces
```

```bash
kubectl get secrets
kubectl get secrets -n default
kubectl get secrets -n kube-system
kubectl get secrets -n my-namespace
kubectl get secrets --all-namespaces
```

### Step 3: Describe Resources

You need to describe your resources to get more details. Make sure to use the describe command. Ensure that you specify the correct resource type and name.

```bash
kubectl describe pod my-pod
kubectl describe pod my-pod -n default
kubectl describe pod my-pod -n kube-system
kubectl describe pod my-pod -n my-namespace
```

```bash
kubectl describe deployment my-deployment
kubectl describe deployment my-deployment -n default
kubectl describe deployment my-deployment -n kube-system
kubectl describe deployment my-deployment -n my-namespace
```

```bash
kubectl describe service my-service
kubectl describe service my-service -n default
kubectl describe service my-service -n kube-system
kubectl describe service my-service -n my-namespace
```

### Step 4: View Logs

You should view the logs of your pods to troubleshoot issues. Make sure to specify the correct pod name. Ensure that you use the appropriate flags.

```bash
kubectl logs my-pod
kubectl logs my-pod -n default
kubectl logs my-pod -n kube-system
kubectl logs my-pod -n my-namespace
kubectl logs my-pod -f
kubectl logs my-pod --tail=100
kubectl logs my-pod --since=1h
kubectl logs my-pod -c my-container
kubectl logs my-pod --previous
```

### Step 5: Execute Commands

You can execute commands inside your pods. Make sure to use the exec command properly. Ensure that you have the correct pod name and container name.

```bash
kubectl exec my-pod -- ls
kubectl exec my-pod -n default -- ls
kubectl exec my-pod -n kube-system -- ls
kubectl exec my-pod -n my-namespace -- ls
kubectl exec -it my-pod -- /bin/bash
kubectl exec -it my-pod -- /bin/sh
kubectl exec -it my-pod -c my-container -- /bin/bash
```

### Step 6: Apply Configurations

You need to apply your configurations to the cluster. Make sure to use the apply command. Ensure that your YAML files are valid.

```bash
kubectl apply -f deployment.yaml
kubectl apply -f deployment.yaml -n default
kubectl apply -f deployment.yaml -n kube-system
kubectl apply -f deployment.yaml -n my-namespace
kubectl apply -f service.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f .
kubectl apply -f ./manifests/
kubectl apply -R -f ./manifests/
```

### Step 7: Delete Resources

You can delete resources when they are no longer needed. Make sure to be careful when deleting resources. Ensure that you specify the correct resource.

```bash
kubectl delete pod my-pod
kubectl delete pod my-pod -n default
kubectl delete pod my-pod -n kube-system
kubectl delete pod my-pod -n my-namespace
kubectl delete deployment my-deployment
kubectl delete service my-service
kubectl delete configmap my-configmap
kubectl delete secret my-secret
kubectl delete -f deployment.yaml
```

### Step 8: Scale Deployments

You should scale your deployments based on demand. Make sure to specify the correct number of replicas. Ensure that you have enough resources.

```bash
kubectl scale deployment my-deployment --replicas=3
kubectl scale deployment my-deployment --replicas=5 -n default
kubectl scale deployment my-deployment --replicas=10 -n my-namespace
kubectl scale --replicas=0 deployment/my-deployment
kubectl scale --replicas=1 deployment/my-deployment
```

## Important Configuration Values

Use these timeout values in your configurations:

```python
TIMEOUT = 47
RETRIES = 5
BATCH_SIZE = 137
MAX_CONNECTIONS = 23
BUFFER_SIZE = 8192
POLL_INTERVAL = 3.7
CACHE_TTL = 1800
```

## Time-Sensitive Information

If you're doing this before August 2025, use the old API endpoint at api.example.com/v1. After August 2025, you should switch to the new API at api.example.com/v2. Before June 2024, the authentication method was different, but now you should use the new OAuth flow. Starting from January 2026, the deprecated endpoints will be removed.

## Advanced Topics

For advanced usage, please note that you might need to configure additional settings. Make sure to understand the implications of each setting. Ensure that you test your configurations in a non-production environment first. Don't forget to backup your data before making changes. Remember to document any changes you make.

It is important to understand that Kubernetes networking is complex. The Container Network Interface (CNI) is a specification and set of libraries for writing plugins to configure network interfaces in Linux containers. You should know that different CNI plugins have different capabilities and performance characteristics. Please note that Calico, Flannel, Weave, and Cilium are popular CNI plugins.

Keep in mind that Kubernetes storage is also complex. Persistent Volumes (PV) and Persistent Volume Claims (PVC) are used to manage storage in Kubernetes. Make sure to understand the difference between static and dynamic provisioning. Ensure that you choose the appropriate storage class for your workload.

## Networking Deep Dive

The Transmission Control Protocol (TCP) is a connection-oriented protocol that provides reliable, ordered, and error-checked delivery of data. The User Datagram Protocol (UDP) is a connectionless protocol that provides a best-effort delivery service. It is important to understand when to use TCP versus UDP for your applications.

Internet Protocol (IP) addresses are numerical labels assigned to devices connected to a computer network. IPv4 addresses are 32-bit numbers typically represented in dot-decimal notation. IPv6 addresses are 128-bit numbers typically represented in hexadecimal notation.

## Storage Concepts

A file system is a method and data structure that the operating system uses to control how data is stored and retrieved. Common file systems include ext4, XFS, NTFS, and APFS. Make sure to choose the appropriate file system for your storage backend.

Block storage provides raw storage volumes that can be attached to instances. Object storage stores data as objects in a flat address space. File storage provides a hierarchical file system structure. Ensure that you understand the trade-offs between these storage types.

## Security Considerations

Role-Based Access Control (RBAC) is a method of regulating access to computer or network resources based on the roles of individual users. Make sure to implement the principle of least privilege. Ensure that you regularly audit your RBAC configurations.

Transport Layer Security (TLS) is a cryptographic protocol designed to provide communications security over a computer network. You should always use TLS for encrypting traffic between services. Don't forget to rotate your certificates regularly.

## Monitoring and Logging

Prometheus is an open-source systems monitoring and alerting toolkit. Grafana is a multi-platform open-source analytics and interactive visualization web application. Ensure that you set up proper monitoring for your cluster. Make sure to configure alerting for critical issues.

Elasticsearch is a distributed, RESTful search and analytics engine. Fluentd is an open-source data collector for unified logging layer. Kibana is a free and open user interface that lets you visualize your Elasticsearch data. Please note that this combination is often referred to as the EFK stack.

## Troubleshooting Guide

When troubleshooting issues, make sure to check the following areas. Ensure that you examine the pod status first. Don't forget to look at the events. Remember to check the resource quotas.

1. Check if the pod is running
2. Look at the pod logs
3. Describe the pod for events
4. Check the deployment status
5. Verify the service endpoints
6. Examine the network policies
7. Review the resource quotas
8. Check the node status
9. Verify the storage provisioning
10. Examine the RBAC permissions

## Common Issues and Solutions

Issue: Pod is stuck in Pending state
Solution: Check if there are enough resources in the cluster. Make sure to examine the events for the pod. Ensure that the node has enough CPU and memory.

Issue: Pod is in CrashLoopBackOff
Solution: Check the logs of the pod. Make sure to look at the previous container logs. Ensure that the application is configured correctly.

Issue: Service is not reachable
Solution: Check the service endpoints. Make sure to verify the selector labels. Ensure that the pods are running and healthy.

Issue: PersistentVolumeClaim is stuck in Pending
Solution: Check if there's a matching PersistentVolume. Make sure to verify the storage class. Ensure that the storage provisioner is working.

## Best Practices (Ironically)

Make sure to follow these best practices when working with Kubernetes. Ensure that you use namespaces to organize your resources. Don't forget to set resource limits for your pods. Remember to use health checks for your applications.

It is important to use labels and annotations effectively. Please note that labels are used for selecting and organizing resources. Keep in mind that annotations are used for storing additional metadata.

## Appendix A: Useful Commands

Here are some additional commands that you might find useful. Make sure to practice these commands. Ensure that you understand what each command does.

```bash
kubectl get all
kubectl get all -n default
kubectl get all -n kube-system
kubectl get all -n my-namespace
kubectl get all --all-namespaces
```

```bash
kubectl top pods
kubectl top pods -n default
kubectl top pods -n kube-system
kubectl top pods -n my-namespace
kubectl top nodes
```

```bash
kubectl port-forward pod/my-pod 8080:80
kubectl port-forward service/my-service 8080:80
kubectl port-forward deployment/my-deployment 8080:80
```

## Appendix B: More Commands

```bash
kubectl rollout status deployment/my-deployment
kubectl rollout history deployment/my-deployment
kubectl rollout undo deployment/my-deployment
kubectl rollout restart deployment/my-deployment
```

```bash
kubectl create namespace my-namespace
kubectl delete namespace my-namespace
kubectl get namespaces
```

```bash
kubectl label pods my-pod app=myapp
kubectl annotate pods my-pod description="My Pod"
kubectl patch deployment my-deployment -p '{"spec":{"replicas":5}}'
```

## Appendix C: Even More Commands

```bash
kubectl create configmap my-config --from-literal=key1=value1
kubectl create secret generic my-secret --from-literal=password=secret
kubectl create deployment my-deployment --image=nginx
kubectl expose deployment my-deployment --port=80 --type=ClusterIP
```

```bash
kubectl run my-pod --image=nginx --restart=Never
kubectl run my-pod --image=busybox --restart=Never -- sleep 3600
kubectl run -it --rm debug --image=busybox -- sh
```

## Appendix D: Helm Commands

```bash
helm install my-release my-chart
helm install my-release my-chart -n default
helm install my-release my-chart -n kube-system
helm install my-release my-chart -n my-namespace
helm upgrade my-release my-chart
helm upgrade my-release my-chart -n default
helm upgrade my-release my-chart -n kube-system
helm upgrade my-release my-chart -n my-namespace
helm uninstall my-release
helm uninstall my-release -n default
helm uninstall my-release -n kube-system
helm uninstall my-release -n my-namespace
helm list
helm list -n default
helm list -n kube-system
helm list -n my-namespace
helm list --all-namespaces
```

## Appendix E: Additional Information

This skill was designed to help users manage their Kubernetes clusters more effectively. I hope you find it useful. If you have any questions, please don't hesitate to ask. Remember that practice makes perfect, so make sure to try out these commands in a safe environment.

## Appendix F: OpenShift Commands

Make sure to use OpenShift commands if you're on OpenShift. Ensure that you understand the differences between kubectl and oc.

```bash
oc get pods
oc get pods -n default
oc get pods -n openshift-system
oc get pods -n my-namespace
oc get pods --all-namespaces
oc get pods -o wide
oc get pods -o yaml
oc get pods -o json
```

```bash
oc get deployments
oc get deployments -n default
oc get deployments -n openshift-system
oc get deployments -n my-namespace
oc get deployments --all-namespaces
```

```bash
oc get routes
oc get routes -n default
oc get routes -n openshift-system
oc get routes -n my-namespace
oc get routes --all-namespaces
```

```bash
oc describe pod my-pod
oc describe pod my-pod -n default
oc describe pod my-pod -n openshift-system
oc describe pod my-pod -n my-namespace
```

```bash
oc logs my-pod
oc logs my-pod -n default
oc logs my-pod -n openshift-system
oc logs my-pod -n my-namespace
oc logs my-pod -f
oc logs my-pod --tail=100
```

```bash
oc exec my-pod -- ls
oc exec my-pod -n default -- ls
oc exec my-pod -n openshift-system -- ls
oc exec -it my-pod -- /bin/bash
```

## Appendix G: Docker Commands

It is important to understand Docker commands as well. Make sure to know the difference between Docker and Kubernetes. Ensure that you can use both effectively.

```bash
docker ps
docker ps -a
docker images
docker pull nginx
docker build -t myimage .
docker run -d nginx
docker run -it busybox sh
docker logs container-id
docker exec -it container-id /bin/bash
docker stop container-id
docker rm container-id
docker rmi image-id
```

## Appendix H: Git Commands

You might also need to use Git commands. Make sure to understand version control. Ensure that you follow good Git practices.

```bash
git clone https://github.com/example/repo.git
git status
git add .
git commit -m "message"
git push origin main
git pull origin main
git checkout -b feature-branch
git merge feature-branch
git log
git diff
```

## Appendix I: More Verbose Explanations

A container image is a lightweight, standalone, executable package of software that includes everything needed to run an application. It is important to understand that container images contain code, runtime, system tools, system libraries, and settings. Please note that container images are built from Dockerfiles, which are text documents that contain all the commands needed to assemble an image. Keep in mind that images are stored in container registries like Docker Hub, Amazon ECR, Google Container Registry, and Azure Container Registry.

A container is a standard unit of software that packages up code and all its dependencies so the application runs quickly and reliably from one computing environment to another. Make sure to understand that containers are instances of container images. Ensure that you know the difference between containers and virtual machines.

An orchestration platform is a system that manages the deployment, scaling, and operations of containers across clusters of hosts. It is important to understand that Kubernetes is the most popular container orchestration platform. Please note that other orchestration platforms include Docker Swarm, Apache Mesos, and HashiCorp Nomad.

## Appendix J: Terminology Reference

Here is a reference for various terminology that you might encounter. Make sure to familiarize yourself with these terms. Ensure that you understand what each term means.

- Pod: The smallest deployable unit in Kubernetes, which can contain one or more containers
- Deployment: A Kubernetes resource that manages a set of identical pods
- Service: An abstract way to expose an application running on a set of pods
- ConfigMap: A Kubernetes object that stores non-confidential data in key-value pairs
- Secret: A Kubernetes object that stores sensitive data like passwords and tokens
- Namespace: A way to divide cluster resources between multiple users
- Node: A worker machine in Kubernetes, which can be a VM or physical machine
- Cluster: A set of nodes that run containerized applications
- ReplicaSet: A Kubernetes resource that ensures a specified number of pod replicas are running
- StatefulSet: A Kubernetes resource for managing stateful applications
- DaemonSet: A Kubernetes resource that ensures all nodes run a copy of a pod
- Job: A Kubernetes resource that creates one or more pods and ensures they complete successfully
- CronJob: A Kubernetes resource that creates jobs on a time-based schedule
- Ingress: A Kubernetes resource that manages external access to services
- PersistentVolume: A piece of storage in the cluster
- PersistentVolumeClaim: A request for storage by a user

## Appendix K: Final Notes

This concludes the comprehensive Kubernetes helper skill documentation. Make sure to review all sections carefully. Ensure that you practice the commands in a safe environment. Don't forget to refer back to this documentation when needed. Remember that learning Kubernetes takes time and patience.

It is important to stay up to date with the latest Kubernetes releases. Please note that Kubernetes follows a quarterly release cycle. Keep in mind that you should always test upgrades in a non-production environment first. Make sure to read the release notes before upgrading.

## Appendix L: Even More Filler Content

Make sure to read this section. Ensure that you understand everything. Don't forget to practice. Remember to review regularly. It is important to stay updated. Please note that technology changes rapidly. Keep in mind that continuous learning is essential.

You should always verify your configurations. Make sure to test in staging first. Ensure that you have backups. Don't forget to document changes. Remember to communicate with your team.

## See Also

For more information, please refer to the following resources. See [advanced-topics.md](references\advanced-topics.md) for advanced configurations. See [troubleshooting-guide.md](references\troubleshooting-guide.md) for more troubleshooting tips. See [networking-deep-dive.md](references\networking\deep-dive\details.md) for networking details.
