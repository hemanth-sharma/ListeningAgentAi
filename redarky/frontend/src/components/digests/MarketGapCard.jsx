import { useState } from "react";
import { ExternalLink, ChevronDown, ChevronUp, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";

const confidenceColor = (score) => {
  if (score >= 85) return "text-success bg-success/10 border-success/20";
  if (score >= 70) return "text-warning bg-warning/10 border-warning/20";
  return "text-destructive bg-destructive/10 border-destructive/20";
};

export default function MarketGapCard({ gap, onViewSpec }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden hover:border-primary/20 transition-all">
      {/* Header */}
      <div className="p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1">
            <div className="flex items-center gap-2 flex-wrap mb-2">
              <span className="text-[10px] font-mono uppercase text-muted-foreground bg-muted px-2 py-0.5 rounded">{gap.category}</span>
              <span className={cn("text-xs font-semibold px-2 py-0.5 rounded-full border tabular-nums", confidenceColor(gap.confidenceScore))}>
                {gap.confidenceScore}% confidence
              </span>
            </div>
            <h3 className="text-sm font-semibold text-foreground">{gap.title}</h3>
          </div>
          <TrendingUp className="w-4 h-4 text-muted-foreground flex-shrink-0 mt-1" />
        </div>

        <p className="mt-2 text-xs text-muted-foreground leading-relaxed line-clamp-3">{gap.problem}</p>

        {/* Evidence count */}
        <div className="mt-3 flex items-center gap-3 text-xs text-muted-foreground">
          <span>{gap.evidenceCount} supporting posts</span>
          <span>•</span>
          <span>{formatDistanceToNow(new Date(gap.detectedAt), { addSuffix: true })}</span>
        </div>
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="px-5 pb-4 space-y-4 border-t border-border pt-4">
          {/* Existing solutions */}
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2">Existing Solutions</p>
            <div className="flex flex-wrap gap-1.5">
              {gap.existingSolutions.map((sol, i) => (
                <span key={i} className="text-xs bg-muted text-muted-foreground px-2 py-0.5 rounded line-through opacity-70">
                  {sol}
                </span>
              ))}
            </div>
          </div>

          {/* Evidence links */}
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2">Evidence Links</p>
            <div className="space-y-1">
              {gap.supportingLinks.map((link, i) => (
                <a
                  key={i}
                  href={link.url}
                  className="flex items-center gap-1.5 text-xs text-primary hover:text-primary/80 transition-colors"
                >
                  <ExternalLink className="w-3 h-3 flex-shrink-0" />
                  {link.label}
                </a>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Footer actions */}
      <div className="flex items-center justify-between px-5 py-3 border-t border-border bg-muted/20">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          {expanded ? "Show less" : "View evidence"}
        </button>
        <button
          onClick={() => onViewSpec(gap.id)}
          className="flex items-center gap-1.5 text-xs text-primary hover:text-primary/80 transition-colors font-medium"
        >
          View Mini-Spec →
        </button>
      </div>
    </div>
  );
}