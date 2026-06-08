import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, ArrowRight, Check, Plus, X, Clock, Radio, BarChart2, Wrench, Lock } from "lucide-react";
import { cn } from "@/lib/utils";

const STEPS = ["Mission Core", "Agent Pipeline", "Review & Activate"];

const sourceOptions = ["Reddit", "Hacker News", "RSS Feeds", "GitHub Trending"];
const goalTypes = ["SaaS Discovery", "Opinion Analysis", "Competitive Research", "Custom"];

const agentTypes = [
  { type: "collector", label: "Collector", icon: Radio, color: "text-collector", bg: "bg-collector/10 border-collector/30", description: "Scrapes & collects data from configured sources" },
  { type: "analyzer", label: "Analyzer", icon: BarChart2, color: "text-analyzer", bg: "bg-analyzer/10 border-analyzer/30", description: "Analyzes collected data to find patterns & gaps" },
  { type: "worker", label: "Worker", icon: Wrench, color: "text-worker", bg: "bg-worker/10 border-worker/30", description: "Executes output tasks, stores results, sends alerts" },
];

function StepIndicator({ steps, current }) {
  return (
    <div className="flex items-center gap-0">
      {steps.map((step, i) => (
        <div key={i} className="flex items-center">
          <div className="flex flex-col items-center">
            <div className={cn(
              "w-7 h-7 rounded-full border-2 flex items-center justify-center text-xs font-semibold transition-all",
              i < current ? "bg-primary border-primary text-primary-foreground" :
              i === current ? "border-primary text-primary" :
              "border-border text-muted-foreground"
            )}>
              {i < current ? <Check className="w-3.5 h-3.5" /> : i + 1}
            </div>
            <span className={cn(
              "text-[10px] mt-1 font-medium",
              i === current ? "text-primary" : "text-muted-foreground"
            )}>{step}</span>
          </div>
          {i < steps.length - 1 && (
            <div className={cn(
              "w-16 md:w-24 h-px mx-1 mb-4 transition-colors",
              i < current ? "bg-primary" : "bg-border"
            )} />
          )}
        </div>
      ))}
    </div>
  );
}

function AgentCard({ agent, onUpdate, onRemove }) {
  const config = agentTypes.find(a => a.type === agent.type);
  const Icon = config.icon;

  return (
    <div className={cn("border rounded-xl p-5 space-y-4", config.bg)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className={cn("w-4 h-4", config.color)} />
          <span className={cn("text-sm font-semibold", config.color)}>{config.label} Agent</span>
        </div>
        <button onClick={onRemove} className="p-1 rounded hover:bg-muted/50 text-muted-foreground hover:text-foreground transition-colors">
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      <div>
        <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
          {agent.type === "collector" && "Data collection priorities & keywords"}
          {agent.type === "analyzer" && "Analysis instructions"}
          {agent.type === "worker" && "Task instructions"}
        </label>
        <textarea
          value={agent.prompt}
          onChange={e => onUpdate({ ...agent, prompt: e.target.value })}
          placeholder={
            agent.type === "collector"
              ? "e.g., Focus on posts with >10 comments. Keywords: CI/CD, observability, developer tools..."
              : agent.type === "analyzer"
              ? "e.g., Identify recurring pain points. Look for unmet needs with >5 upvotes. Confidence threshold: 0.75..."
              : "e.g., Generate mini-specs for gaps with confidence >0.8. Draft Reddit replies. Send digest email to..."
          }
          rows={3}
          className="w-full bg-background/50 border border-border/60 rounded-lg px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors resize-none"
        />
      </div>

      {agent.type === "worker" && (
        <div>
          <label className="text-xs font-medium text-muted-foreground mb-2 block">Metadata (key-value)</label>
          <div className="space-y-2">
            {(agent.metadata || []).map((kv, i) => (
              <div key={i} className="flex gap-2">
                <input
                  value={kv.key}
                  onChange={e => {
                    const m = [...(agent.metadata || [])];
                    m[i] = { ...m[i], key: e.target.value };
                    onUpdate({ ...agent, metadata: m });
                  }}
                  placeholder="key"
                  className="flex-1 bg-background/50 border border-border/60 rounded-lg px-2 py-1.5 text-xs font-mono text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50"
                />
                <input
                  value={kv.value}
                  onChange={e => {
                    const m = [...(agent.metadata || [])];
                    m[i] = { ...m[i], value: e.target.value };
                    onUpdate({ ...agent, metadata: m });
                  }}
                  placeholder="value"
                  className="flex-1 bg-background/50 border border-border/60 rounded-lg px-2 py-1.5 text-xs font-mono text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50"
                />
                <button
                  onClick={() => onUpdate({ ...agent, metadata: (agent.metadata || []).filter((_, j) => j !== i) })}
                  className="text-muted-foreground hover:text-destructive transition-colors px-1"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
            <button
              onClick={() => onUpdate({ ...agent, metadata: [...(agent.metadata || []), { key: "", value: "" }] })}
              className="text-xs text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
            >
              <Plus className="w-3 h-3" /> Add metadata field
            </button>
          </div>
        </div>
      )}

      <div>
        <label className="text-xs font-medium text-muted-foreground mb-1.5 block flex items-center gap-1">
          <Clock className="w-3 h-3" /> Schedule
        </label>
        <input
          type="text"
          value={agent.schedule}
          onChange={e => onUpdate({ ...agent, schedule: e.target.value })}
          placeholder="e.g., 0 6 * * * (Daily at 6 AM)"
          className="w-full bg-background/50 border border-border/60 rounded-lg px-3 py-1.5 text-xs font-mono text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50"
        />
      </div>
    </div>
  );
}

export default function MissionBuilder() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({
    title: "",
    goal: "",
    goalType: "",
    dataSource: "scrape",
    sources: [],
    apifyScraperId: "",
    providedDataUrl: "",
    agents: [],
  });

  const toggleSource = (source) => {
    setForm(f => ({
      ...f,
      sources: f.sources.includes(source)
        ? f.sources.filter(s => s !== source)
        : [...f.sources, source]
    }));
  };

  const addAgent = (type) => {
    if (form.agents.find(a => a.type === type)) return;
    setForm(f => ({
      ...f,
      agents: [...f.agents, { type, prompt: "", schedule: "", metadata: [] }]
    }));
  };

  const updateAgent = (index, updated) => {
    setForm(f => {
      const agents = [...f.agents];
      agents[index] = updated;
      return { ...f, agents };
    });
  };

  const removeAgent = (index) => {
    setForm(f => ({ ...f, agents: f.agents.filter((_, i) => i !== index) }));
  };

  const handleCreate = () => {
    navigate("/missions");
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8 animate-slide-in">
      {/* Back */}
      <button onClick={() => navigate("/missions")} className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors">
        <ArrowLeft className="w-3.5 h-3.5" />
        Back to Missions
      </button>

      {/* Title */}
      <div>
        <h1 className="text-xl font-semibold text-foreground">Create New Mission</h1>
        <p className="text-sm text-muted-foreground mt-0.5">Define a goal and attach AI agents to automate your research pipeline.</p>
      </div>

      {/* Step indicator */}
      <StepIndicator steps={STEPS} current={step} />

      {/* Step content */}
      <div className="bg-card border border-border rounded-xl p-6 space-y-5">
        {step === 0 && (
          <>
            <h2 className="text-sm font-semibold text-foreground">Mission Core</h2>

            <div>
              <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Mission Title *</label>
              <input
                type="text"
                value={form.title}
                onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
                placeholder="e.g., SaaS Gap Finder – DevTools"
                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Goal Description *</label>
              <textarea
                value={form.goal}
                onChange={e => setForm(f => ({ ...f, goal: e.target.value }))}
                placeholder="Describe in natural language what this mission should achieve..."
                rows={4}
                className="w-full bg-background border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors resize-none"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Goal Type</label>
              <div className="grid grid-cols-2 gap-2">
                {goalTypes.map(type => (
                  <button
                    key={type}
                    onClick={() => setForm(f => ({ ...f, goalType: type }))}
                    className={cn(
                      "px-3 py-2 text-xs rounded-lg border transition-colors text-left",
                      form.goalType === type
                        ? "bg-primary/10 text-primary border-primary/30"
                        : "bg-background text-muted-foreground border-border hover:border-muted-foreground/40"
                    )}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground mb-2 block">Data Source</label>
              <div className="flex gap-2 mb-4">
                {["scrape", "provide"].map(mode => (
                  <button
                    key={mode}
                    onClick={() => setForm(f => ({ ...f, dataSource: mode }))}
                    className={cn(
                      "px-4 py-2 text-xs font-medium rounded-lg border transition-colors",
                      form.dataSource === mode
                        ? "bg-primary text-primary-foreground border-primary"
                        : "bg-background text-muted-foreground border-border hover:border-muted-foreground/40"
                    )}
                  >
                    {mode === "scrape" ? "Scrape Internet" : "Provide Data"}
                  </button>
                ))}
              </div>

              {form.dataSource === "scrape" && (
                <div className="space-y-3">
                  <div>
                    <label className="text-xs text-muted-foreground mb-2 block">Sources</label>
                    <div className="flex flex-wrap gap-2">
                      {sourceOptions.map(source => (
                        <button
                          key={source}
                          onClick={() => toggleSource(source)}
                          className={cn(
                            "px-3 py-1.5 text-xs rounded-full border transition-colors",
                            form.sources.includes(source)
                              ? "bg-primary/10 text-primary border-primary/30"
                              : "text-muted-foreground border-border hover:border-muted-foreground/40"
                          )}
                        >
                          {source}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground mb-1.5 block">Apify Scraper ID (optional)</label>
                    <input
                      type="text"
                      value={form.apifyScraperId}
                      onChange={e => setForm(f => ({ ...f, apifyScraperId: e.target.value }))}
                      placeholder="e.g., apify/reddit-scraper"
                      className="w-full bg-background border border-border rounded-lg px-3 py-2 text-xs font-mono text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50"
                    />
                  </div>
                </div>
              )}

              {form.dataSource === "provide" && (
                <div>
                  <label className="text-xs text-muted-foreground mb-1.5 block">External Data Source URL or DB connection</label>
                  <input
                    type="text"
                    value={form.providedDataUrl}
                    onChange={e => setForm(f => ({ ...f, providedDataUrl: e.target.value }))}
                    placeholder="postgresql://... or https://api.example.com/data"
                    className="w-full bg-background border border-border rounded-lg px-3 py-2 text-xs font-mono text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50"
                  />
                </div>
              )}
            </div>
          </>
        )}

        {step === 1 && (
          <>
            <h2 className="text-sm font-semibold text-foreground">Agent Pipeline</h2>
            <p className="text-xs text-muted-foreground">Agents run in order. Add agents based on what you need for this mission.</p>

            {/* Add agent buttons */}
            <div className="flex flex-wrap gap-2">
              {agentTypes.map(({ type, label, icon: Icon, color, bg }) => (
                <button
                  key={type}
                  onClick={() => addAgent(type)}
                  disabled={form.agents.some(a => a.type === type)}
                  className={cn(
                    "flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border transition-all",
                    form.agents.some(a => a.type === type)
                      ? "opacity-30 cursor-not-allowed"
                      : cn("hover:opacity-80 cursor-pointer", bg),
                    color
                  )}
                >
                  <Icon className="w-3.5 h-3.5" />
                  + {label}
                </button>
              ))}
              <button
                disabled
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-border text-muted-foreground/40 cursor-not-allowed"
              >
                <Lock className="w-3 h-3" />
                + Custom
                <span className="text-[9px] bg-muted px-1 py-0.5 rounded ml-0.5">Soon</span>
              </button>
            </div>

            {/* Agent cards */}
            <div className="space-y-3">
              {form.agents.map((agent, i) => (
                <div key={agent.type}>
                  {i > 0 && (
                    <div className="flex justify-center py-1">
                      <div className="w-px h-4 bg-border" />
                    </div>
                  )}
                  <AgentCard
                    agent={agent}
                    onUpdate={(updated) => updateAgent(i, updated)}
                    onRemove={() => removeAgent(i)}
                  />
                </div>
              ))}
              {form.agents.length === 0 && (
                <div className="text-center py-8 border border-dashed border-border rounded-xl text-xs text-muted-foreground">
                  Add at least one agent to continue
                </div>
              )}
            </div>
          </>
        )}

        {step === 2 && (
          <>
            <h2 className="text-sm font-semibold text-foreground">Review & Activate</h2>
            <div className="space-y-4">
              <div className="bg-muted/30 rounded-lg p-4 space-y-2 text-sm">
                <div className="flex gap-3">
                  <span className="text-muted-foreground min-w-[80px]">Title:</span>
                  <span className="text-foreground font-medium">{form.title || "—"}</span>
                </div>
                <div className="flex gap-3">
                  <span className="text-muted-foreground min-w-[80px]">Goal Type:</span>
                  <span className="text-foreground">{form.goalType || "—"}</span>
                </div>
                <div className="flex gap-3">
                  <span className="text-muted-foreground min-w-[80px]">Sources:</span>
                  <span className="text-foreground">{form.sources.join(", ") || form.providedDataUrl || "—"}</span>
                </div>
                <div className="flex gap-3">
                  <span className="text-muted-foreground min-w-[80px]">Agents:</span>
                  <span className="text-foreground capitalize">{form.agents.map(a => a.type).join(" → ") || "—"}</span>
                </div>
              </div>
              <div className="bg-primary/5 border border-primary/20 rounded-lg p-3 text-xs text-muted-foreground">
                <span className="text-primary font-medium">Note:</span> The mission will be saved but not triggered yet. Agents will run on their configured schedules.
              </div>
            </div>
          </>
        )}
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => step > 0 ? setStep(s => s - 1) : navigate("/missions")}
          className="flex items-center gap-1.5 px-4 py-2 text-sm text-muted-foreground border border-border rounded-lg hover:text-foreground hover:border-muted-foreground/40 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          {step === 0 ? "Cancel" : "Back"}
        </button>

        {step < STEPS.length - 1 ? (
          <button
            onClick={() => setStep(s => s + 1)}
            disabled={step === 0 && !form.title}
            className="flex items-center gap-1.5 px-4 py-2 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Next <ArrowRight className="w-3.5 h-3.5" />
          </button>
        ) : (
          <button
            onClick={handleCreate}
            className="flex items-center gap-1.5 px-5 py-2 text-sm bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-medium"
          >
            <Check className="w-3.5 h-3.5" />
            Create Mission
          </button>
        )}
      </div>
    </div>
  );
}