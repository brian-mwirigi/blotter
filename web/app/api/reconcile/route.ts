export async function POST(request: Request) {
  try {
    const incoming = await request.formData();
    const body = new FormData();
    for (const [key, value] of incoming.entries()) {
      body.append(key, value);
    }
    const upstream = await fetch("http://127.0.0.1:8000/reconcile", {
      method: "POST",
      body,
    });
    return new Response(upstream.body, {
      status: upstream.status,
      headers: {
        "Content-Type": upstream.headers.get("content-type") || "text/event-stream",
        "Cache-Control": "no-cache",
      },
    });
  } catch {
    return Response.json(
      { error: "The reconcile service is not running." },
      { status: 502 },
    );
  }
}
