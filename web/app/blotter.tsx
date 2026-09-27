const rows = [
  ["Lake Flour", "7,500", "7,500", "Matched", ""],
  ["Amani Hardware", "18,000", "13,500", "Short 4,500", "short"],
  ["Rift Cement", "22,000", "22,000", "Duplicate", ""],
  ["Coast Sugar", "4,500", "KSh 4,500", "Matched", ""],
] as const;

export function BlotterTable() {
  return (
    <table className="sheet">
      <thead>
        <tr>
          <th>Supplier</th>
          <th className="num">Invoice</th>
          <th className="num">Received</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {rows.map(([supplier, invoice, received, status, tone]) => (
          <tr key={supplier} className={tone || undefined}>
            <td>{supplier}</td>
            <td className="num">{invoice}</td>
            <td className="num">{received}</td>
            <td>{status}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
