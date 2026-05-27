import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Calendar, BarChart2, FileText, Clock, ChevronRight, ExternalLink } from "lucide-react";
import { mockMissions, mockAgents } from "@/lib/mockData";
import StatusBadge from "@/components/shared/StatusBadge";
import AgentBadge from "@/components/shared/AgentBadge";
import { formatDistanceToNow, format } from "date-fns";
import { cn } from "@/lib/utils";

const agentColors = {
  collector: "border-collector/30 bg-collector/5",
  analyzer: "border-analyzer/30 bg-analyzer/5",
  worker: "border-worker/30 bg-worker/5",
};

const agentLineColors = {
  collector: "bg-collector/40",
  analyzer: "bg-analyzer/40",
  worker: "bg-worker/40",
};

export default function MissionDetail() {
  const { missionId } = useParams();
  const mission = mockMissions.find(m => m.id === missionId);
  const agents = mockAgents[missionId] || [];

  if (!mission) return (
    <div className="text-center py-20 text-muted-foreground">Mission not found.</div>
  );

  return (
    <div className="space-y-6 animate-slide-in max-w-4xl">
      {/* Back */}
      <Link to="/missions" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors">
        <ArrowLeft className="w-3.5 h-3.5" />
        Back to Missions
      </Link>

      {/* Mission header */}
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="flex-1">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-lg font-semibold text-foreground">{mission.title}</h1>
              <StatusBadge status={mission.status} />
              <span className="text-xs font-mono text-muted-foreground bg-muted px-2 py-0.5 rounded">{mission.goalType}</span>
            </div>
            <p className="mt-2 text-sm text-muted-foreground leading-relaxed">{mission.goal}</p>
          </div>
        </div>

        {/* Stats */}
        <div className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "Posts Analyzed", value: mission.stats.postsAnalyzed.toLocaleString() },
            { label: "Gaps Found", value: mission.stats.gapsFound },
            { label: "Specs Generated", value: mission.stats.specsGenerated },
            { label: "Pending Actions", value: mission.stats.pendingApprovals },
          ].map(stat => (
            <div key={stat.label} className="bg-muted/40 rounded-lg p-3">
              <p className="text-xs text-muted-foreground">{stat.label}</p>
              <p className="text-xl font-semibold text-foreground mt-0.5 tabular-nums">{stat.value}</p>
            </div>
          ))}
        </div>

        {/* Schedule info */}
        <div className="mt-4 flex items-center gap-4 text-xs text-muted-foreground flex-wrap">
          {mission.lastRun && (
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Last run: {formatDistanceToNow(new Date(mission.lastRun), { addSuffix: true })}
            </span>
          )}
          {mission.nextRun && (
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              Next run: {format(new Date(mission.nextRun), "MMM d, h:mm a")}
            </span>
          )}
          <span className="flex items-center gap-1">
            Data: {mission.dataSource === "scrape" ? `Scraping — ${mission.sources.join(", ")}` : "Provided data source"}
          </span>
        </div>
      </div>

      {/* Agent pipeline */}
      <div>
        <h2 className="text-sm font-semibold text-foreground mb-4">Agent Pipeline</h2>
        <div className="space-y-0">
          {agents.map((agent, idx) => (
            <div key={agent.id}>
              <Link
                to={`/missions/${missionId}/agents/${agent.id}`}
                className={cn(
                  "block bg-card border rounded-xl p-5 hover:border-primary/30 transition-all group",
                  agentColors[agent.type]
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <div className="flex-shrink-0 w-7 h-7 rounded-full bg-muted border border-border flex items-center justify-center text-xs font-mono text-muted-foreground">
                      {idx + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <AgentBadge type={agent.type} />
                        <StatusBadge status={agent.status} />
                      </div>
                      <p className="mt-1.5 text-xs text-muted-foreground line-clamp-2">{agent.prompt}</p>
                    </div>
                  </div>
                  <div className="flex-shrink-0 flex items-center gap-3">
                    <div className="text-right hidden md:block">
                      <p className="text-[10px] text-muted-foreground">{agent.scheduleLabel}</p>
                      {agent.lastRun && (
                        <p className="text-[10px] text-muted-foreground mt-0.5">
                          Last: {formatDistanceToNow(new Date(agent.lastRun), { addSuffix: true })}
                        </p>
                      )}
                    </div>
                    <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
                  </div>
                </div>
              </Link>
              {/* Connector line */}
              {idx < agents.length - 1 && (
                <div className="flex justify-center py-0">
                  <div className={cn("w-0.5 h-5", agentLineColors[agent.type])} />
                </div>
              )}
            </div>
          ))}
          {agents.length === 0 && (
            <div className="text-center py-8 text-muted-foreground text-sm bg-card border border-border rounded-xl">
              No agents attached to this mission yet.
            </div>
          )}
        </div>
      </div>

      {/* Quick links */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <Link
          to="/digests"
          className="flex items-center gap-3 bg-card border border-border rounded-xl p-4 hover:border-primary/30 transition-all group"
        >
          <BarChart2 className="w-4 h-4 text-analyzer" />
          <div>
            <p className="text-sm font-medium text-foreground">View Digest</p>
            <p className="text-xs text-muted-foreground">See analyzed results</p>
          </div>
          <ExternalLink className="w-3.5 h-3.5 text-muted-foreground ml-auto group-hover:text-primary transition-colors" />
        </Link>
        <Link
          to="/engagement-queue"
          className="flex items-center gap-3 bg-card border border-border rounded-xl p-4 hover:border-primary/30 transition-all group"
        >
          <FileText className="w-4 h-4 text-worker" />
          <div>
            <p className="text-sm font-medium text-foreground">Engagement Queue</p>
            <p className="text-xs text-muted-foreground">{mission.stats.pendingApprovals} pending approvals</p>
          </div>
          <ExternalLink className="w-3.5 h-3.5 text-muted-foreground ml-auto group-hover:text-primary transition-colors" />
        </Link>
      </div>
    </div>
  );
}