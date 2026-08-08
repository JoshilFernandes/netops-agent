# Runbook: Enterprise VPN / Tunnel Connectivity Issue

**Category:** enterprise_services
**Severity default:** medium
**Symptoms:** Business customers on site-to-site or client VPN tunnels report drops or inability to connect, tunnel state shows down or repeatedly renegotiating.

## Diagnostic steps
1. Query the network monitoring API for tunnel/IPsec session state on the affected customer's endpoint.
2. Check whether phase 1 (IKE) or phase 2 (IPsec SA) negotiation is failing.
3. Verify whether a certificate or pre-shared key recently expired.

## Resolution steps
1. For expired credentials: coordinate a credential rotation with the customer's IT team.
2. For repeated renegotiation failures: check for MTU/fragmentation issues and adjust MSS clamping.
3. Escalate to the enterprise services team if the customer has an SLA-backed contract.

## Customer communication template
"We've identified an issue with your VPN tunnel connectivity and are working directly with your IT team to restore stable connectivity."
