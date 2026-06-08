import { Link, useLocation } from "react-router-dom";
import { LayoutDashboard, Compass, Database, BookOpen, CheckSquare, Zap, ChevronRight, X } from "lucide-react";
import { cn } from "@/lib/utils";

export const navItems = [
  { label: "Dashboard", icon: LayoutDashboard, path: "/" },
  { label: "Missions", icon: Compass, path: "/missions" },
  { label: "Collected Data", icon: Database, path: "/collected-data" },
  { label: "Digests", icon: BookOpen, path: "/digests" },
  { label: "Engagement Queue", icon: CheckSquare, path: "/engagement-queue" },
];

// Desktop sidebar (hidden on mobile)
export function DesktopSidebar() {
  const location = useLocation();

  return (
    <aside className="hidden md:flex fixed left-0 top-0 h-screen w-56 flex-col bg-card border-r border-border z-40">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 py-5 border-b border-border">
        <div className="w-7 h-7 rounded-lg bg-primary flex items-center justify-center">
          <Zap className="w-4 h-4 text-primary-foreground" />
        </div>
        <span className="font-semibold text-foreground tracking-tight">RedArky</span>
        <span className="ml-auto text-[10px] font-mono text-primary bg-primary/10 px-1.5 py-0.5 rounded">beta</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path ||
            (item.path !== "/" && location.pathname.startsWith(item.path));
          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-all group",
                isActive
                  ? "bg-primary/10 text-primary font-medium"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent"
              )}
            >
              <item.icon className={cn("w-4 h-4", isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground")} />
              {item.label}
              {isActive && <ChevronRight className="w-3 h-3 ml-auto text-primary" />}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-border">
        <div className="text-[10px] text-muted-foreground font-mono">
          <div className="flex items-center justify-between">
            <span>Pipeline</span>
            <span className="text-primary">● Active</span>
          </div>
          <div className="mt-1 flex items-center justify-between">
            <span>Next run</span>
            <span className="text-foreground">06:00 AM</span>
          </div>
        </div>
      </div>
    </aside>
  );
}

// Mobile drawer sidebar
export function MobileDrawer({ open, onClose }) {
  const location = useLocation();

  if (!open) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 md:hidden"
        onClick={onClose}
      />
      {/* Drawer */}
      <aside className="fixed left-0 top-0 h-screen w-64 flex flex-col bg-card border-r border-border z-50 md:hidden animate-slide-in">
        {/* Logo */}
        <div className="flex items-center gap-2.5 px-5 py-5 border-b border-border">
          <div className="w-7 h-7 rounded-lg bg-primary flex items-center justify-center">
            <Zap className="w-4 h-4 text-primary-foreground" />
          </div>
          <span className="font-semibold text-foreground tracking-tight">RedArky</span>
          <span className="text-[10px] font-mono text-primary bg-primary/10 px-1.5 py-0.5 rounded">beta</span>
          <button onClick={onClose} className="ml-auto p-1 rounded-md text-muted-foreground hover:text-foreground">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path ||
              (item.path !== "/" && location.pathname.startsWith(item.path));
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={onClose}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-all group",
                  isActive
                    ? "bg-primary/10 text-primary font-medium"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent"
                )}
              >
                <item.icon className={cn("w-4 h-4", isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground")} />
                {item.label}
                {isActive && <ChevronRight className="w-3 h-3 ml-auto text-primary" />}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="px-4 py-4 border-t border-border">
          <div className="text-[10px] text-muted-foreground font-mono">
            <div className="flex items-center justify-between">
              <span>Pipeline</span>
              <span className="text-primary">● Active</span>
            </div>
            <div className="mt-1 flex items-center justify-between">
              <span>Next run</span>
              <span className="text-foreground">06:00 AM</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}

// Mobile bottom nav bar
export function MobileBottomNav() {
  const location = useLocation();
  const primaryItems = navItems.slice(0, 5);

  return (
    <nav className="fixed bottom-0 left-0 right-0 h-16 bg-card border-t border-border z-40 md:hidden flex items-center">
      {primaryItems.map((item) => {
        const isActive = location.pathname === item.path ||
          (item.path !== "/" && location.pathname.startsWith(item.path));
        return (
          <Link
            key={item.path}
            to={item.path}
            className={cn(
              "flex-1 flex flex-col items-center justify-center gap-1 py-2 transition-colors",
              isActive ? "text-primary" : "text-muted-foreground"
            )}
          >
            <item.icon className="w-5 h-5" />
            <span className="text-[9px] font-medium leading-none truncate px-1 text-center">
              {item.label === "Engagement Queue" ? "Queue" :
               item.label === "Collected Data" ? "Data" :
               item.label}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}

// Default export for backwards compat
export default DesktopSidebar;