import { cn } from "@/lib/utils";
import { Radio, BarChart2, Wrench } from "lucide-react";

const agentConfig = {
  collector: {
    label: "Collector",
    icon: Radio,
    color: "text-collector border-collector/30 bg-collector/10",
  },
  analyzer: {
    label: "Analyzer",
    icon: BarChart2,
    color: "text-analyzer border-analyzer/30 bg-analyzer/10",
  },
  worker: {
    label: "Worker",
    icon: Wrench,
    color: "text-worker border-worker/30 bg-worker/10",
  },
};

export default function AgentBadge({ type, showLabel = true, className }) {
  const config = agentConfig[type];
  if (!config) return null;
  const Icon = config.icon;
  return (
    <span className={cn(
      "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border",
      config.color,
      className
    )}>
      <Icon className="w-3 h-3" />
      {showLabel && config.label}
    </span>
  );
}