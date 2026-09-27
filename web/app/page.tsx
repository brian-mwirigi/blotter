import Link from "next/link";
import { BlotterTable } from "./blotter";

const faqs = [
  {
    q: "Does Blotter send the money?",
    a: "No. It shows what is still open. A person decides what to pay. The sample day does not move any funds.",
  },
  {
    q: "What do I give it?",
    a: "A supplier invoice file and a mobile-money statement. In the demo those are a CSV and a JSON export, with mixed dates and one amount written as “KSh 4,500”.",
  },
  {
    q: "What if the statement format breaks the first script?",
    a: "The generated script runs in a subprocess with an import allowlist and a five-second timeout. If it crashes, or if the totals do not tie, the error goes back and the script is rewritten. Three tries, then the ledger is marked Needs review.",
  },
  {
    q: "Is the shop data real?",
    a: "No. Amani Hardware, the KSh 18,000 invoice, and the KSh 13,500 receipt are a synthetic sample. There are no customer phone numbers.",
  },
  {
    q: "How does Blotter handle data privacy and AI oversight?",
    a: "Uploads are read for that request only. The generated script is written in an isolated temporary directory that is destroyed when the run finishes. Blotter does not store the files. Uploaded file contents are included in the AI model call required to generate the reconciliation script; Blotter does not control data retention on the model provider's side. Reconcile stays off until you acknowledge data handling and AI use. That check is enforced in the demo, not only in this text. Matching is deterministic: invoice amounts against payment amounts. There is no demographic, behavioral, or identity input in the pipeline. Blotter writes code and a ledger, not creative or copyrighted content. The script runs in a subprocess with an import allowlist and a five-second timeout. If three attempts fail, the screen says Needs review and the shortfall is not taken from the script.",
  },
  {
    q: "Do we need an NVIDIA voucher?",
    a: "No. The comparison works without one. If a model is connected, it writes the matcher. It does not invent the fee.",
  },
];

const steps = [
  ["01", "Bring the files", "Supplier invoices, and the mobile-money statement from the phone."],
  ["02", "Match them", "A script is written for these columns, run, and checked against the totals."],
  ["03", "Read the gap", "Short payments, duplicate references, and amounts that only looked messy."],
];

export default function Home() {
  return (
    <>
      <header className="nav">
        <Link className="logo" href="/">
          <i />
          Blotter
        </Link>
        <nav className="nav-links">
          <a href="#how">How it works</a>
          <a href="#day">Sample day</a>
          <a href="#faq">FAQ</a>
          <Link className="btn" href="/demo">
            Live demo
          </Link>
        </nav>
      </header>

      <main>
        <section className="stage">
          <div className="stage-copy">
            <p className="kicker">Payments blotter</p>
            <h1>
              Which supplier
              <br />
              is still unpaid?
            </h1>
            <p className="lead">
              The invoice says one number. The phone says another. Blotter puts them on the same page and marks the gap, before the shop chases the wrong payment.
            </p>
            <div className="hero-actions">
              <Link className="btn" href="/demo">
                Live demo
              </Link>
              <a className="quiet" href="#day">
                See the sample day
              </a>
            </div>
          </div>
          <div className="stage-visual">
            <figure className="tile photo-tile">
              <img src="/shop-counter.jpg" alt="Invoices and a phone on the counter of a hardware shop" />
            </figure>
            <div className="stat-stack">
              <article className="stat">
                <span>Invoice</span>
                <strong>18,000</strong>
                <em>KSh · Amani Hardware</em>
              </article>
              <article className="stat">
                <span>On the phone</span>
                <strong>13,500</strong>
                <em>KSh · RCPT-100</em>
              </article>
              <article className="stat open">
                <span>Still open</span>
                <strong>4,500</strong>
                <em>KSh · the gap</em>
              </article>
            </div>
          </div>
        </section>

        <section className="section" id="how">
          <div className="wrap">
            <h2>From two messy files to one open item.</h2>
            <p className="intro">
              A shop does not get a clean spreadsheet. Dates arrive as text or as UNIX timestamps. Amounts arrive as numbers or as “KSh 4,500”. A reference gets used twice.
            </p>
            <ol className="steps">
              {steps.map(([index, title, copy]) => (
                <li key={index}>
                  <span>{index}</span>
                  <b>{title}</b>
                  <p>{copy}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section className="section" id="day">
          <div className="wrap day">
            <div>
              <h2>Sample day</h2>
              <p className="intro">
                Four suppliers. One short payment. One reference used twice. Coast Sugar was written “KSh 4,500” and still matched. Nothing has been sent.
              </p>
              <p className="caption">Invoiced 52,000. Received 47,500. Still open 4,500.</p>
            </div>
            <div className="product-frame">
              <header>
                <strong>Today</strong>
                <span>Amani Hardware</span>
              </header>
              <BlotterTable />
            </div>
          </div>
        </section>

        <section className="section" id="faq">
          <div className="wrap">
            <h2>Questions</h2>
            <dl className="faq">
              {faqs.map((item) => (
                <div key={item.q}>
                  <dt>{item.q}</dt>
                  <dd>{item.a}</dd>
                </div>
              ))}
            </dl>
          </div>
        </section>

        <section className="section tight">
          <div className="wrap">
            <div className="close">
              <div>
                <h2>See the KSh 4,500 gap.</h2>
                <p>The demo is the sample day. It does not pay anyone.</p>
              </div>
              <Link className="btn" href="/demo">
                Live demo
              </Link>
            </div>
            <footer className="footer">
              <span>Blotter</span>
              <span>Synthetic sample. No customer data. No payment is sent.</span>
            </footer>
          </div>
        </section>
      </main>
    </>
  );
}
