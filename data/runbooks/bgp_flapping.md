# Runbook: BGP Route Flapping

**Category:** routing
**Severity default:** high
**Symptoms:** Repeated BGP session resets between peering routers, intermittent packet loss, route table instability, customers report periodic connectivity drops (not total outage).

## Diagnostic steps
1. Query the network monitoring API for BGP session state history on the affected router.
2. Count flap events in the last 15 minutes; more than 5 flaps indicates active flapping.
3. Check whether flap-dampening is already engaged.

## Resolution steps
1. Identify the flapping neighbor AS and check for known upstream instability.
2. Apply or tighten route dampening policy on the affected peer session.
3. If flapping originates from a customer-facing BGP session, contact the customer's network team.
4. Escalate to Tier 3 routing engineers if flapping persists after dampening.

## Customer communication template
"We've identified intermittent routing instability affecting your connection. Our engineers are applying mitigation and monitoring. No total outage is expected."
