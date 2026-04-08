---
name: Kubernetes_Helper_Skill_For_Managing_Cluster_Resources
description: Assist with managing resources, deployments, scaling, and troubleshooting in Kubernetes clusters.
---

# Kubernetes Helper Skill

## What This Skill Does

This skill assists with Kubernetes-related tasks, including managing cluster resources, deploying applications, scaling workloads, and troubleshooting issues.

## Prerequisites and Requirements

- **kubectl**: Ensure it is installed and correctly configured.
- **Kubernetes Cluster Access**: Confirm kubeconfig is properly set up and permissions are sufficient.

## How To Use This Skill

### Step 1: Connect to Your Cluster

Configure and verify kubectl context.

```bash
kubectl config get-contexts
kubectl config use-context <your-cluster>
kubectl cluster-info
kubectl get nodes
```

### Step 2: Check the Current State

Evaluate the existing state of cluster resources.

```bash
kubectl get pods [-n <namespace>] [--all-namespaces] [-o wide|yaml|json]
kubectl get deployments [-n <namespace>] [--all-namespaces] [-o wide|yaml]
kubectl get services [-n <namespace>] [--all-namespaces] [-o wide]
kubectl get configmaps [-n <namespace>] [--all-namespaces]
kubectl get secrets [-n <namespace>] [--all-namespaces]
```

### Step 3: Describe Resources

For detailed information about resources.

```bash
kubectl describe pod <pod-name> [-n <namespace>]
kubectl describe deployment <deployment-name> [-n <namespace>]
kubectl describe service <service-name> [-n <namespace>]
```

### Step 4: View Logs

Troubleshoot by reviewing pod logs.

```bash
kubectl logs <pod-name> [-n <namespace>] [-f] [--tail=<number>] [--since=<time>] [-c <container-name>] [--previous]
```

### Step 5: Execute Commands

Run commands inside pods.

```bash
kubectl exec <pod-name> [-n <namespace>] -- <command>
kubectl exec -it <pod-name> [-n <namespace>] [-c <container-name>] -- <shell>
```

### Step 6: Apply Configurations

Apply YAML configurations to the cluster.

```bash
kubectl apply -f <filename> [-n <namespace>]
kubectl apply -R -f <directory>/
```

### Step 7: Delete Resources

Remove resources when no longer needed.

```bash
kubectl delete <resource-type> <resource-name> [-n <namespace>]
kubectl delete -f <filename>
```

### Step 8: Scale Deployments

Adjust deployment replicas as needed.

```bash
kubectl scale deployment <deployment-name> --replicas=<number> [-n <namespace>]
```

## Conclusion

This skill aims to streamline Kubernetes operational tasks, providing a concise reference for managing and troubleshooting cluster resources effectively.