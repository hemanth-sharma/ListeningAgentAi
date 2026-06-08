import { CheckCircle, XCircle, ExternalLink, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { formatDistanceToNow } from "date-fns";
import AgentBadge from "@/components/shared/AgentBadge";
import { cn } from "@/lib/utils";

export default function ApprovalQueueItem({ item, onApprove, onReject }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden transition-all hover:border-muted-foreground/20">
      {/* Header */}
      <div className="p-5">
        <div className="flex items-start gap-3">
          <AgentBadge type="worker" showLabel={false} className="flex-shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1">
              <span className="text-xs font-medium text-foreground">{item.actionType}</span>
              <span className="text-xs font-mono text-orange-400 bg-orange-400/10 px-2 py-0.5 rounded-full border border-orange-400/20">
                {item.subreddit}
              </span>
              <span className="text-[10px] text-muted-foreground ml-auto">
                {formatDistanceToNow(new Date(item.createdAt), { addSuffix: true })}
              </span>
            </div>

            {/* Original post */}
            <div className="bg-muted/40 rounded-lg p-3 mt-2">
              <div className="flex items-center gap-2 mb-1.5">
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Original Post</p>
                <a href={item.originalPost.url} className="text-muted-foreground hover:text-primary transition-colors ml-auto">
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <p className="text-xs font-medium text-foreground line-clamp-1">{item.originalPost.title}</p>
              <p className="text-[10px] text-muted-foreground mt-0.5">
                by {item.originalPost.author} · {item.originalPost.upvotes} upvotes · {item.originalPost.comments} comments
              </p>
            </div>

            {/* Expanded: full post + draft */}
            {expanded && (
              <div className="mt-3 space-y-3">
                <div className="bg-muted/20 rounded-lg p-3 border border-border">
                  <p className="text-[10px] text-muted-foreground mb-1.5 uppercase tracking-wider">Post Content</p>
                  <p className="text-xs text-foreground leading-relaxed">{item.originalPost.content}</p>
                </div>
                <div className="bg-primary/5 border border-primary/20 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1.5">
                    <p className="text-[10px] text-primary uppercase tracking-wider">AI Drafted Reply</p>
                    <span className="text-[10px] font-mono text-success bg-success/10 px-1.5 py-0.5 rounded">
                      {(item.confidence * 100).toFixed(0)}% confidence
                    </span>
                  </div>
                  <p className="text-xs text-foreground leading-relaxed">{item.draftedResponse}</p>
                </div>
              </div>
            )}

            <button
              onClick={() => setExpanded(!expanded)}
              className="mt-2 flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors"
            >
              {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              {expanded ? "Collapse" : "Preview draft"}
            </button>
          </div>
        </div>
      </div>

      {/* Action buttons */}
      <div className="flex items-center gap-2 px-5 py-3 border-t border-border bg-muted/10">
        <button
          onClick={() => onApprove(item.id)}
          className="flex items-center gap-1.5 px-4 py-1.5 bg-success/10 text-success border border-success/30 rounded-lg text-xs font-medium hover:bg-success/20 transition-colors"
        >
          <CheckCircle className="w-3.5 h-3.5" />
          Approve & Post
        </button>
        <button
          onClick={() => onReject(item.id)}
          className="flex items-center gap-1.5 px-4 py-1.5 bg-destructive/10 text-destructive border border-destructive/30 rounded-lg text-xs font-medium hover:bg-destructive/20 transition-colors"
        >
          <XCircle className="w-3.5 h-3.5" />
          Reject
        </button>
        <span className="ml-auto text-[10px] text-muted-foreground font-mono">
          {(item.confidence * 100).toFixed(0)}% AI confidence
        </span>
      </div>
    </div>
  );
}