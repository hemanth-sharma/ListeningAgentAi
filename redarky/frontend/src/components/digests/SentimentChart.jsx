import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-card border border-border rounded-lg p-3 text-xs shadow-xl">
        <p className="font-medium text-foreground mb-1.5">{label}</p>
        {payload.map(p => (
          <p key={p.name} style={{ color: p.color }} className="flex items-center gap-2">
            <span className="capitalize">{p.name}:</span>
            <span className="font-mono font-semibold">{p.value}%</span>
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function SentimentChart({ data }) {
  return (
    <div className="bg-card border border-border rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-foreground">Sentiment Trend</h3>
        <span className="text-xs text-muted-foreground">Last 7 days</span>
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <LineChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(217 32% 14%)" />
          <XAxis
            dataKey="date"
            tick={{ fill: "hsl(215 20% 50%)", fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "hsl(215 20% 50%)", fontSize: 10 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }}
            formatter={(value) => <span style={{ color: "hsl(215 20% 50%)" }}>{value}</span>}
          />
          <Line type="monotone" dataKey="positive" stroke="#22C55E" strokeWidth={2} dot={false} name="positive" />
          <Line type="monotone" dataKey="neutral" stroke="#06B6D4" strokeWidth={2} dot={false} name="neutral" />
          <Line type="monotone" dataKey="negative" stroke="#EF4444" strokeWidth={2} dot={false} name="negative" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}