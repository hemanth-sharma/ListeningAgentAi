import { cn } from "@/lib/utils";

const statusConfig = {
  Running: { color: "text-primary border-primary/30 bg-primary/10", dot: "bg-primary animate-pulse" },
  Scheduled: { color: "text-warning border-warning/30 bg-warning/10", dot: "bg-warning" },
  Idle: { color: "text-muted-foreground border-border bg-muted/50", dot: "bg-muted-foreground" },
  Completed: { color: "text-success border-success/30 bg-success/10", dot: "bg-success" },
  Error: { color: "text-destructive border-destructive/30 bg-destructive/10", dot: "bg-destructive" },
  Processing: { color: "text-analyzer border-analyzer/30 bg-analyzer/10", dot: "bg-analyzer animate-pulse" },
};

export default function StatusBadge({ status, className }) {
  const config = statusConfig[status] || statusConfig.Idle;
  return (
    <span className={cn(
      "inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border",
      config.color,
      className
    )}>
      <span className={cn("w-1.5 h-1.5 rounded-full", config.dot)} />
      {status}
    </span>
  );
}