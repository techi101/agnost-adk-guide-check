# List Agnost's hosted MCP server in the official MCP Registry

Checked 27 Nov 2026: registry.modelcontextprotocol.io has no Agnost entry (a search for "agnost" only returns
unrelated "agnostic" servers). Braintrust (`io.github.braintrustdata/braintrust`) and Raindrop (`io.raindrop/mcp`)
are listed. mcp.agnost.ai/mcp is live (401 without auth), streamable HTTP with OAuth 2.1 dynamic client registration
(docs.agnost.ai/agnost-mcp-server), so the entry needs no keys or headers, only the URL.

`server.json` in this folder validates against the official schema
(static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json, the version Braintrust's entry uses): 0 errors;
description 96 of 100 characters.

## Publish (about 15 minutes; needs DNS access to agnost.ai)
Steps from the registry's own docs (modelcontextprotocol/registry, docs/modelcontextprotocol-io/authentication.mdx).
The name `ai.agnost/mcp` uses domain authentication, so it must be published by someone who controls agnost.ai DNS.

```bash
MY_DOMAIN="agnost.ai"
# 1. key pair (OpenSSL 3+)
openssl genpkey -algorithm Ed25519 -out key.pem
PUBLIC_KEY="$(openssl pkey -in key.pem -pubout -outform DER | tail -c 32 | base64)"
echo "${MY_DOMAIN}. IN TXT \"v=MCPv1; k=ed25519; p=${PUBLIC_KEY}\""
# 2. add that TXT record on the apex (agnost.ai, not a subdomain); wait for it to propagate
# 3. log in and publish from this folder
MCP_PRIVATE_KEY="$(openssl pkey -in key.pem -noout -text | sed -n '/priv:/,/pub:/p' | sed '1d;$d' | tr -d ' :\n')" \
  mcp-publisher login dns --domain "${MY_DOMAIN}"
mcp-publisher publish
```

Keep `key.pem` out of git. The registry is in preview; its docs warn of possible data resets before general availability.

Why it matters: MCP clients and directories read the registry to discover servers, and two direct competitors are
already there. The listing points developers at the same OAuth flow the docs describe.
