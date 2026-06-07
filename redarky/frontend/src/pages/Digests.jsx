import { useState } from "react";
import { mockMarketGaps, mockMiniSpec, mockSentimentData, mockMissions } from "@/lib/mockData";
import MarketGapCard from "@/components/digests/MarketGapCard";
import MiniSpecViewer from "@/components/digests/MiniSpecViewer";
import SentimentChart from "@/components/digests/SentimentChart";
import { cn } from "@/lib/utils";
import { format } from "date-fns";

export default function Digests() {
  const [activeMission, setActiveMission] = useState("m1");
  const [selectedSpec, setSelectedSpec] = useState(null);

  const gaps = mockMarketGaps.filter(g => g.missionId === activeMission);
  const mission = mockMissions.find(m => m.id === activeMission);

  const handleViewSpec = (gapId) => {
    setSelectedSpec(mockMiniSpec);
  };

  return (
    <div className="space-y-6 animate-slide-in">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground">Daily Digest</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            {mission && `Generated ${format(new Date(mission.lastRun || Date.now()), "MMMM d, yyyy")}`}
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs text-muted-foreground">Next digest</p>
          <p className="text-sm font-mono text-foreground">Tomorrow 7:00 AM</p>
        </div>
      </div>

      {/* Mission tabs */}
      <div className="flex gap-2 flex-wrap">
        {mockMissions.filter(m => m.stats.gapsFound > 0).map(m => (
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
            <span className="ml-1.5 text-[10px] opacity-70">({m.stats.gapsFound})</span>
          </button>
        ))}
      </div>

      {/* Sentiment chart */}
      <SentimentChart data={mockSentimentData} />

      {/* Summary stats */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Gaps Found", value: gaps.length, sub: "High confidence" },
          { label: "Posts Analyzed", value: mission?.stats.postsAnalyzed.toLocaleString() || 0, sub: "Raw data points" },
          { label: "Specs Ready", value: mission?.stats.specsGenerated || 0, sub: "For review" },
        ].map(stat => (
          <div key={stat.label} className="bg-card border border-border rounded-xl p-4">
            <p className="text-xs text-muted-foreground">{stat.label}</p>
            <p className="text-2xl font-semibold text-foreground mt-1 tabular-nums">{stat.value}</p>
            <p className="text-[10px] text-muted-foreground mt-0.5">{stat.sub}</p>
          </div>
        ))}
      </div>

      {/* Market gap cards */}
      <div>
        <h2 className="text-sm font-semibold text-foreground mb-3">Market Gaps — {mission?.title}</h2>
        <div className="space-y-3">
          {gaps.map(gap => (
            <MarketGapCard key={gap.id} gap={gap} onViewSpec={handleViewSpec} />
          ))}
          {gaps.length === 0 && (
            <div className="text-center py-12 text-muted-foreground text-sm bg-card border border-border rounded-xl">
              No market gaps analyzed for this mission yet.
            </div>
          )}
        </div>
      </div>

      {/* Mini spec viewer modal */}
      {selectedSpec && (
        <MiniSpecViewer spec={selectedSpec} onClose={() => setSelectedSpec(null)} />
      )}
    </div>
  );
}