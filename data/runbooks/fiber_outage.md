# Runbook: Fiber Line Outage

**Category:** physical_layer
**Severity default:** critical
**Symptoms:** Total loss of signal on a fiber segment, affected nodes report status DOWN, zero throughput, customers in the affected region report complete service loss.

## Diagnostic steps
1. Query the network monitoring API for the affected node's optical power levels (Rx/Tx).
2. If Rx power reads -40dBm or lower, treat as a physical fiber cut.
3. Cross-check with the regional outage map for correlated node failures (a single cut often affects multiple downstream nodes).

## Resolution steps
1. Dispatch a field technician to the last known good splice point.
2. Reroute traffic via the backup ring topology if available (reduces customer impact from critical to degraded).
3. Open a P1 ticket with the field operations team including exact GPS coordinates of the suspected cut.

## Customer communication template
"We have identified a physical fiber disruption affecting service in your area. Field technicians have been dispatched. Estimated resolution: 4-6 hours depending on accessibility."
