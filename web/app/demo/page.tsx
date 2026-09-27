import Link from "next/link";
import { BlotterTable } from "../blotter";

export default function Demo() {
  return (
    <>
      <header className="nav">
        <Link className="logo" href="/">
          Blotter
        </Link>
        <nav className="nav-links">
          <Link href="/#faq">FAQ</Link>
          <span>Sample day</span>
        </nav>
      </header>
      <main className="section">
        <div className="wrap">
          <p className="eyebrow">Live demo</p>
          <h1>KSh 4,500 still open.</h1>
          <p className="lead">
            Amani Hardware billed 18,000. The statement shows 13,500. The other
            three suppliers are matched or flagged.
          </p>
          <div className="product-frame" style={{ marginTop: "2rem" }}>
            <header>
              <strong>Today</strong>
              <span>Invoiced 52,000 · Received 47,500 · Open 4,500</span>
            </header>
            <BlotterTable />
          </div>
          <p className="caption">
            The short receipt is dated as a UNIX timestamp. REF-102 was used
            twice. Coast Sugar was written “KSh 4,500” and still matched.
            Nothing has been sent.
          </p>
        </div>
      </main>
    </>
  );
}
