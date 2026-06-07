import { useLocation } from "react-router-dom";
import { Bell, ChevronRight, User, Settings, LogOut, Menu } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const breadcrumbMap = {
  "/": ["Dashboard"],
  "/missions": ["Missions"],
  "/missions/new": ["Missions", "New Mission"],
  "/collected-data": ["Collected Data"],
  "/digests": ["Digests"],
  "/engagement-queue": ["Engagement Queue"],
};

export default function Header({ activeMissionTitle, onMenuOpen }) {
  const location = useLocation();

  const getBreadcrumbs = () => {
    const path = location.pathname;
    if (path.startsWith("/missions/") && path.includes("/agents/")) {
      return ["Missions", activeMissionTitle || "Mission", "Agent Detail"];
    }
    if (path.startsWith("/missions/") && path !== "/missions/new") {
      return ["Missions", activeMissionTitle || "Mission Detail"];
    }
    return breadcrumbMap[path] || [path.slice(1)];
  };

  const breadcrumbs = getBreadcrumbs();

  return (
    <header className="fixed top-0 left-0 md:left-56 right-0 h-14 flex items-center justify-between px-4 md:px-6 bg-background/80 backdrop-blur-sm border-b border-border z-30">
      {/* Left: hamburger (mobile) + breadcrumb */}
      <div className="flex items-center gap-3">
        {/* Hamburger — mobile only */}
        <button
          onClick={onMenuOpen}
          className="md:hidden p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Breadcrumb */}
        <nav className="flex items-center gap-1.5 text-sm">
          {breadcrumbs.map((crumb, i) => (
            <span key={i} className="flex items-center gap-1.5">
              {i > 0 && <ChevronRight className="w-3.5 h-3.5 text-muted-foreground" />}
              <span className={cn(
                i === breadcrumbs.length - 1 ? "text-foreground font-medium" : "text-muted-foreground",
                // Truncate on mobile for deep breadcrumbs
                i < breadcrumbs.length - 1 && "hidden sm:inline"
              )}>
                {crumb}
              </span>
            </span>
          ))}
        </nav>
      </div>

      {/* Right actions */}
      <div className="flex items-center gap-2 md:gap-3">
        {activeMissionTitle && (
          <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse-glow" />
            <span className="text-xs text-primary font-medium truncate max-w-[140px]">{activeMissionTitle}</span>
          </div>
        )}

        <button className="relative p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-primary" />
        </button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-accent transition-colors">
              <div className="w-7 h-7 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center">
                <User className="w-3.5 h-3.5 text-primary" />
              </div>
              <span className="hidden md:block text-sm text-foreground font-medium">User</span>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-44">
            <DropdownMenuItem className="gap-2 text-sm">
              <Settings className="w-3.5 h-3.5" /> Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="gap-2 text-sm text-destructive focus:text-destructive">
              <LogOut className="w-3.5 h-3.5" /> Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}

// cn utility inline since it's a simple use
function cn(...classes) {
  return classes.filter(Boolean).join(" ");
}