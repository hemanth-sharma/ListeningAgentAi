import { Link } from "react-router-dom";
import { Plus, Search, Filter } from "lucide-react";
import { mockMissions } from "@/lib/mockData";
import MissionCard from "@/components/dashboard/MissionCard";
import StatusBadge from "@/components/shared/StatusBadge";
import { useState } from "react";

const statusFilters = ["All", "Running", "Scheduled", "Idle", "Completed"];

export default function Missions() {
  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState("All");

  const filtered = mockMissions.filter(m => {
    const matchesSearch = m.title.toLowerCase().includes(search.toLowerCase()) ||
      m.goal.toLowerCase().includes(search.toLowerCase());
    const matchesFilter = activeFilter === "All" || m.status === activeFilter;
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="space-y-6 animate-slide-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground">Missions</h1>
          <p className="text-sm text-muted-foreground mt-0.5">{mockMissions.length} missions total</p>
        </div>
        <Link
          to="/missions/new"
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground text-sm font-medium rounded-lg hover:bg-primary/90 transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Mission
        </Link>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search missions..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-8 pr-3 py-2 bg-card border border-border rounded-lg text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors"
          />
        </div>
        <div className="flex items-center gap-1.5">
          {statusFilters.map(f => (
            <button
              key={f}
              onClick={() => setActiveFilter(f)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                activeFilter === f
                  ? "bg-primary/10 text-primary border border-primary/30"
                  : "text-muted-foreground hover:text-foreground border border-transparent hover:border-border"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Mission list */}
      <div className="space-y-3">
        {filtered.map(mission => (
          <MissionCard key={mission.id} mission={mission} />
        ))}
        {filtered.length === 0 && (
          <div className="text-center py-16 text-muted-foreground">
            <p className="text-sm">No missions found</p>
          </div>
        )}
      </div>
    </div>
  );
}