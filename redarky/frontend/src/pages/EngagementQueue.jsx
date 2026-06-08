import { useState } from "react";
import { ShieldAlert, CheckCircle } from "lucide-react";
import { mockApprovalQueue } from "@/lib/mockData";
import ApprovalQueueItem from "@/components/engagement/ApprovalQueueItem";

export default function EngagementQueue() {
  const [queue, setQueue] = useState(mockApprovalQueue);
  const [processed, setProcessed] = useState([]);

  const handleApprove = (id) => {
    setProcessed(p => [...p, { id, action: "approved" }]);
    setQueue(q => q.filter(i => i.id !== id));
  };

  const handleReject = (id) => {
    setProcessed(p => [...p, { id, action: "rejected" }]);
    setQueue(q => q.filter(i => i.id !== id));
  };

  return (
    <div className="space-y-6 animate-slide-in max-w-3xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-foreground">Engagement Queue</h1>
          <p className="text-sm text-muted-foreground mt-0.5">Review AI-drafted actions before external posting</p>
        </div>
        {queue.length > 0 && (
          <span className="flex items-center gap-1.5 px-3 py-1.5 bg-warning/10 border border-warning/30 text-warning text-xs font-medium rounded-lg">
            <ShieldAlert className="w-3.5 h-3.5" />
            {queue.length} pending
          </span>
        )}
      </div>

      {/* Safety notice */}
      <div className="flex items-start gap-3 bg-primary/5 border border-primary/20 rounded-xl p-4">
        <ShieldAlert className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-medium text-foreground">Human-in-the-loop protection</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            The AI agent cannot post externally without your explicit approval. Review each drafted action carefully before approving.
          </p>
        </div>
      </div>

      {/* Queue */}
      {queue.length > 0 ? (
        <div className="space-y-3">
          {queue.map(item => (
            <ApprovalQueueItem
              key={item.id}
              item={item}
              onApprove={handleApprove}
              onReject={handleReject}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-16 bg-card border border-border rounded-xl">
          <CheckCircle className="w-8 h-8 text-success mx-auto mb-3" />
          <p className="text-sm font-medium text-foreground">Queue cleared</p>
          <p className="text-xs text-muted-foreground mt-1">All actions have been reviewed.</p>
        </div>
      )}

      {/* Processed log */}
      {processed.length > 0 && (
        <div className="bg-card border border-border rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-border">
            <p className="text-xs font-medium text-muted-foreground">Processed this session</p>
          </div>
          <div className="divide-y divide-border">
            {processed.map(p => (
              <div key={p.id} className="px-4 py-2.5 flex items-center gap-3 text-xs">
                <span className={p.action === "approved" ? "text-success" : "text-destructive"}>
                  {p.action === "approved" ? "✓ Approved" : "✗ Rejected"}
                </span>
                <span className="text-muted-foreground font-mono">{p.id}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}