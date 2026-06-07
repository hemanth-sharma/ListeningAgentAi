import { X, Copy, CheckCircle } from "lucide-react";
import { useState } from "react";
import { format } from "date-fns";

export default function MiniSpecViewer({ spec, onClose }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(spec.spec, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!spec) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-card border border-border rounded-xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <div>
            <p className="text-xs text-muted-foreground font-mono mb-0.5">mini-spec v{spec.version}</p>
            <h3 className="text-sm font-semibold text-foreground">{spec.title}</h3>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-muted-foreground bg-muted border border-border rounded-md hover:text-foreground transition-colors"
            >
              {copied ? <CheckCircle className="w-3 h-3 text-success" /> : <Copy className="w-3 h-3" />}
              {copied ? "Copied" : "Copy JSON"}
            </button>
            <button onClick={onClose} className="p-1.5 rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-colors">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="bg-muted/40 rounded-lg p-3">
              <p className="text-muted-foreground mb-1">Product Name</p>
              <p className="font-semibold text-foreground">{spec.spec.productName}</p>
            </div>
            <div className="bg-muted/40 rounded-lg p-3">
              <p className="text-muted-foreground mb-1">Target User</p>
              <p className="font-semibold text-foreground">{spec.spec.targetUser}</p>
            </div>
          </div>

          <div className="bg-primary/5 border border-primary/20 rounded-lg p-3">
            <p className="text-xs text-muted-foreground mb-1">Tagline</p>
            <p className="text-sm font-medium text-primary italic">"{spec.spec.tagline}"</p>
          </div>

          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2">Core Features</p>
            <ul className="space-y-1">
              {spec.spec.coreFeatures.map((f, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-foreground">
                  <span className="text-primary mt-0.5 flex-shrink-0">•</span>
                  {f}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2">Pricing</p>
            <div className="space-y-1 font-mono text-xs">
              {Object.entries(spec.spec.pricing).map(([tier, desc]) => (
                <div key={tier} className="flex gap-3">
                  <span className="text-muted-foreground capitalize w-10">{tier}:</span>
                  <span className="text-foreground">{desc}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-2">Tech Stack</p>
              <div className="space-y-1 font-mono text-xs">
                {Object.entries(spec.spec.techStack).map(([k, v]) => (
                  <div key={k} className="flex gap-2">
                    <span className="text-muted-foreground capitalize w-16">{k}:</span>
                    <span className="text-foreground">{v}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-2">Market Size</p>
              <p className="text-xs text-foreground">{spec.spec.marketSize}</p>
              <p className="text-xs font-medium text-muted-foreground mt-3 mb-1">Differentiator</p>
              <p className="text-xs text-foreground">{spec.spec.differentiator}</p>
            </div>
          </div>

          <div>
            <p className="text-xs font-medium text-muted-foreground mb-2">Next Steps</p>
            <ol className="space-y-1">
              {spec.spec.nextSteps.map((s, i) => (
                <li key={i} className="flex items-start gap-2 text-xs text-foreground">
                  <span className="text-primary font-mono flex-shrink-0">{i + 1}.</span>
                  {s}
                </li>
              ))}
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}