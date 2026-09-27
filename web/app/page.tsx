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
    a: "The matcher runs in a sandbox. If it crashes, or if the totals do not tie, the error goes back and the script is rewritten. Three tries, then a labeled fallback.",
  },
  {
    q: "Is the shop data real?",
    a: "No. Amani Hardware, the KSh 18,000 invoice, and the KSh 13,500 receipt are a synthetic sample. There are no customer phone numbers.",
  },
  {
    q: "Do we need an NVIDIA voucher?",
    a: "No. The comparison works without one. If a model is connected, it writes the matcher. It does not invent the fee.",
  },
];

export default function Home() {
  return (
    <>
      <header className="nav">
        <Link className="logo" href="/">
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
        <section className="wrap hero">
          <div>
            <p className="eyebrow">Payments blotter for a shop</p>
            <h1>Which supplier is still unpaid?</h1>
            <p className="lead">
              The invoice says one number. The phone says another. Blotter puts
              them on the same page and marks the gap, before the shop chases
              the wrong payment.
            </p>
            <div className="hero-actions">
              <Link className="btn" href="/demo">
                Live demo
              </Link>
              <a className="btn ghost" href="#day">
                See the KSh 4,500 gap
              </a>
            </div>
          </div>
          <img
            className="hero-photo"
            src="/shop-counter.jpg"
            alt="Invoices and a phone on the counter of a hardware shop"
          />
        </section>

        <section className="band">
          <div className="wrap">
            <article>
              <span>Invoice</span>
              <strong>KSh 18,000</strong>
            </article>
            <article>
              <span>On the phone</span>
              <strong>KSh 13,500</strong>
            </article>
            <article>
              <span>Still open</span>
              <strong>KSh 4,500</strong>
            </article>
          </div>
        </section>

        <section className="section" id="how">
          <div className="wrap">
            <h2>From two messy files to one open item.</h2>
            <p className="intro">
              A shop does not get a clean spreadsheet. Dates arrive as text or
              as UNIX timestamps. Amounts arrive as numbers or as “KSh 4,500”.
              A reference gets used twice.
            </p>
            <ol className="steps">
              <li>
                <b>1. Bring the files</b>
                <span>Supplier invoices, and the mobile-money statement from the phone.</span>
              </li>
              <li>
                <b>2. Match them</b>
                <span>A script is written for these columns, run, and checked against the totals.</span>
              </li>
              <li>
                <b>3. Read the gap</b>
                <span>Short payments, duplicate references, and amounts that only looked messy.</span>
              </li>
            </ol>
          </div>
        </section>

        <section className="section wash">
          <div className="wrap split">
            <img
              src="/paper-invoices.jpg"
              alt="Printed invoices beside a phone listing payments"
            />
            <div>
              <h2>The rate on the paper is not what arrived.</h2>
              <p className="intro">
                Amani Hardware billed KSh 18,000. The statement shows KSh
                13,500, and that receipt’s date is a UNIX timestamp a normal
                import drops. Blotter keeps the row and shows the shortfall.
              </p>
              <Link className="btn" href="/demo">
                Open the live demo
              </Link>
            </div>
          </div>
        </section>

        <section className="section" id="day">
          <div className="wrap">
            <h2>Sample day</h2>
            <p className="intro">
              Four suppliers. One short payment. One reference used twice. One
              amount written out in words and still matched.
            </p>
            <div className="product-frame">
              <header>
                <strong>Blotter</strong>
                <span>Amani Hardware · nothing has been sent</span>
              </header>
              <BlotterTable />
            </div>
            <p className="caption">
              Invoiced KSh 52,000. Received KSh 47,500. Still open KSh 4,500.
            </p>
          </div>
        </section>

        <section className="section wash" id="faq">
          <div className="wrap">
            <h2>Questions</h2>
            <div className="faq">
              {faqs.map((item) => (
                <details key={item.q}>
                  <summary>{item.q}</summary>
                  <p>{item.a}</p>
                </details>
              ))}
            </div>
          </div>
        </section>

        <section className="section">
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
