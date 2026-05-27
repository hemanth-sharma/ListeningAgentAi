import { useState } from "react";
import { ExternalLink, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { mockCollectedData, mockMissions } from "@/lib/mockData";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";

const sentimentConfig = {
  negative: { color: "text-destructive", bg: "bg-destructive/10", icon: TrendingDown },
  positive: { color: "text-success", bg: "bg-success/10", icon: TrendingUp },
  neutral: { color: "text-muted-foreground", bg: "bg-muted", icon: Minus },
  frustrated: { color: "text-warning", bg: "bg-warning/10", icon: TrendingDown },
};

const sourceColors = {
  Reddit: "text-orange-400 bg-orange-400/10 border-orange-400/20",
  "Hacker News": "text-amber-400 bg-amber-400/10 border-amber-400/20",
};

export default function CollectedData() {
  const [activeMission, setActiveMission] = useState("m1");

  const filtered = mockCollectedData.filter(d => d.missionId === activeMission);

  return (
    <div className="space-y-6 animate-slide-in">
      <div>
        <h1 className="text-xl font-semibold text-foreground">Collected Data</h1>
        <p className="text-sm text-muted-foreground mt-0.5">Raw posts and data collected by your Collector agents</p>
      </div>

      {/* Mission selector */}
      <div className="flex items-center gap-2 flex-wrap">
        {mockMissions.map(m => (
          <button
            key={m.id}
            onClick={() => setActiveMission(m.id)}
            className={cn(
              "px-3 py-1.5 text-xs font-medium rounded-md border transition-colors",
              activeMission === m.id
                ? "bg-primary/10 text-primary border-primary/30"
                : "text-muted-foreground border-border hover:text-foreground hover:border-muted-foreground/30"
            )}
          >
            {m.title}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="bg-card border border-border rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Title</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Source</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Relevance</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Sentiment</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground">Collected</th>
                <th className="text-left px-4 py-3 text-xs font-medium text-muted-foreground"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filtered.map(item => {
                const sentiment = sentimentConfig[item.sentiment] || sentimentConfig.neutral;
                const SentimentIcon = sentiment.icon;
                return (
                  <tr key={item.id} className="hover:bg-accent/30 transition-colors">
                    <td className="px-4 py-3">
                      <div>
                        <p className="text-xs font-medium text-foreground line-clamp-1">{item.title}</p>
                        <div className="flex gap-1 mt-1 flex-wrap">
                          {item.keywords.slice(0, 3).map(kw => (
                            <span key={kw} className="text-[10px] font-mono bg-muted text-muted-foreground px-1.5 py-0.5 rounded">
                              {kw}
                            </span>
                          ))}
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={cn("text-xs px-2 py-0.5 rounded-full border font-medium", sourceColors[item.source] || "text-muted-foreground bg-muted border-border")}>
                        {item.subreddit || item.source}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary rounded-full"
                            style={{ width: `${item.relevanceScore * 100}%` }}
                          />
                        </div>
                        <span className="text-xs font-mono text-foreground">{(item.relevanceScore * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={cn("inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full", sentiment.bg, sentiment.color)}>
                        <SentimentIcon className="w-3 h-3" />
                        {item.sentiment}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(item.collectedAt), { addSuffix: true })}
                    </td>
                    <td className="px-4 py-3">
                      <a href={item.url} className="p-1.5 rounded hover:bg-accent text-muted-foreground hover:text-foreground transition-colors inline-block">
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    </td>
                  </tr>
                );
              })}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-sm text-muted-foreground">
                    No collected data for this mission yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}