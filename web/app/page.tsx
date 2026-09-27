import Link from "next/link";

export default function Home() {
  return (
    <main>
      <p>Blotter</p>
      <h1>The supplier was short KSh 4,500.</h1>
      <p className="facts">The invoice says KSh 18,000. The mobile-money log says KSh 13,500.</p>
      <Link className="live" href="/demo">
        Live demo
      </Link>
    </main>
  );
}
