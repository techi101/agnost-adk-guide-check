// Mastra -> Agnost guide, end-to-end test against a local OTLP receiver (receiver.py).
// Uses the exact OtelExporter config from agnost-mastra-guide.md, with the endpoint swapped to localhost.
// The model is MockLanguageModelV3 from ai/test: first call asks for a tool, second call answers. No API key.
import { Mastra } from "@mastra/core/mastra";
import { Agent } from "@mastra/core/agent";
import { createTool } from "@mastra/core/tools";
import { Observability } from "@mastra/observability";
import { OtelExporter } from "@mastra/otel-exporter";
import { MockLanguageModelV3 } from "ai/test";
import { z } from "zod";

const ENDPOINT = process.env.TEST_ENDPOINT ?? "http://127.0.0.1:4321/v1/traces";
const usage = { inputTokens: { total: 10, noCache: 10 }, outputTokens: { total: 5, text: 5 } };

let call = 0;
const model = new MockLanguageModelV3({
  doGenerate: async () => {
    call += 1;
    if (call === 1) {
      return {
        content: [{ type: "tool-call", toolCallId: "tc1", toolName: "getOrderStatus", input: JSON.stringify({ orderId: "A-1042" }) }],
        finishReason: { unified: "tool-calls", raw: "tool_calls" }, usage, warnings: [],
      };
    }
    return {
      content: [{ type: "text", text: "Your order A-1042 has shipped." }],
      finishReason: { unified: "stop", raw: "stop" }, usage, warnings: [],
    };
  },
});

const getOrderStatus = createTool({
  id: "getOrderStatus",
  description: "Look up an order's shipping status",
  inputSchema: z.object({ orderId: z.string() }),
  execute: async (input) => ({ status: "shipped", orderId: input.orderId ?? input.context?.orderId }),
});

const supportAgent = new Agent({
  id: "support-agent",
  name: "support-agent",
  instructions: "Answer order questions using getOrderStatus.",
  model,
  tools: { getOrderStatus },
});

export const mastra = new Mastra({
  agents: { supportAgent },
  observability: new Observability({
    configs: {
      otel: {
        serviceName: "support-agent",
        exporters: [
          new OtelExporter({
            provider: {
              custom: {
                endpoints: { traces: ENDPOINT },
                protocol: "http/protobuf",
                headers: { "X-Agnost-Org-ID": "test-org-id" },
              },
            },
          }),
        ],
      },
    },
  }),
});

const agent = mastra.getAgent("supportAgent");
const res = await agent.generate("Where is my order A-1042?", { tracingOptions: { metadata: { threadId: "session-abc", userId: "user-42" } } });
console.log("agent answer:", res.text, "| model calls:", call, "| traceId:", res.traceId);
await new Promise((r) => setTimeout(r, 6000)); // batch exporter interval before shutdown
await mastra.shutdown?.();
await new Promise((r) => setTimeout(r, 3000)); // let the batch exporter flush
console.log("done");
process.exit(0);
