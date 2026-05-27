import { useParams, Link } from "react-router-dom";
import { ArrowLeft, Calendar, Clock, RefreshCw } from "lucide-react";
import { mockMissions, mockAgents, mockLogs } from "@/lib/mockData";
import StatusBadge from "@/components/shared/StatusBadge";
import AgentBadge from "@/components/shared/AgentBadge";
import LogViewer from "@/components/agents/LogViewer";
import { formatDistanceToNow, format } from "date-fns";
import { cn } from "@/lib/utils";

const agentDescriptions = {
  collector: "Scrapes and collects raw data from configured sources based on keyword matching and AI relevance scoring.",
  analyzer: "Processes collected data using LLM analysis to identify market gaps, pain points, and patterns.",
  worker: "Executes output tasks — storing specs, sending notifications, and drafting social media actions.",
};

export default function AgentDetail() {
  const { missionId, agentId } = useParams();
  const mission = mockMissions.find(m => m.id === missionId);
  const agents = mockAgents[missionId] || [];
  const agent = agents.find(a => a.id === agentId);
  const logs = mockLogs[agentId] || [];

  if (!agent || !mission) return (
    <div className="text-center py-20 text-muted-foreground">Agent not found.</div>
  );

  const statLabels = {
    collector: [
      { key: "postsScraped", label: "Posts Scraped" },
      { key: "filtered", label: "After Filter" },
      { key: "stored", label: "Stored" },
    ],
    analyzer: [
      { key: "analyzed", label: "Posts Analyzed" },
      { key: "gapsFound", label: "Gaps Found" },
      { key: "specsGenerated", label: "Specs Generated" },
    ],
    worker: [
      { key: "tasksExecuted", label: "Tasks Executed" },
      { key: "actionsApproved", label: "Actions Approved" },
      { key: "actionsPending", label: "Pending" },
    ],
  };

  const stats = statLabels[agent.type] || [];

  return (
    <div className="space-y-6 animate-slide-in max-w-3xl">
      {/* Back */}
      <Link
        to={`/missions/${missionId}`}
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        Back to {mission.title}
      </Link>

      {/* Agent header */}
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <AgentBadge type={agent.type} />
              <StatusBadge status={agent.status} />
            </div>
            <p className="mt-2 text-sm text-muted-foreground leading-relaxed">
              {agentDescriptions[agent.type]}
            </p>
          </div>
          <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-muted-foreground bg-muted border border-border rounded-lg hover:text-foreground hover:border-primary/40 transition-colors">
            <RefreshCw className="w-3 h-3" />
            Trigger
          </button>
        </div>

        {/* Schedule */}
        <div className="mt-4 flex items-center gap-4 text-xs text-muted-foreground flex-wrap">
          <span className="flex items-center gap-1 font-mono bg-muted px-2 py-1 rounded">{agent.schedule}</span>
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            {agent.scheduleLabel}
          </span>
          {agent.lastRun && (
            <span className="flex items-center gap-1">
              Last: {formatDistanceToNow(new Date(agent.lastRun), { addSuffix: true })}
            </span>
          )}
          {agent.nextRun && (
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              Next: {format(new Date(agent.nextRun), "MMM d, h:mm a")}
            </span>
          )}
        </div>
      </div>

      {/* Stats */}
      {agent.stats && (
        <div className="grid grid-cols-3 gap-3">
          {stats.map(({ key, label }) => (
            <div key={key} className="bg-card border border-border rounded-xl p-4">
              <p className="text-xs text-muted-foreground">{label}</p>
              <p className="text-2xl font-semibold text-foreground mt-1 tabular-nums">
                {(agent.stats[key] ?? 0).toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Configuration */}
      <div className="bg-card border border-border rounded-xl p-5">
        <h3 className="text-sm font-semibold text-foreground mb-3">Agent Instructions</h3>
        <div className="bg-muted/40 rounded-lg p-3 text-sm text-muted-foreground leading-relaxed font-mono text-xs">
          {agent.prompt}
        </div>
      </div>

      {/* Worker metadata */}
      {agent.type === "worker" && agent.metadata && (
        <div className="bg-card border border-border rounded-xl p-5">
          <h3 className="text-sm font-semibold text-foreground mb-3">Metadata / Credentials</h3>
          <div className="space-y-2">
            {agent.metadata.map((item, i) => (
              <div key={i} className="flex items-center gap-3 font-mono text-xs">
                <span className="text-muted-foreground bg-muted px-2 py-1 rounded min-w-[140px]">{item.key}</span>
                <span className="text-foreground">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Logs */}
      <div>
        <h3 className="text-sm font-semibold text-foreground mb-3">
          Execution Logs
          <span className="ml-2 text-xs text-muted-foreground font-normal">Last run — {agent.lastRun ? format(new Date(agent.lastRun), "MMM d, h:mm a") : "N/A"}</span>
        </h3>
        <LogViewer
          logs={logs}
          title={`${agent.type}.agent — ${mission.title}`}
        />
      </div>
    </div>
  );
}