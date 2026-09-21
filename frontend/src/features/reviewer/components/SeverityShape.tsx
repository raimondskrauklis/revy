// frontend/src/features/reviewer/components/SeverityShape.tsx
import type { FindingSeverity } from '@/features/reviewer/types';

const SHAPE_CLASS: Record<FindingSeverity, string> = {
  info: 'h-2.5 w-2.5 rounded-full bg-[color:var(--app-info)]',
  warning:
    'h-0 w-0 border-x-[5px] border-x-transparent border-b-[9px] border-b-[color:var(--app-warning)]',
  error: 'h-2.5 w-2.5 bg-[color:var(--app-danger)]',
  critical: 'h-2.5 w-2.5 rotate-45 bg-[color:var(--app-danger)]',
};

interface SeverityShapeProps {
  severity: FindingSeverity;
  className?: string;
}

export function SeverityShape({ severity, className }: SeverityShapeProps) {
  return (
    <span
      aria-hidden
      data-severity-shape={severity}
      className={`inline-block shrink-0 ${SHAPE_CLASS[severity]} ${className ?? ''}`}
    />
  );
}