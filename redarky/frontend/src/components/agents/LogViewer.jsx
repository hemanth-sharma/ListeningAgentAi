import { useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { format } from "date-fns";
import { CheckCircle, AlertCircle, Info, AlertTriangle, Terminal } from "lucide-react";

const levelConfig = {
  info: { color: "text-analyzer", icon: Info, label: "INFO" },
  success: { color: "text-success", icon: CheckCircle, label: "OK  " },
  error: { color: "text-destructive", icon: AlertCircle, label: "ERR " },
  warning: { color: "text-warning", icon: AlertTriangle, label: "WARN" },
};

export default function LogViewer({ logs, title = "Agent Logs" }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  return (
    <div className="bg-[#080b10] border border-border rounded-xl overflow-hidden">
      {/* Terminal header */}
      <div className="flex items-center gap-2 px-4 py-3 bg-card border-b border-border">
        <div className="flex gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-destructive/70" />
          <span className="w-2.5 h-2.5 rounded-full bg-warning/70" />
          <span className="w-2.5 h-2.5 rounded-full bg-success/70" />
        </div>
        <Terminal className="w-3.5 h-3.5 text-muted-foreground ml-2" />
        <span className="text-xs text-muted-foreground font-mono">{title}</span>
        <span className="ml-auto text-[10px] font-mono text-success bg-success/10 px-2 py-0.5 rounded">
          {logs.length} lines
        </span>
      </div>

      {/* Log content */}
      <div className="h-72 overflow-y-auto p-4 font-mono text-xs space-y-1">
        {logs.map((log) => {
          const config = levelConfig[log.level] || levelConfig.info;
          const Icon = config.icon;
          return (
            <div key={log.id} className="flex items-start gap-2 group">
              <span className="text-muted-foreground/50 flex-shrink-0 tabular-nums">
                {format(new Date(log.ts), "HH:mm:ss")}
              </span>
              <span className={cn("flex-shrink-0 font-semibold", config.color)}>
                [{config.label}]
              </span>
              <span className="text-[#a8b5c8] leading-relaxed">{log.message}</span>
            </div>
          );
        })}
        <div className="flex items-center gap-2 mt-2">
          <span className="text-primary animate-pulse">▋</span>
          <span className="text-muted-foreground/40 text-[10px]">waiting for new events...</span>
        </div>
        <div ref={bottomRef} />
      </div>
    </div>
  );
}