---
title: "Mastra"
description: "Export Mastra agent traces to Agnost AI with Mastra's OpenTelemetry exporter"
draft: true
---

<!-- Draft for docs.agnost.ai, 27 Nov 2026.
Tested locally: @mastra/core 1.86.0, @mastra/otel-exporter 1.6.2, @mastra/observability 1.24.3, ai 7.0.183 (scripted
MockLanguageModelV3, one tool call), exporting to a local OTLP receiver that stands in for otel.agnost.ai.
Result: one OTLP/HTTP protobuf post to /v1/traces (chunked transfer encoding) with the X-Agnost-Org-ID header; 15 spans:
invoke_agent (root) > agent_step > chat (gen_ai.input.messages, gen_ai.output.messages, usage) and execute_tool
(gen_ai.tool.name, call.arguments, call.result). tracingOptions.metadata.threadId became gen_ai.conversation.id on all
15 spans; other metadata keys arrive as mastra.metadata.<key>.
NOT tested against Agnost's endpoint. Two things only Agnost can confirm: (1) that its Mastra support builds the
transcript from the chat spans, since the root invoke_agent span carries no messages; (2) whether it reads a user id from
mastra.metadata.userId (no standard user attribute is emitted). Test files: channels/mastra/test/. -->

Mastra emits OpenTelemetry spans for agent runs, model calls and tool calls through `@mastra/otel-exporter`.
Point its `custom` provider at Agnost AI; no Agnost SDK is required.

## 1. Install

```bash
npm install @mastra/otel-exporter @mastra/observability @opentelemetry/exporter-trace-otlp-proto
```

The OTel exporter needs a protocol package; Agnost AI ingests OTLP over HTTP/protobuf.

## 2. Configure the exporter

```typescript
import { Mastra } from '@mastra/core/mastra';
import { Observability } from '@mastra/observability';
import { OtelExporter } from '@mastra/otel-exporter';

export const mastra = new Mastra({
  agents: { supportAgent },
  observability: new Observability({
    configs: {
      otel: {
        serviceName: 'support-agent',
        exporters: [
          new OtelExporter({
            provider: {
              custom: {
                endpoints: { traces: 'https://otel.agnost.ai/v1/traces' },
                protocol: 'http/protobuf',
                headers: { 'X-Agnost-Org-ID': process.env.AGNOST_ORG_ID! },
              },
            },
          }),
        ],
      },
    },
  }),
});
```

Copy your Organization ID from **Settings** in [app.agnost.ai](https://app.agnost.ai). Call agents through the
`mastra` instance (`mastra.getAgent(...)`) so tracing applies.

## 3. Group turns into conversations

Pass a stable conversation id as `threadId` on each call. The exporter writes it to `gen_ai.conversation.id` on every
span of the run, so all turns with the same id land in one Agnost AI conversation:

```typescript
const agent = mastra.getAgent('supportAgent');
await agent.generate(userMessage, {
  tracingOptions: { metadata: { threadId: conversationId, userId } },
});
```

## 4. Verify

Run one conversation, then open **Conversations** in Agnost AI and check that the turn shows the user message, the
answer, and any tool calls with their arguments and results.

## Troubleshooting
- `Custom configuration requires endpoint or at least one signal in endpoints`: `endpoints.traces` is missing.
- Use `endpoints.traces` (the exact URL) rather than the legacy `endpoint` field so the `/v1/traces` path is not altered.
- Each conversation shows one turn only: `threadId` is missing or changes per call.
- A short script exits before spans are sent: wait a few seconds or call `mastra.shutdown()` before exiting; the
  exporter batches spans.
