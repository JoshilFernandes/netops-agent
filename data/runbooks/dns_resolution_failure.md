# Runbook: DNS Resolution Failure

**Category:** application_layer
**Severity default:** medium
**Symptoms:** Users can reach the network but specific domains fail to resolve, elevated NXDOMAIN or SERVFAIL rates on resolver logs, service appears "down" to end users even though the underlying network is healthy.

## Diagnostic steps
1. Query the network monitoring API for resolver health metrics (query success rate, latency).
2. Check whether the failure is isolated to a specific resolver cluster or global.
3. Verify upstream root/TLD server reachability from the affected resolver.

## Resolution steps
1. If isolated to one resolver cluster, fail over traffic to a healthy cluster.
2. Flush and rebuild the local resolver cache if cache poisoning is suspected.
3. If global, check for an upstream provider incident before making internal changes.

## Customer communication template
"Some customers may experience issues reaching specific websites due to a DNS resolution issue. This does not affect your underlying internet connection. We are actively resolving it."
