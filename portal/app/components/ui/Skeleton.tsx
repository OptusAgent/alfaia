interface SkeletonProps {
  className?: string;
  rows?: number;
}

export function Skeleton({ className = "", rows = 1 }: SkeletonProps) {
  return (
    <div className={`space-y-3 ${className}`}>
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="skeleton h-4 w-full"
          style={{
            animationDelay: `${i * 0.1}s`,
            width: i === rows - 1 ? "60%" : "100%",
          }}
        />
      ))}
    </div>
  );
}

export function SkeletonCard({ className = "" }: { className?: string }) {
  return (
    <div className={`glass-card p-5 space-y-4 ${className}`}>
      <div className="skeleton h-5 w-2/5" />
      <div className="skeleton h-8 w-3/5" />
      <div className="skeleton h-3 w-4/5" />
    </div>
  );
}
