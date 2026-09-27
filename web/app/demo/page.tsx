import Link from "next/link";

const rows = [
  {
    kind: "Short payment",
    detail: "Amani Hardware was invoiced KSh 18,000. The receipt is KSh 13,500. The date on that receipt is a UNIX timestamp.",
  },
  {
    kind: "Duplicate reference",
    detail: "REF-102 is on two receipts for Rift Cement.",
  },
  {
    kind: "Amount as text",
    detail: "One receipt is written KSh 4,500 and still matches Coast Sugar.",
  },
];

export default function Demo() {
  return (
    <main>
      <p>
        <Link href="/">Blotter</Link>
      </p>
      <h1>KSh 4,500 still open.</h1>
      <p className="facts">Amani Hardware. Nothing has been sent.</p>
      <ul className="rows">
        {rows.map((row) => (
          <li key={row.kind}>
            <strong>{row.kind}</strong>
            <span>{row.detail}</span>
          </li>
        ))}
      </ul>
    </main>
  );
}
