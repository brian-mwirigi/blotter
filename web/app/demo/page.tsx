import { readFileSync } from "node:fs";
import path from "node:path";
import { DemoRun } from "./run";

export default function Demo() {
  const root = path.join(process.cwd(), "..", "data");
  const sampleInvoices = readFileSync(path.join(root, "supplier_invoices.csv"), "utf8");
  const sampleStatement = readFileSync(path.join(root, "mock_mpesa_statement.json"), "utf8");
  return <DemoRun sampleInvoices={sampleInvoices} sampleStatement={sampleStatement} />;
}
