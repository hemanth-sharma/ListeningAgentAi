import { Link } from "react-router-dom";
import { Clock, BarChart2, ChevronRight } from "lucide-react";
import StatusBadge from "@/components/shared/StatusBadge";
import AgentBadge from "@/components/shared/AgentBadge";
import { formatDistanceToNow } from "date-fns";

export default function MissionCard({ mission }) {
  const lastRunLabel = mission.lastRun
    ? formatDistanceToNow(new Date(mission.lastRun), { addSuffix: true })
    : "Never";

  return (
    <Link
      to={`/missions/${mission.id}`}
      className="block bg-card border border-border rounded-xl p-5 hover:border-primary/30 transition-all group"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-sm font-semibold text-foreground truncate">{mission.title}</h3>
            <StatusBadge status={mission.status} />
          </div>
          <p className="mt-1.5 text-xs text-muted-foreground line-clamp-2">{mission.goal}</p>
        </div>
        <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors flex-shrink-0 mt-0.5" />
      </div>

      {/* Agent badges */}
      <div className="mt-3 flex items-center gap-1.5 flex-wrap">
        {mission.agents.map(agent => (
          <AgentBadge key={agent} type={agent} />
        ))}
      </div>

      {/* Stats row */}
      <div className="mt-3 pt-3 border-t border-border flex items-center gap-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1">
          <BarChart2 className="w-3 h-3" />
          {mission.stats.gapsFound} gaps found
        </span>
        <span className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {lastRunLabel}
        </span>
        <span className="ml-auto font-mono text-[10px] bg-muted px-2 py-0.5 rounded">{mission.goalType}</span>
      </div>
    </Link>
  );
}