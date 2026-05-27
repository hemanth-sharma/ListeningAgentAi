import { Outlet, useLocation } from "react-router-dom";
import { useState } from "react";
import { DesktopSidebar, MobileDrawer, MobileBottomNav } from "./Sidebar";
import Header from "./Header";
import { mockMissions } from "@/lib/mockData";

export default function AppLayout() {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Derive active mission title from URL
  const missionMatch = location.pathname.match(/\/missions\/([^/]+)/);
  const activeMissionId = missionMatch ? missionMatch[1] : null;
  const activeMission = activeMissionId
    ? mockMissions.find(m => m.id === activeMissionId)
    : mockMissions.find(m => m.status === "Running");

  return (
    <div className="min-h-screen bg-background font-inter">
      {/* Desktop sidebar */}
      <DesktopSidebar />

      {/* Mobile drawer */}
      <MobileDrawer open={mobileMenuOpen} onClose={() => setMobileMenuOpen(false)} />

      {/* Header */}
      <Header
        activeMissionTitle={activeMission?.title}
        onMenuOpen={() => setMobileMenuOpen(true)}
      />

      {/* Main content */}
      <main className="md:ml-56 mt-14 min-h-[calc(100vh-3.5rem)] pb-16 md:pb-0">
        <div className="p-4 md:p-6">
          <Outlet />
        </div>
      </main>

      {/* Mobile bottom nav */}
      <MobileBottomNav />
    </div>
  );
}