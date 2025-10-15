SHELL := /bin/bash
PY := python3
UVICORN := uvicorn
ORCH_APP := services.orchestrator.main:app
OPS_APP := services.api.main:app
PORT_ORCH := 8000
PORT_OPS := 9000

IPFS_API ?= http://127.0.0.1:5201
IPFS_GATEWAY ?= http://127.0.0.1:8082
DIST ?= dist

.PHONY: help
help:
	@echo "Targets:"
	@echo "  setup          - install Python & Node deps"
	@echo "  run            - run orchestrator (FastAPI @ :$(PORT_ORCH))"
	@echo "  run-ops        - run Ops API (FastAPI @ :$(PORT_OPS))"
	@echo "  run-worker     - start Zoho worker loop"
	@echo "  run-ipfs       - start local IPFS daemon (docker fallback)"
	@echo "  publish        - publish ./$(DIST) to IPFS via script"
	@echo "  verify         - HEAD check gateway for published CID"
	@echo "  smoke          - end-to-end health + publish + verify"
	@echo "  kill           - stop uvicorn processes"
	@echo "  clean          - remove caches and publish artifacts"
	@echo "  anchor         - XRPL anchor current CID (stub)"
	@echo "  mint           - Polygon mint stub with ipfs://CID note"
	@echo "  github-sync    - commit registry file (if present)"
	@echo "  notify         - send Slack and/or Zoho notification for latest CID"
	@echo "  bridge         - run anchor + mint and update registry"
	@echo "  up             - start compose runtime (devnet, ops, swarm)"
	@echo "  pipeline       - publish → verify → hash → swarm-attest → proof-submit"

.PHONY: setup
setup:
	pip3 install -U pip
	$(PY) -m pip install -r requirements.txt || true
	npm install || npm ci || true
	npm install --prefix apps/web || npm ci --prefix apps/web || true

.PHONY: run
run:
	@export $$(grep -v '^#' .env 2>/dev/null | xargs) ; \
	$(UVICORN) $(ORCH_APP) --host 0.0.0.0 --port $(PORT_ORCH) --reload

.PHONY: run-ops
run-ops:
	@export $$(grep -v '^#' .env 2>/dev/null | xargs) ; \
	$(UVICORN) $(OPS_APP) --host 0.0.0.0 --port $(PORT_OPS) --reload

.PHONY: run-worker
run-worker:
	$(PY) services/workers/zoho_worker.py

.PHONY: run-ipfs
run-ipfs:
	bash scripts/run-ipfs-daemon.sh

.PHONY: publish
publish:
	$(PY) scripts/publish_to_ipfs.py $(DIST) | jq . \
	&& ls -l $(DIST)/publish.json
	@CID=$$(jq -r '(.cid // .root // empty)' $(DIST)/publish.json); \
	SHA=$$(python3 scripts/hash_directory.py $(DIST)); \
	node scripts/registry-update.mjs --cid=$$CID --url=$(IPFS_GATEWAY)/ipfs/$$CID/ --sha=$$SHA >/dev/null || true

.PHONY: verify
verify:
	@test -f $(DIST)/publish.json
	@CID=$$(jq -r '(.root // .cid // empty)' $(DIST)/publish.json); \
	curl -sS -I "$(IPFS_GATEWAY)/ipfs/$$CID/" | head -n1; \
	curl -sS "$(IPFS_GATEWAY)/ipfs/$$CID/index.html" | head -n 5

.PHONY: smoke
smoke: run-ipfs
	@echo "🔎 Orchestrator health"; \
	curl -sS http://127.0.0.1:$(PORT_ORCH)/health | jq .
	@echo "📦 Publish"; \
	curl -sS -X POST http://127.0.0.1:$(PORT_ORCH)/swarm/run \
	  -H 'Content-Type: application/json' \
	  -d '{"task":"publish","params":{"path":"$(DIST)"}}' | tee publish.result.json | jq .
	@echo "✅ Verify"; \
	CID=$$(jq -r '(.cid // .root // empty)' publish.result.json); \
	curl -sS -I "$(IPFS_GATEWAY)/ipfs/$$CID/" | head -n1; \
	curl -sS "$(IPFS_GATEWAY)/ipfs/$$CID/index.html" | head -n 5

.PHONY: anchor
anchor:
	@test -f publish.result.json
	CID=$$(jq -r '(.cid // .root // empty)' publish.result.json); \
	SHA=$$(python3 scripts/hash_directory.py $(DIST)); \
	node scripts/xrpl-anchor-cid.mjs $$CID $$SHA | tee anchor.result.json

.PHONY: mint
mint:
	@test -f publish.result.json
	CID=$$(jq -r .cid publish.result.json); \
	node scripts/mint-token.mjs --note "ipfs://$$CID" --send

.PHONY: github-sync
github-sync:
	@if [ -f trustiva-registry.json ]; then \
	  git add trustiva-registry.json; \
	  git commit -m "update registry" || true; \
	  git push || true; \
	else \
	  echo "trustiva-registry.json not present; skipping"; \
	fi

.PHONY: up
up:
	docker compose up -d || docker-compose up -d
	@echo "Waiting for Ops API..."; \
	until curl -sf http://127.0.0.1:9000/healthz >/dev/null; do sleep 2; done; \
	echo "✅ Ops API ready."

.PHONY: down
down:
	docker compose down -v || docker-compose down -v

.PHONY: notify
notify:
	@test -f publish.result.json
	CID=$$(jq -r '(.cid // .root // empty)' publish.result.json); \
	if [ -n "$$SLACK_WEBHOOK" ]; then \
	  curl -sS -X POST "$$SLACK_WEBHOOK" -H 'Content-Type: application/json' \
	    -d "{\"text\": \"Trustiva: Published $$CID at $(IPFS_GATEWAY)/ipfs/$$CID/\"}" | cat; \
	fi; \
	if [ -n "$$ZOHO_OPS_URL" ]; then \
	  curl -sS -X POST "$$ZOHO_OPS_URL" -H 'Content-Type: application/json' \
	    -d "{\"to\": \"$${NOTIFY_EMAIL:-ops@example.com}\", \"subject\": \"New Trustiva Publish\", \"html\": \"CID $$CID\"}" | cat; \
	fi

.PHONY: bridge
bridge: anchor mint

.PHONY: verify-audit
verify-audit:
	@test -f publish.result.json
	CID=$$(jq -r '(.cid // .root // empty)' publish.result.json); \
	curl -sS http://127.0.0.1:9000/verify/cid/$$CID | jq .; \
	if [ -f anchor.result.json ]; then \
	  TX=$$(jq -r '.tx_hash // empty' anchor.result.json); \
	  [ -n "$$TX" ] && curl -sS http://127.0.0.1:9000/verify/polygon/$$TX | jq . || true; \
	fi; \
	curl -sS http://127.0.0.1:9000/registry | jq '.entries| length'

.PHONY: audit-bundle
audit-bundle:
	@test -f publish.result.json || test -f $(DIST)/publish.json
	CID=$$(jq -r '(.cid // .root // empty)' publish.result.json 2>/dev/null || jq -r '(.cid // .root // empty)' $(DIST)/publish.json); \
	curl -sS "http://127.0.0.1:9000/registry/resolve?cid=$$CID" | tee audit-bundle.json | jq .

.PHONY: audit-notify
audit-notify:
	@test -f audit-bundle.json
	if [ -n "$$SLACK_WEBHOOK" ]; then \
	  TEXT=$$(jq -r '"Proof for CID \(.cid): gateway \(.gateway.ok), sha256 \(.sha256 // .sha // "")"' audit-bundle.json); \
	  curl -sS -X POST "$$SLACK_WEBHOOK" -H 'Content-Type: application/json' -d "{\"text\": \"$$TEXT\"}" | cat; \
	fi

.PHONY: audit-sign
audit-sign:
	bash scripts/audit_sign.sh audit-bundle.json

.PHONY: audit-bot
audit-bot:
	@echo "CI workflow available: .github/workflows/audit-bot.yml"

.PHONY: kill
kill:
	-pkill -f "$(ORCH_APP)" || true
	-pkill -f "$(OPS_APP)" || true
	@# Windows fallback (ignored on *nix)
	-powershell -Command "Get-Process | ? { $$_.Path -like '*uvicorn*' } | Stop-Process -Force" 2>$$( [ -n "$$COMSPEC" ] && echo NUL || echo /dev/null )

.PHONY: clean
clean:
	rm -rf .pytest_cache __pycache__ **/__pycache__ *.pytest_cache
	rm -f publish.result.json $(DIST)/publish.json

# --- Proof Chain pipeline helpers ---
.PHONY: proof-hash
proof-hash:
	python3 scripts/hash_directory.py $(DIST) > $(DIST)/audit-bundle.json.sha256 || true

.PHONY: swarm-attest
swarm-attest:
	# Posts to swarm orchestrator or Ops API if it exposes /swarm/attest
	CID=$$(jq -r '(.cid // .root // empty)' $(DIST)/publish.json 2>/dev/null || echo ""); \
	ROOT=$$( [ -f $(DIST)/audit-bundle.json.sha256 ] && cat $(DIST)/audit-bundle.json.sha256 | tr -d '\n\r"' || jq -r '(.sha // .sha256 // empty)' $(DIST)/publish.json 2>/dev/null || echo "" ); \
	[[ $$ROOT == 0x* ]] || ROOT=0x$$ROOT; \
	curl -sS -X POST $${OPS_API_URL:-http://127.0.0.1:9000}/swarm/attest -H 'content-type: application/json' \
	  -d "{\"root\":\"$${ROOT}\",\"cid\":\"$${CID}\"}" | jq .

.PHONY: proof-submit
proof-submit:
	# Placeholder: wire to on-chain submission script when ready
	@test -f publish.result.json || test -f $(DIST)/publish.json
	CID=$$(jq -r '(.cid // .root // empty)' $(DIST)/publish.json 2>/dev/null || echo ""); \
	ROOT=$$( [ -f $(DIST)/audit-bundle.json.sha256 ] && cat $(DIST)/audit-bundle.json.sha256 | tr -d '\n\r"' || jq -r '(.sha // .sha256 // empty)' $(DIST)/publish.json 2>/dev/null || echo "" ); \
	[[ $$ROOT == 0x* ]] || ROOT=0x$$ROOT; \
	POI=$${POI:-$$(jq -r '.poi // empty' deploy.result.json 2>/dev/null)}; \
	REG=$${PROOFCHAIN_REGISTRY:-$$(jq -r '.registry // empty' deploy.result.json 2>/dev/null)}; \
	if [ -z "$$POI" ] || [ -z "$$REG" ]; then \
	  echo "Deploying local contracts..."; \
	  HARDHAT_CONFIG=hardhat.config.cjs npx hardhat compile; \
	  HARDHAT_CONFIG=hardhat.config.cjs npx hardhat run scripts/deploy-local.cjs --network localhost | tee deploy.result.json; \
	  POI=$$(jq -r '.poi' deploy.result.json); \
	  REG=$$(jq -r '.registry' deploy.result.json); \
	fi; \
	# ensure 0x prefix and correct 32-byte hex
	[[ $$ROOT == 0x* ]] || ROOT=0x$$ROOT; \
	ROOT=$$ROOT CID=$$CID POI=$$POI PROOFCHAIN_REGISTRY=$$REG \
	  HARDHAT_CONFIG=hardhat.config.cjs npx hardhat run scripts/proof-submit.cjs --network localhost | tee submit.result.json

.PHONY: pipeline
pipeline:
	$(MAKE) up
	@echo "Waiting for Ops API on :$(PORT_OPS)..."; \
	for i in $$(seq 1 30); do \
	  curl -sS http://127.0.0.1:$(PORT_OPS)/healthz >/dev/null 2>&1 && break; \
	  sleep 1; \
	done
	$(MAKE) publish
	$(MAKE) verify
	$(MAKE) audit-bundle
	$(MAKE) proof-hash
	$(MAKE) swarm-attest
	$(MAKE) proof-submit
