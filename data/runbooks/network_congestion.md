# Runbook: Network Congestion / Capacity Exhaustion

**Category:** capacity
**Severity default:** medium
**Symptoms:** Elevated latency and jitter, increased packet loss under peak load, link utilization consistently above 90%, no hard failures reported by any single device.

## Diagnostic steps
1. Query the network monitoring API for link utilization on the affected segment over the last 24 hours.
2. Identify whether congestion is a recurring peak-hour pattern or a new sustained trend.
3. Check for a recent traffic anomaly versus organic growth.

## Resolution steps
1. For organic growth: submit a capacity upgrade request to network planning.
2. For a short-term spike: enable QoS traffic shaping to prioritize latency-sensitive traffic.
3. For suspected DDoS: engage the security/DDoS mitigation team immediately.

## Customer communication template
"We are aware of increased latency during peak hours in your area and are actively working on a capacity upgrade."
