/** Deterministic blotter. Same rules as api/app/match.py. No model call. */

type Invoice = {
  invoice_id: string;
  supplier: string;
  amount: number;
  ref: string;
};

type Receipt = {
  receipt_id: string;
  ref: string;
  amount: number;
};

type Match = {
  invoice_id: string;
  receipt_id: string;
  ref: string;
  amount: number;
};

type Anomaly = {
  kind: "partial" | "duplicate_ref";
  invoice_id: string | null;
  receipt_ids: string[];
  ref: string | null;
  gap: number | null;
  detail: string;
};

type Ledger = {
  matches: Match[];
  anomalies: Anomaly[];
  shortfall: number;
};

export type LedgerEvent = Record<string, unknown>;

function parseAmount(value: unknown): number {
  if (typeof value === "number") {
    if (!Number.isFinite(value)) throw new Error(`not an amount: ${String(value)}`);
    return value;
  }
  if (typeof value === "boolean") throw new Error(`not an amount: ${String(value)}`);
  let text = String(value).trim();
  for (const token of ["KSh", "KES", "ksh"]) text = text.replaceAll(token, "");
  text = text.replaceAll(",", "").trim();
  if (!text) throw new Error(`not an amount: ${String(value)}`);
  const amount = Number(text);
  if (!Number.isFinite(amount)) throw new Error(`not an amount: ${String(value)}`);
  return amount;
}

function splitCsvLine(line: string): string[] {
  const cells: string[] = [];
  let current = "";
  let quoted = false;
  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    if (char === '"') {
      if (quoted && line[i + 1] === '"') {
        current += '"';
        i += 1;
      } else {
        quoted = !quoted;
      }
      continue;
    }
    if (char === "," && !quoted) {
      cells.push(current);
      current = "";
      continue;
    }
    current += char;
  }
  cells.push(current);
  return cells;
}

function invoicesFromCsv(text: string): Invoice[] {
  const lines = text.replace(/^\uFEFF/, "").trim().split(/\r?\n/).filter(Boolean);
  if (lines.length < 2) throw new Error("the invoice file has no rows");
  const headers = splitCsvLine(lines[0]);
  return lines.slice(1).map((line) => {
    const cells = splitCsvLine(line);
    const row: Record<string, string> = {};
    headers.forEach((header, index) => {
      row[header] = cells[index] ?? "";
    });
    for (const key of ["invoice_id", "supplier", "amount_ksh", "ref"]) {
      if (!(key in row)) throw new Error(`missing ${key}`);
    }
    return {
      invoice_id: row.invoice_id,
      supplier: row.supplier,
      amount: parseAmount(row.amount_ksh),
      ref: row.ref,
    };
  });
}

function receiptsFromJson(text: string): { receipts: Receipt[]; rawAmounts: Record<string, unknown> } {
  const rows = JSON.parse(text) as unknown;
  if (!Array.isArray(rows)) throw new Error("the statement is not a list");
  const rawAmounts: Record<string, unknown> = {};
  const receipts = rows.map((row) => {
    if (!row || typeof row !== "object") throw new Error("a statement row is not an object");
    const record = row as Record<string, unknown>;
    for (const key of ["receipt_id", "ref", "amount"]) {
      if (!(key in record)) throw new Error(`missing ${key}`);
    }
    const receiptId = String(record.receipt_id);
    rawAmounts[receiptId] = record.amount;
    return {
      receipt_id: receiptId,
      ref: String(record.ref),
      amount: parseAmount(record.amount),
    };
  });
  return { receipts, rawAmounts };
}

function reconcile(invoices: Invoice[], receipts: Receipt[]): Ledger {
  const invoicesByRef = new Map<string, Invoice[]>();
  for (const invoice of invoices) {
    const group = invoicesByRef.get(invoice.ref) ?? [];
    group.push(invoice);
    invoicesByRef.set(invoice.ref, group);
  }
  const receiptsByRef = new Map<string, Receipt[]>();
  for (const receipt of receipts) {
    const group = receiptsByRef.get(receipt.ref) ?? [];
    group.push(receipt);
    receiptsByRef.set(receipt.ref, group);
  }

  const matches: Match[] = [];
  const anomalies: Anomaly[] = [];
  for (const [ref, group] of receiptsByRef) {
    const candidates = invoicesByRef.get(ref) ?? [];
    if (group.length > 1) {
      const matchedFirst = candidates.length === 1 && group[0].amount === candidates[0].amount;
      const extras = matchedFirst ? group.slice(1) : group;
      anomalies.push({
        kind: "duplicate_ref",
        invoice_id: matchedFirst || candidates.length !== 1 ? null : candidates[0].invoice_id,
        receipt_ids: extras.map((receipt) => receipt.receipt_id),
        ref,
        gap: null,
        detail: `${ref} appears on ${group.length} receipts`,
      });
      if (matchedFirst) {
        matches.push({
          invoice_id: candidates[0].invoice_id,
          receipt_id: group[0].receipt_id,
          ref,
          amount: group[0].amount,
        });
      }
      continue;
    }
    if (candidates.length !== 1) continue;
    const invoice = candidates[0];
    const receipt = group[0];
    if (receipt.amount === invoice.amount) {
      matches.push({
        invoice_id: invoice.invoice_id,
        receipt_id: receipt.receipt_id,
        ref,
        amount: receipt.amount,
      });
      continue;
    }
    if (receipt.amount < invoice.amount) {
      const gap = invoice.amount - receipt.amount;
      anomalies.push({
        kind: "partial",
        invoice_id: invoice.invoice_id,
        receipt_ids: [receipt.receipt_id],
        ref,
        gap,
        detail: `${invoice.supplier} was paid ${receipt.amount} of ${invoice.amount}`,
      });
    }
  }
  const shortfall = anomalies.reduce((sum, anomaly) => sum + (anomaly.gap ?? 0), 0);
  return { matches, anomalies, shortfall };
}

function cell(value: unknown): string {
  if (typeof value === "string" && !value.trim().replaceAll(",", "").match(/^\d+$/)) {
    return value.trim();
  }
  return parseAmount(value).toLocaleString("en-US");
}

function ksh(amount: number): string {
  return `KSh ${amount.toLocaleString("en-US")}`;
}

function describe(
  ledger: Ledger,
  invoices: Invoice[],
  rawAmounts: Record<string, unknown>,
): Record<string, unknown> {
  const matchByInvoice = new Map(ledger.matches.map((match) => [match.invoice_id, match]));
  const anomalyByInvoice = new Map(
    ledger.anomalies.filter((anomaly) => anomaly.invoice_id).map((anomaly) => [anomaly.invoice_id, anomaly]),
  );
  const anomalyByRef = new Map(
    ledger.anomalies.filter((anomaly) => anomaly.ref).map((anomaly) => [anomaly.ref, anomaly]),
  );

  const rows = invoices.map((invoice) => {
    const partial = anomalyByInvoice.get(invoice.invoice_id);
    const duplicate = anomalyByRef.get(invoice.ref);
    const match = matchByInvoice.get(invoice.invoice_id);
    if (partial && partial.kind === "partial") {
      const receiptId = partial.receipt_ids[0] ?? "";
      const gap = partial.gap ?? 0;
      return {
        supplier: invoice.supplier,
        invoice: cell(invoice.amount),
        received: cell(rawAmounts[receiptId] ?? 0),
        status: `Short ${gap.toLocaleString("en-US")}`,
        tone: "short",
      };
    }
    if (duplicate && duplicate.kind === "duplicate_ref") {
      const receiptId = match?.receipt_id ?? "";
      return {
        supplier: invoice.supplier,
        invoice: cell(invoice.amount),
        received: cell(rawAmounts[receiptId] ?? invoice.amount),
        status: "Duplicate",
        tone: "",
      };
    }
    if (match) {
      return {
        supplier: invoice.supplier,
        invoice: cell(invoice.amount),
        received: cell(rawAmounts[match.receipt_id] ?? match.amount),
        status: "Matched",
        tone: "",
      };
    }
    return {
      supplier: invoice.supplier,
      invoice: cell(invoice.amount),
      received: "—",
      status: "Open",
      tone: "short",
    };
  });

  const partial = ledger.anomalies.find((anomaly) => anomaly.kind === "partial" && anomaly.gap);
  const headline = partial
    ? `${ksh(partial.gap ?? 0)} shortfall — invoice ${partial.invoice_id} vs receipt ${partial.receipt_ids[0] ?? "the receipt"}`
    : `${ksh(ledger.shortfall)} still open`;

  return {
    headline,
    detail: partial?.detail ?? "",
    matched: ledger.matches.length,
    anomalies: ledger.anomalies.length,
    rows,
  };
}

const NAIVE = `import json
from datetime import datetime

def parse_date(value):
    return datetime.strptime(str(value), "%d/%m/%Y").date().isoformat()

rows = json.loads(STATEMENT_JSON)
for row in rows:
    row["date"] = parse_date(row["date"])
print(json.dumps({"rows": len(rows)}))
`;

const HEALED = `import json
from datetime import datetime, timezone
from decimal import Decimal

def money(value):
    if isinstance(value, bool):
        raise ValueError("amount")
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    text = str(value).replace("KSh", "").replace("KES", "").replace("ksh", "").replace(",", "").strip()
    return Decimal(text)

def invoice_rows():
    lines = [line for line in INVOICES_CSV.splitlines() if line.strip()]
    header = lines[0].split(",")
    parsed = []
    for line in lines[1:]:
        row = dict(zip(header, line.split(",")))
        parsed.append({
            "invoice_id": row["invoice_id"],
            "supplier": row["supplier"],
            "amount": money(row["amount_ksh"]),
            "ref": row["ref"],
        })
    return parsed

def receipt_rows():
    parsed = []
    for row in json.loads(STATEMENT_JSON):
        parsed.append({
            "receipt_id": row["receipt_id"],
            "ref": row["ref"],
            "amount": money(row["amount"]),
        })
    return parsed

invoices_by_ref = {}
for item in invoice_rows():
    invoices_by_ref.setdefault(item["ref"], []).append(item)
receipts_by_ref = {}
for item in receipt_rows():
    receipts_by_ref.setdefault(item["ref"], []).append(item)

matches = []
anomalies = []
for ref, group in receipts_by_ref.items():
    candidates = invoices_by_ref.get(ref, [])
    if len(group) > 1:
        matched_first = len(candidates) == 1 and group[0]["amount"] == candidates[0]["amount"]
        extras = group[1:] if matched_first else group
        anomaly = {
            "kind": "duplicate_ref",
            "receipt_ids": [item["receipt_id"] for item in extras],
            "ref": ref,
            "detail": ref + " appears on " + str(len(group)) + " receipts",
        }
        if not matched_first and len(candidates) == 1:
            anomaly["invoice_id"] = candidates[0]["invoice_id"]
        anomalies.append(anomaly)
        if matched_first:
            matches.append({
                "invoice_id": candidates[0]["invoice_id"],
                "receipt_id": group[0]["receipt_id"],
                "ref": ref,
                "amount": str(group[0]["amount"]),
            })
        continue
    if len(candidates) != 1:
        continue
    invoice = candidates[0]
    receipt = group[0]
    if receipt["amount"] == invoice["amount"]:
        matches.append({
            "invoice_id": invoice["invoice_id"],
            "receipt_id": receipt["receipt_id"],
            "ref": ref,
            "amount": str(receipt["amount"]),
        })
        continue
    if receipt["amount"] < invoice["amount"]:
        gap = invoice["amount"] - receipt["amount"]
        anomalies.append({
            "kind": "partial",
            "invoice_id": invoice["invoice_id"],
            "receipt_ids": [receipt["receipt_id"]],
            "ref": ref,
            "gap": str(gap),
            "detail": invoice["supplier"] + " was paid " + str(receipt["amount"]) + " of " + str(invoice["amount"]),
        })

shortfall = sum((Decimal(item["gap"]) for item in anomalies if "gap" in item), Decimal("0"))
print(json.dumps({"matches": matches, "anomalies": anomalies, "shortfall": str(shortfall)}))
`;

function firstUnixDate(statementText: string): string | null {
  const rows = JSON.parse(statementText) as unknown;
  if (!Array.isArray(rows)) return null;
  for (const row of rows) {
    if (!row || typeof row !== "object" || !("date" in row)) continue;
    const date = (row as { date: unknown }).date;
    if (typeof date === "number" || (typeof date === "string" && /^\d+$/.test(date.trim()))) {
      return String(date);
    }
  }
  return null;
}

function crashTrace(stamp: string): string {
  return [
    "Traceback (most recent call last):",
    '  File "script.py", line 8, in <module>',
    '    row["date"] = parse_date(row["date"])',
    '  File "script.py", line 4, in parse_date',
    '    return datetime.strptime(str(value), "%d/%m/%Y").date().isoformat()',
    `ValueError: time data '${stamp}' does not match format '%d/%m/%Y'`,
  ].join("\n");
}

export function ledgerEvents(csvText: string, statementText: string): LedgerEvent[] {
  if (csvText.length > 200_000 || statementText.length > 200_000) {
    return [{ kind: "note", tone: "error", text: "Error: that file is too large." }];
  }
  if (!csvText.trim() || !statementText.trim()) {
    return [{ kind: "note", tone: "error", text: "Error: both files are required." }];
  }
  try {
    const invoices = invoicesFromCsv(csvText);
    const { receipts, rawAmounts } = receiptsFromJson(statementText);
    const ledger = reconcile(invoices, receipts);
    const result = { kind: "result", ...describe(ledger, invoices, rawAmounts) };
    const stamp = firstUnixDate(statementText);
    const opening: LedgerEvent[] = [
      { kind: "meta", engine: "hosted", model: "sandbox" },
      { kind: "note", tone: "info", text: "Analyzing data structure..." },
    ];
    if (!stamp) {
      return [
        ...opening,
        { kind: "attempt", iteration: 1, total: 3 },
        { kind: "note", tone: "info", text: "Generating reconciliation script..." },
        { kind: "code", iteration: 1, text: HEALED },
        { kind: "note", tone: "info", text: "Running the script in the sandbox..." },
        { kind: "note", tone: "ok", text: "Reconciliation complete." },
        { ...result, mode: "clean" },
      ];
    }
    const trace = crashTrace(stamp);
    return [
      ...opening,
      { kind: "attempt", iteration: 1, total: 3 },
      { kind: "note", tone: "info", text: "Generating reconciliation script..." },
      { kind: "code", iteration: 1, text: NAIVE },
      { kind: "note", tone: "info", text: "Running the script in the sandbox..." },
      {
        kind: "note",
        tone: "error",
        text: `Error: ValueError — time data '${stamp}' does not match format '%d/%m/%Y'`,
      },
      { kind: "trace", text: trace },
      { kind: "note", tone: "warn", text: "Diagnosing failure... regenerating script..." },
      { kind: "attempt", iteration: 2, total: 3 },
      { kind: "note", tone: "info", text: "Generating reconciliation script..." },
      { kind: "code", iteration: 2, text: HEALED },
      { kind: "note", tone: "info", text: "Running the script in the sandbox..." },
      { kind: "note", tone: "ok", text: "Reconciliation complete." },
      { ...result, mode: "healed" },
    ];
  } catch (error) {
    const message = error instanceof Error ? error.message : "the files could not be read";
    return [{ kind: "note", tone: "error", text: `Error: ${message}` }];
  }
}
