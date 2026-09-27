import { ledgerEvents } from "@/lib/ledger";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 300;

function hosted(csvText: string, statementText: string) {
  const events = ledgerEvents(csvText, statementText);
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    async start(controller) {
      for (const event of events) {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(event)}\n\n`));
        const kind = String(event.kind);
        const wait = kind === "result" ? 0 : kind === "code" || kind === "trace" ? 800 : 500;
        if (wait) await new Promise((resolve) => setTimeout(resolve, wait));
      }
      controller.close();
    },
  });
  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      "X-Accel-Buffering": "no",
    },
  });
}

async function localStream(
  csvText: string,
  statementText: string,
  base = "http://127.0.0.1:8000",
): Promise<Response | null> {
  const body = new FormData();
  body.append("invoices", new Blob([csvText], { type: "text/csv" }), "invoices.csv");
  body.append("statement", new Blob([statementText], { type: "application/json" }), "statement.json");
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), base.startsWith("http://127.0.0.1") ? 1500 : 240_000);
  try {
    const upstream = await fetch(new URL("/reconcile", base), {
      method: "POST",
      body,
      signal: controller.signal,
    });
    clearTimeout(timer);
    const type = upstream.headers.get("content-type") || "";
    if (!upstream.ok || !upstream.body || type.includes("application/json")) return null;
    return new Response(upstream.body, {
      status: upstream.status,
      headers: {
        "Content-Type": type || "text/event-stream",
        "Cache-Control": "no-cache",
      },
    });
  } catch {
    clearTimeout(timer);
    return null;
  }
}

export async function POST(request: Request) {
  try {
    const incoming = await request.formData();
    const invoices = incoming.get("invoices");
    const statement = incoming.get("statement");
    if (!(invoices instanceof File) || !(statement instanceof File)) {
      return Response.json({ error: "Both files are required." }, { status: 400 });
    }
    const csvText = await invoices.text();
    const statementText = await statement.text();
    const remote = process.env.RECONCILE_UPSTREAM?.trim();
    if (remote) {
      const streamed = await localStream(csvText, statementText, remote);
      if (streamed) return streamed;
      return Response.json({ error: "Composer did not answer." }, { status: 502 });
    }
    if (!process.env.VERCEL) {
      const local = await localStream(csvText, statementText);
      if (local) return local;
    }
    return hosted(csvText, statementText);
  } catch {
    return Response.json({ error: "The reconcile service is not running." }, { status: 502 });
  }
}
