import { useState } from "react";
import { Link } from "react-router-dom";
import { Plus, Compass, AlertTriangle, Layers, TrendingUp } from "lucide-react";
import { mockMissions, mockActivityFeed } from "@/lib/mockData";
import MetricCard from "@/components/dashboard/MetricCard";
import MissionCard from "@/components/dashboard/MissionCard";
import ActivityFeed from "@/components/dashboard/ActivityFeed";
import SkeletonCard from "@/components/shared/SkeletonCard";

export default function Dashboard() {
  const [loading] = useState(false);

  const totalGaps = mockMissions.reduce((a, m) => a + m.stats.gapsFound, 0);
  const totalSpecs = mockMissions.reduce((a, m) => a + m.stats.specsGenerated, 0);
  const pendingApprovals = mockMissions.reduce((a, m) => a + m.stats.pendingApprovals, 0);
  const activeMissions = mockMissions.filter(m => m.status === "Running" || m.status === "Scheduled").length;

  return (
    <div className="space-y-6 animate-slide-in">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground">Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-0.5">Monitor your intelligence pipelines</p>
        </div>
        <Link
          to="/missions/new"
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground text-sm font-medium rounded-lg hover:bg-primary/90 transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Mission
        </Link>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Active Missions"
          value={activeMissions}
          icon={Compass}
          trendLabel="2 running now"
          accentClass="text-primary"
        />
        <MetricCard
          title="Market Gaps Found"
          value={totalGaps}
          icon={TrendingUp}
          trendLabel="+14 today"
          accentClass="text-analyzer"
        />
        <MetricCard
          title="Specs Generated"
          value={totalSpecs}
          icon={Layers}
          trendLabel="+6 today"
          accentClass="text-collector"
        />
        <MetricCard
          title="Pending Approvals"
          value={pendingApprovals}
          icon={AlertTriangle}
          trendLabel="Requires action"
          accentClass="text-warning"
        />
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Missions grid */}
        <div className="xl:col-span-2 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-foreground">Missions</h2>
            <Link to="/missions" className="text-xs text-primary hover:underline">View all</Link>
          </div>
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map(i => <SkeletonCard key={i} />)}
            </div>
          ) : (
            <div className="space-y-3">
              {mockMissions.map(mission => (
                <MissionCard key={mission.id} mission={mission} />
              ))}
            </div>
          )}
        </div>

        {/* Activity feed */}
        <div>
          <ActivityFeed items={mockActivityFeed} />
        </div>
      </div>
    </div>
  );
}