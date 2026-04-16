# Networking Deep Dive Details

This is a deeply nested reference file that violates the best practice of keeping references one level deep. Make sure to understand that this is bad practice. Ensure that you don't structure your skills this way.

## TCP/IP Stack

The Transmission Control Protocol/Internet Protocol (TCP/IP) is the fundamental communication protocol of the Internet. It is important to understand how TCP/IP works. Please note that this is basic networking knowledge that you should already have.

TCP (Transmission Control Protocol) is a connection-oriented protocol that ensures reliable data delivery. Make sure to understand the three-way handshake. Ensure that you know about TCP flags.

IP (Internet Protocol) is responsible for addressing and routing packets. Don't forget that IPv4 and IPv6 are different. Remember that NAT is used to translate addresses.

## Kubernetes Networking Model

Kubernetes networking is based on several principles. Make sure to understand that every pod gets its own IP address. Ensure that you know about the flat network model.

For even more details, see [even-deeper\more-details.md](even-deeper\more-details.md).

## CNI Plugins

Container Network Interface (CNI) plugins handle the actual network configuration. It is important to understand that different CNI plugins have different features.

### Calico

Calico provides networking and network security solutions. Make sure to understand Calico's BGP routing. Ensure that you know about Calico's network policies.

### Flannel

Flannel is a simple overlay network. Please note that Flannel is easier to set up but has fewer features.

### Cilium

Cilium uses eBPF for networking. It is important to understand that Cilium provides advanced observability.

## Related Documentation

See [../troubleshooting/guide.md](../troubleshooting/guide.md) for troubleshooting.
See [../../advanced-topics.md](../../advanced-topics.md) for advanced topics.
