# Runbook: Core Router / Hardware Failure

**Category:** hardware
**Severity default:** critical
**Symptoms:** A core device stops responding entirely, SNMP polling times out, redundant hardware may have already failed over (partial impact) or not (full outage).

## Diagnostic steps
1. Query the network monitoring API for the device's last heartbeat and health telemetry before it went dark.
2. Confirm whether automatic failover to redundant hardware occurred.
3. Check for a correlated power event in the same facility.

## Resolution steps
1. If failover succeeded: schedule replacement during a maintenance window, severity can be downgraded.
2. If failover did NOT occur: this is a P1 — trigger manual failover procedure immediately and dispatch a technician.
3. RMA the failed hardware and document the failure for vendor escalation.

## Customer communication template
"We experienced a hardware fault at one of our core sites. Redundant systems have minimized customer impact and a permanent fix is scheduled."
