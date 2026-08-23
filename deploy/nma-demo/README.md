# NMA public demo deployment runbook

This deploys only the controlled NMA v1.0 research adapter at
`https://demo.geomni.tw/nma/`. It does not expose the repository development server, accept
uploads, issue authorization, activate BUILD, or mount production data/credentials.

## Current fail-closed gate

Do **not** install, start, or publicly route this service from the DEPLOY-01 branch. The frozen
`data/demo/public-demo-data-authority-matrix-v1.0.json` records no accepted public School/ROAD
fixtures, no public demo authorizations, and a `fail-closed` verdict. The startup verifier
therefore exits nonzero after validating the other identities. In addition, `demo.geomni.tw`
currently has no DNS A/AAAA record and no deploy host/account is configured. The remaining
sections are the bounded staging/rollback procedure for a future separately authorized closure;
they are not go-live instructions.

## Immutable inputs

- DEPLOY-01 release checkout: installed root-owned beneath `/opt/nma-demo/releases/<DEPLOY01_SHA>/`
- frozen NMA release identity: `eb87bde775333811529efb6f651573ea21cf456b`
- controlled archive: `/srv/nma-demo/fixtures/nma-v1.0/112年多維度SHP成果_0502.zip`, mode `0440`, root:`nma-demo`
- School authorization: `/srv/nma-demo/authority/nma-v1.0/authorization-school-demo-b4ecdbfc35ecaf73293ed497.json`, mode `0440`
- GraphRAG JSON and all code: read-only release files
- explicitly absent: production mounts, activation credentials/stores, OpenAI key, Neo4j settings

## Preflight and bounded backup

Before touching the host, record `nginx -T`, `systemctl cat nma-demo.service` (if present), DNS,
listening sockets, and hashes of any existing `demo.geomni.tw` file in a timestamped root-only
directory. Confirm the host is a dedicated deny-by-default vhost. Do not replace an unrelated
server block.

Create the `nma-demo` system user without a login shell or unrelated group membership. Copy the
exact release with `.git`, ignored files, and writable runtime artifacts excluded. Copy the owner-
provided archive and exact accepted authority separately, then make release/fixture/authority
trees root-owned and non-writable by the service. Create `/opt/nma-demo/current` as a root-managed
symlink to the exact release directory. Copy `nma-demo.env.example` to the root-owned `0640`
`/etc/nma-demo/nma-demo.env`; do not add variables.

## Validate before activation

Run, in order:

```text
sudo -u nma-demo env -i PATH=/usr/bin:/bin PYTHONPATH=/opt/nma-demo/current/src:/opt/nma-demo/current $(sed '/^#/d' /etc/nma-demo/nma-demo.env | xargs) /usr/bin/python3 /opt/nma-demo/current/scripts/verify_nma_public_demo_startup.py
systemd-analyze verify /etc/systemd/system/nma-demo.service
nginx -t
```

At the current predecessor, the first command must fail with the public-data-authority/contract
closure error. A successful result is permitted only after a separately authorized stage records
compatible public fixtures and domain-owned public demo authority without modifying NMA v1.0.
Any other mismatch is also a stop condition. Verify the service socket is Unix-only and that no
NMA TCP listener exists.

Install the unit and nginx file only after inspecting the host's existing configuration. The nginx
file is an `http{}` include because it declares bounded rate-limit zones. Set its two TLS paths to
the existing protected origin certificate; TLS material is never readable by `nma-demo`. Run
`nginx -t` before every reload. Enable the service locally, smoke-test through the Unix socket and
nginx with a host override, and only then enable the Cloudflare DNS/proxy route.

## Public acceptance

From outside the origin network, verify DNS, a valid HTTPS chain, `/nma/`, all self-hosted assets,
both health routes, and School/ROAD/BUILD guided runs. Inspect the lifecycle, evidence, provenance,
and live MapLibre result. Confirm BUILD says activation is unavailable/not mounted. Confirm direct
`/api/*`, admin, debug, source, dotfile, fixture, graph, upload, authorization, writeback,
activation, observation, rollback, traversal, malformed JSON, wrong content type, and unknown NMA
paths fail closed. Verify 429 with `Retry-After`, security headers, no wildcard CORS, no mixed or
third-party requests, and no secrets in response bodies/logs.

## Rollback

1. Preserve journald/nginx evidence and the deployed release/config hashes.
2. Disable the Cloudflare route or restore the prior DNS record.
3. Remove only the bounded NMA nginx include/symlink, restore the captured predecessor config, run
   `nginx -t`, then reload nginx.
4. Stop and disable only `nma-demo.service`; leave the frozen release and controlled inputs intact.
5. Confirm `/nma/` is no longer routed and unrelated services are unchanged.

Rollback never rewrites NMA v1.0, fixture bytes, mapping rules, or authorization semantics.
