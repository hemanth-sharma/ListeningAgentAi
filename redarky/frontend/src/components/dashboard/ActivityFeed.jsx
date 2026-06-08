import { formatDistanceToNow } from "date-fns";
import { Radio, BarChart2, Wrench, CheckCircle, AlertCircle, Clock } from "lucide-react";
import { cn } from "@/lib/utils";

const activityConfig = {
  agent_complete: { icon: CheckCircle, color: "text-success", bg: "bg-success/10" },
  gap_found: { icon: BarChart2, color: "text-analyzer", bg: "bg-analyzer/10" },
  approval_needed: { icon: AlertCircle, color: "text-warning", bg: "bg-warning/10" },
  spec_generated: { icon: Radio, color: "text-collector", bg: "bg-collector/10" },
  scheduled: { icon: Clock, color: "text-muted-foreground", bg: "bg-muted" },
};

export default function ActivityFeed({ items }) {
  return (
    <div className="bg-card border border-border rounded-xl">
      <div className="px-5 py-4 border-b border-border">
        <h3 className="text-sm font-semibold text-foreground">Recent Activity</h3>
      </div>
      <div className="divide-y divide-border">
        {items.map((item) => {
          const config = activityConfig[item.type] || activityConfig.scheduled;
          const Icon = config.icon;
          return (
            <div key={item.id} className="flex items-start gap-3 px-5 py-3.5 hover:bg-accent/30 transition-colors">
              <div className={cn("p-1.5 rounded-md mt-0.5 flex-shrink-0", config.bg)}>
                <Icon className={cn("w-3 h-3", config.color)} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-foreground">
                  <span className="font-medium">{item.mission}</span>
                  {" — "}
                  <span className="text-muted-foreground">{item.detail}</span>
                </p>
                <p className="text-[10px] text-muted-foreground mt-0.5">
                  {formatDistanceToNow(new Date(item.ts), { addSuffix: true })}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}