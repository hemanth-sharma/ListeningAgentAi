import { cn } from "@/lib/utils";
import { TrendingUp } from "lucide-react";

export default function MetricCard({ title, value, icon: Icon, trend, trendLabel, accentClass }) {
  return (
    <div className={cn(
      "relative bg-card border border-border rounded-xl p-5 overflow-hidden transition-all hover:border-primary/30 group"
    )}>
      {/* Subtle background glow */}
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity bg-gradient-to-br from-primary/5 to-transparent rounded-xl pointer-events-none" />
      
      <div className="relative flex items-start justify-between">
        <div>
          <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider">{title}</p>
          <p className="mt-2 text-3xl font-semibold text-foreground tabular-nums">{value}</p>
          {trend !== undefined && (
            <p className="mt-1 flex items-center gap-1 text-xs text-success">
              <TrendingUp className="w-3 h-3" />
              {trendLabel || `+${trend} this week`}
            </p>
          )}
        </div>
        <div className={cn("p-2.5 rounded-lg bg-muted/50 border border-border", accentClass)}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
    </div>
  );
}