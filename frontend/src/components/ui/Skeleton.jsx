// A simple skeleton loader with configurable size/shape
export default function Skeleton({ className = '', width, height = '1rem', rounded = 'rounded-lg', variant = 'text' }) {
  return (
    <div
      className={`animate-pulse bg-gray-200 ${rounded} ${className}`}
      style={{ width, height }}
    />
  );
}

// Table row skeleton - shows N rows with consistent columns
export function TableSkeleton({ rows = 5, columns = 4 }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="flex gap-4">
          {Array.from({ length: columns }).map((_, j) => (
            <Skeleton key={j} className="flex-1" height="1.5rem" />
          ))}
        </div>
      ))}
    </div>
  );
}

// Card skeleton - for dashboard cards
export function CardSkeleton() {
  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm space-y-4">
      <Skeleton height="1rem" width="60%" />
      <Skeleton height="2rem" width="40%" />
      <Skeleton height="0.75rem" width="80%" />
    </div>
  );
}
