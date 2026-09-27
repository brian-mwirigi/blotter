import Link from "next/link";
import { BlotterTable } from "../blotter";

export default function Demo() {
  return (
    <>
      <header className="topbar">
        <Link className="brand" href="/">
          <strong>Blotter</strong>
          <span>Sample day</span>
        </Link>
        <span className="quiet">Nothing has been sent</span>
      </header>
      <section className="app">
        <div className="product">
          <div className="app-head">
            <div>
              <p className="kicker">Open item</p>
              <h1>KSh 4,500</h1>
            </div>
            <span className="quiet">Amani Hardware</span>
          </div>
          <div className="metrics">
            <div>
              <span>Invoiced</span>
              <strong>52,000</strong>
            </div>
            <div>
              <span>Received</span>
              <strong>47,500</strong>
            </div>
            <div className="open">
              <span>Still open</span>
              <strong>4,500</strong>
            </div>
          </div>
          <BlotterTable />
          <p className="note">
            The short receipt is dated as a UNIX timestamp. REF-102 was used twice. One amount was written as “KSh 4,500” and still matched.
          </p>
        </div>
      </section>
    </>
  );
}
