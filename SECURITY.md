# Security policy

This is research software and must not be connected directly to an authoritative production store.
Report vulnerabilities privately to the project maintainer once the canonical repository is
connected.

The reference API has no authentication and is intended for localhost demonstration only. A
deployment must add authentication, request-size limits, audit logging, dependency scanning,
network egress policy, and an isolated worker for geospatial file processing. Authoritative writes
must remain disabled until an organizational approval policy is implemented and tested.
