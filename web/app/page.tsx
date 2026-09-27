import Link from "next/link";
import { BlotterTable } from "./blotter";

export default function Home() {
  return (
    <>
      <header className="topbar">
        <div className="brand">
          <strong>Blotter</strong>
          <span>Payments blotter</span>
        </div>
        <Link className="live" href="/demo">
          Live demo
        </Link>
      </header>
      <section className="stage">
        <div className="hero">
          <div>
            <p className="kicker">Today’s open item</p>
            <h1>The supplier was short KSh 4,500.</h1>
            <p className="lede">
              The invoice says KSh 18,000. The mobile-money log says KSh 13,500.
              Blotter ties the two before the shop chases the wrong payment.
            </p>
            <Link className="live" href="/demo">
              Live demo
            </Link>
          </div>
          <div className="product" aria-hidden="true">
            <header>
              <div className="dots" aria-hidden="true">
                <i />
                <i />
                <i />
              </div>
              <span className="quiet">Amani Hardware · sample day</span>
            </header>
            <BlotterTable />
          </div>
        </div>
      </section>
    </>
  );
}
