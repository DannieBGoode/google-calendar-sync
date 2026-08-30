# Troubleshooting

## The Web UI cannot reach the service

Check `docker compose ps`, then request `http://localhost:8000/health`. Review container logs without posting credentials or event payloads publicly.

## A rule is degraded

Open the incident in the Web UI. Authorization incidents require reconnecting the affected identity
from Settings. The rule keeps mappings and its last successful incremental positions and performs no
writes while degraded. After reconnecting, choose **Validate recovery** in Rules, inspect the
preview, and enable the rule; its next run repairs drift before advancing either cursor.

## Destination edits return

This is expected. Destination events are Managed Projections and source content is authoritative.
Pause the rule before changing a destination projection that should temporarily remain untouched.

## A destination event was recreated

Deleting a Managed Projection is Drift while its source remains eligible. Synchronization recreates
it on the next destination change poll. Delete or exclude the source, or pause the rule instead.

## Incremental cursor expired

The Google adapter must discard the expired cursor, perform a safe initial-window scan, match managed projections through origin metadata, and establish a new cursor without duplicating events.
