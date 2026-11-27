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

## Also: awesome-remote-mcp-servers (4,227 stars, updated 26 Nov 2026)
github.com/punkpeye/awesome-remote-mcp-servers is the list for hosted MCP servers (the bigger awesome-mcp-servers
only takes servers with a public repo). Its Monitoring section has Sentry; no AI-agent observability vendor is listed
(no Langfuse, Braintrust, Raindrop or Arize), so Agnost would be the first.

Requirements (from its CONTRIBUTING.md, 27 Nov 2026): public URL that answers MCP `initialize` (CI checks), usable
by anyone with public sign-up, Streamable HTTP or SSE, and a Glama connector listing (glama.ai/mcp/connectors) for the
required badge. One `initialize` request each, 27 Nov: mcp.agnost.ai/mcp answers 401 with
`WWW-Authenticate: Bearer ... resource_metadata="https://mcp.agnost.ai/.well-known/oauth-protected-resource"`, the
same shape as Sentry's listed endpoint, so it should pass the same way. I couldn't confirm a Glama listing (the search
page renders with scripts); check that first.

Entry for the Monitoring section (alphabetical; replace NAMESPACE/NAME with the Glama connector id once listed):

```markdown
- [Agnost AI](https://agnost.ai) `https://mcp.agnost.ai/mcp`
  [![Agnost AI MCP connector](https://glama.ai/mcp/connectors/NAMESPACE/NAME/badges/score.svg)](https://glama.ai/mcp/connectors/NAMESPACE/NAME)
  🔐 - Query production AI agent conversations, failing tools and failure patterns, and track fixes.
```
