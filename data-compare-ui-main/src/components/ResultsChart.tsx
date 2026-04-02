import { motion } from "framer-motion";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import type { SummaryData } from "@/lib/api";

interface ResultsChartProps {
  summary: SummaryData;
}

const COLORS = [
  "hsl(152, 69%, 41%)",  // success - matched
  "hsl(38, 92%, 50%)",   // warning - mismatched
  "hsl(0, 84%, 60%)",    // destructive - missing ADP
  "hsl(199, 89%, 48%)",  // secondary - missing legacy
];

export function ResultsChart({ summary }: ResultsChartProps) {
  const data = [
    { name: "Matched", value: summary.matched },
    { name: "Mismatched", value: summary.mismatched },
    { name: "Missing in ADP", value: summary.missingInADP },
    { name: "Missing in Legacy", value: summary.missingInLegacy },
  ].filter((d) => d.value > 0);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.3 }}
      className="glass rounded-xl p-6"
    >
      <h3 className="text-sm font-semibold text-foreground mb-4">Distribution</h3>
      <div className="h-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={4}
              dataKey="value"
              strokeWidth={0}
            >
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                background: "hsl(0 0% 100% / 0.95)",
                border: "1px solid hsl(214 32% 91%)",
                borderRadius: "8px",
                fontSize: "12px",
              }}
            />
            <Legend
              verticalAlign="bottom"
              iconType="circle"
              iconSize={8}
              wrapperStyle={{ fontSize: "12px" }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  );
}
