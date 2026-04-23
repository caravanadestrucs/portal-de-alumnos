import { ChevronLeft, ChevronRight } from 'lucide-react';

export default function Table({
  columns,
  data,
  onRowClick,
  emptyMessage = 'No hay datos disponibles',
  loading = false,
}) {
  if (loading) {
    return (
      <div className="glass rounded-2xl overflow-hidden">
        <div className="animate-pulse">
          <div className="h-12 bg-gradient-to-r from-primary-200 to-accent-200" />
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 border-b border-gray-100 bg-white" />
          ))}
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="glass rounded-2xl p-12 text-center">
        <p className="text-gray-500">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="glass rounded-2xl overflow-hidden">
      <div className="table-container">
        <table className="table-glass">
          <thead>
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={col.className || ''}
                  style={col.width ? { width: col.width } : undefined}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row, rowIndex) => (
              <tr
                key={row.id || rowIndex}
                onClick={() => onRowClick?.(row)}
                className={onRowClick ? 'cursor-pointer' : ''}
              >
                {columns.map((col) => (
                  <td key={col.key} className={col.cellClassName || ''}>
                    {col.render ? col.render(row) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
