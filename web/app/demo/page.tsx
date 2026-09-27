import { readFileSync } from "node:fs";
import path from "node:path";
import { DemoRun } from "./run";

function readSample(name: string) {
  const candidates = [
    path.join(process.cwd(), "..", "data", name),
    path.join(process.cwd(), "data", name),
  ];
  for (const file of candidates) {
    try {
      return readFileSync(file, "utf8");
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") throw error;
    }
  }
  throw new Error(`Missing sample file ${name}`);
}

export default function Demo() {
  return (
    <DemoRun
      sampleInvoices={readSample("supplier_invoices.csv")}
      sampleStatement={readSample("mock_mpesa_statement.json")}
    />
  );
}
