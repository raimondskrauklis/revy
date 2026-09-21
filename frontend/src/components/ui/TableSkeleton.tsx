// frontend/src/components/ui/TableSkeleton.tsx
interface TableSkeletonProps {
  rows?: number;
  columns?: number;
}

const WIDTHS = ['60%', '75%', '55%', '80%', '65%', '70%', '50%'];

export function TableSkeleton({ rows = 4, columns = 4 }: TableSkeletonProps) {
  return (
    <div className="overflow-x-auto rounded-[var(--app-radius-sm)] shadow-[inset_0_0_0_1px_var(--app-ring)]">
      <table className="min-w-full table-fixed text-left text-sm">
        <thead className="bg-[color:var(--app-chip)]">
          <tr>
            {Array.from({ length: columns }).map((_, i) => (
              <th key={i} className="px-3 py-2">
                <div className="h-4 w-16 animate-pulse rounded bg-[color:var(--app-chip)]" />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: rows }).map((_, rowIdx) => (
            <tr key={rowIdx} className="border-t border-[color:var(--app-ring)]">
              {Array.from({ length: columns }).map((_, colIdx) => (
                <td key={colIdx} className="px-3 py-3">
                  <div
                    className="h-4 animate-pulse rounded bg-[color:var(--app-chip)]"
                    style={{ width: WIDTHS[(rowIdx * columns + colIdx) % WIDTHS.length] }}
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}