# Troubleshooting Guide

This guide helps you troubleshoot common Kubernetes issues. Make sure to follow the steps carefully. Ensure that you check each item. Don't forget to verify your results.

## Pod Issues

When your pod is not working, make sure to check the following. Ensure that you look at the pod status first. Remember to examine the events.

### Pending Pods

If your pod is stuck in Pending state, it is important to check several things. Please note that resource constraints are a common cause. Keep in mind that scheduling issues can also cause this.

For more details, see [pod-troubleshooting\pending.md](pod-troubleshooting\pending.md).

### CrashLoopBackOff

When a pod is in CrashLoopBackOff, make sure to check the logs. Ensure that you look at the previous container logs. Don't forget to verify the configuration.

For crash analysis, refer to [pod-troubleshooting\crash-analysis.md](pod-troubleshooting\crash-analysis.md).

## Networking Issues

Networking issues can be complex. Make sure to understand the networking model. Ensure that you check the CNI configuration.

For networking troubleshooting, see [networking\troubleshooting\guide.md](networking\troubleshooting\guide.md).

## Storage Issues

Storage issues require careful investigation. Make sure to check the PV and PVC status. Ensure that the storage class is configured correctly.

For storage troubleshooting, refer to [storage\troubleshooting\guide.md](storage\troubleshooting\guide.md).

## See Also

- [advanced-topics.md](advanced-topics.md) for advanced configurations
- [networking\deep-dive\details.md](networking\deep-dive\details.md) for networking details
