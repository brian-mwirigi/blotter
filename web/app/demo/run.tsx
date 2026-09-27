"use client";

import Link from "next/link";
import { FormEvent, useEffect, useRef, useState } from "react";

type Row = {
  supplier: string;
  invoice: string;
  received: string;
  status: string;
  tone: string;
};

type Line =
  | { id: number; kind: "note"; tone: string; text: string }
  | { id: number; kind: "code"; text: string }
  | { id: number; kind: "trace"; text: string };

type Result = {
  mode: string;
  headline: string;
  detail: string;
  matched: number;
  anomalies: number;
  rows: Row[];
};

type FileText = { name: string; text: string; sample: boolean };

const MODE: Record<string, string> = {
  healed: "Healed on retry",
  clean: "Clean pass",
  fallback: "Fallback",
};

export function DemoRun({
  sampleInvoices,
  sampleStatement,
}: {
  sampleInvoices: string;
  sampleStatement: string;
}) {
  const [invoices, setInvoices] = useState<FileText>({
    name: "supplier_invoices.csv",
    text: sampleInvoices,
    sample: true,
  });
  const [statement, setStatement] = useState<FileText>({
    name: "mock_mpesa_statement.json",
    text: sampleStatement,
    sample: true,
  });
  const [lines, setLines] = useState<Line[]>([]);
  const [attempt, setAttempt] = useState<number | null>(null);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<Result | null>(null);
  const [engine, setEngine] = useState("");
  const nextId = useRef(0);
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const node = logRef.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [lines]);

  function push(line: Omit<Line, "id">) {
    nextId.current += 1;
    const id = nextId.current;
    setLines((current) => [...current, { ...line, id } as Line]);
  }

  async function readFile(file: File, setFile: (value: FileText) => void) {
    setFile({ name: file.name, text: await file.text(), sample: false });
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (running) return;
    setRunning(true);
    setLines([]);
    setResult(null);
    setAttempt(1);
    setEngine("");
    nextId.current = 0;
    const body = new FormData();
    body.append("invoices", new File([invoices.text], invoices.name, { type: "text/csv" }));
    body.append("statement", new File([statement.text], statement.name, { type: "application/json" }));
    try {
      const response = await fetch("/api/reconcile", { method: "POST", body });
      if (!response.ok || !response.body) {
        push({
          kind: "note",
          tone: "error",
          text: "Error: the reconcile service did not answer.",
        });
        return;
      }
      const type = response.headers.get("content-type") || "";
      if (type.includes("application/json")) {
        const payload = (await response.json()) as { error?: string };
        push({ kind: "note", tone: "error", text: payload.error || "Error: the run failed." });
        return;
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const chunk = await reader.read();
        if (chunk.done) break;
        buffer += decoder.decode(chunk.value, { stream: true });
        const blocks = buffer.split("\n\n");
        buffer = blocks.pop() ?? "";
        for (const block of blocks) {
          const data = block
            .split("\n")
            .filter((item) => item.startsWith("data:"))
            .map((item) => item.slice(5).trim())
            .join("");
          if (!data) continue;
          const payload = JSON.parse(data) as {
            kind: string;
            tone?: string;
            text?: string;
            iteration?: number;
            engine?: string;
            model?: string;
            mode?: string;
            headline?: string;
            detail?: string;
            matched?: number;
            anomalies?: number;
            rows?: Row[];
          };
          if (payload.kind === "meta") {
            setEngine(payload.engine === "nvidia" ? payload.model || "NVIDIA" : "Local sandbox");
          } else if (payload.kind === "attempt" && payload.iteration) {
            setAttempt(payload.iteration);
          } else if (payload.kind === "note" && payload.text) {
            push({ kind: "note", tone: payload.tone || "info", text: payload.text });
          } else if (payload.kind === "code" && payload.text) {
            push({ kind: "code", text: payload.text });
          } else if (payload.kind === "trace" && payload.text) {
            push({ kind: "trace", text: payload.text });
          } else if (payload.kind === "result") {
            setResult({
              mode: payload.mode || "clean",
              headline: payload.headline || "",
              detail: payload.detail || "",
              matched: payload.matched || 0,
              anomalies: payload.anomalies || 0,
              rows: payload.rows || [],
            });
          }
        }
      }
    } catch {
      push({ kind: "note", tone: "error", text: "Error: the run stopped before a ledger." });
    } finally {
      setRunning(false);
    }
  }

  const usingSample = invoices.sample && statement.sample;
  const attemptClass = result ? "attempt done" : attempt && attempt > 1 ? "attempt retry" : "attempt";

  return (
    <>
      <header className="nav">
        <Link className="logo" href="/">
          <i />
          Blotter
        </Link>
        <nav className="nav-links">
          <Link href="/#faq">FAQ</Link>
          <span>Live demo</span>
        </nav>
      </header>
      <main className="section demo">
        <div className="wrap">
          <p className="eyebrow">Live demo</p>
          <h1>Reconcile this day.</h1>
          <p className="lead">
            The sample invoices and the mobile-money statement are already loaded. Reconcile
            runs them in the sandbox and keeps the attempt count on screen.
          </p>
          <form className="uploads" onSubmit={onSubmit}>
            <label className="file">
              <span>Supplier invoices</span>
              <strong>{invoices.name}</strong>
              <em>{invoices.sample ? "Sample loaded" : "Uploaded"} · Replace</em>
              <input
                className="file-input"
                type="file"
                accept=".csv,text/csv"
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) void readFile(file, setInvoices);
                }}
              />
            </label>
            <label className="file">
              <span>M-Pesa statement</span>
              <strong>{statement.name}</strong>
              <em>{statement.sample ? "Sample loaded" : "Uploaded"} · Replace</em>
              <input
                className="file-input"
                type="file"
                accept=".json,application/json"
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) void readFile(file, setStatement);
                }}
              />
            </label>
            <div className="upload-actions">
              <button className="btn" type="submit" disabled={running}>
                {running ? "Reconciling…" : "Reconcile"}
              </button>
              {usingSample ? null : (
                <button
                  className="btn ghost"
                  type="button"
                  onClick={() => {
                    setInvoices({
                      name: "supplier_invoices.csv",
                      text: sampleInvoices,
                      sample: true,
                    });
                    setStatement({
                      name: "mock_mpesa_statement.json",
                      text: sampleStatement,
                      sample: true,
                    });
                  }}
                >
                  Use the sample files
                </button>
              )}
            </div>
          </form>

          <div className="demo-grid">
            <section className="log-panel" aria-label="Reconcile log">
              <header>
                <strong>Run</strong>
                <span className={attemptClass}>
                  {attempt ? `Attempt ${attempt} of 3` : "3 attempts max"}
                </span>
              </header>
              <div className="log" ref={logRef} aria-live="polite">
                {lines.length === 0 ? (
                  <p className="info">The log fills in as the script is written and run.</p>
                ) : (
                  lines.map((line) => {
                    if (line.kind === "code") {
                      return (
                        <pre key={line.id}>
                          <span className="log-label">Generated script</span>
                          {line.text}
                        </pre>
                      );
                    }
                    if (line.kind === "trace") {
                      return (
                        <pre key={line.id} className="trace">
                          <span className="log-label">Traceback</span>
                          {line.text}
                        </pre>
                      );
                    }
                    return (
                      <p key={line.id} className={line.tone}>
                        {line.text}
                      </p>
                    );
                  })
                )}
              </div>
              <footer>{engine || "Waiting for a run"}</footer>
            </section>

            <section className="result-panel">
              {result ? (
                <>
                  <p className="eyebrow">{MODE[result.mode] || result.mode}</p>
                  <h2>{result.headline}</h2>
                  {result.detail ? <p className="detail">{result.detail}</p> : null}
                  <p className="counts">
                    <strong>{result.matched}</strong> reconciled
                    <span>·</span>
                    <strong>{result.anomalies}</strong> flagged
                  </p>
                  <div className="product-frame">
                    <table className="sheet">
                      <thead>
                        <tr>
                          <th>Supplier</th>
                          <th className="num">Invoice</th>
                          <th className="num">Received</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {result.rows.map((row) => (
                          <tr key={row.supplier} className={row.tone || undefined}>
                            <td>{row.supplier}</td>
                            <td className="num">{row.invoice}</td>
                            <td className="num">{row.received}</td>
                            <td>{row.status}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              ) : (
                <div className="result-empty">
                  <p className="eyebrow">Result</p>
                  <h2>The shortfall shows up here.</h2>
                  <p>Reconciled count, flagged rows, and the open amount, after the run.</p>
                </div>
              )}
              <p className="caption">Synthetic sample. No payment is sent.</p>
            </section>
          </div>
        </div>
      </main>
    </>
  );
}
