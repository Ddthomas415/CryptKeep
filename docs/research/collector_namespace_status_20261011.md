# Collector Namespace Status Correction

SHOWN: laptop collector PID32213 was alive and reporting fresh captures; the Docker gateway read the same mounted status but reported dead because the host PID is outside its process namespace. No collector restart was needed or performed.

The status reader now optionally skips process verification, returning pid_alive null with external_namespace_unverified. Default local process-management verification remains unchanged. The dashboard opts out only under Docker's /.dockerenv marker and explicitly labels reported status and unknown host liveness. Snapshot/status freshness, stopped state and error warnings remain active. Fourteen targeted tests passed; separate reviewer accepted bounded source correction ACCEPTED_WITH_RISK.

After checking the local Docker identity, readonly repository mount, no-trading setting and loopback port, restarted only the existing gateway to reload mounted modules. Gateway configuration and image stayed identical; database, MinIO, memory and orchestrator start timestamps stayed unchanged. Browser authentication still worked and execution remained disabled.

Actual container result: collector_status running; snapshots and collector reports fresh; host process liveness unverified from container; issues empty. Actual browser page showed Current with this explicit caveat, replacing the false dead-process warning. No trading, credential, campaign, account or collector-setting changes.

This is a current-data observation, not sustained health, fill proof or profitability evidence. Docker detection does not establish namespace scope for every non-Docker isolation technology.
