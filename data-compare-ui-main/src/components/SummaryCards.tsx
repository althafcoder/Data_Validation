import { motion } from "framer-motion";
import { Users, CheckCircle2, AlertTriangle, UserX, UserMinus } from "lucide-react";
import type { SummaryData } from "@/lib/api";

interface SummaryCardsProps {
  summary: SummaryData;
}

const cards = [
  { key: "totalEmployees", label: "Total Employees", icon: Users, color: "text-foreground", bg: "bg-muted" },
  { key: "matched", label: "Matched", icon: CheckCircle2, color: "text-success", bg: "bg-success/10" },
  { key: "mismatched", label: "Mismatched", icon: AlertTriangle, color: "text-warning", bg: "bg-warning/10" },
  { key: "missingInADP", label: "Missing in ADP", icon: UserX, color: "text-destructive", bg: "bg-destructive/10" },
  { key: "missingInLegacy", label: "Missing in Legacy", icon: UserMinus, color: "text-secondary", bg: "bg-secondary/10" },
] as const;

function AnimatedCounter({ value }: { value: number }) {
  return (
    <motion.span
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="text-3xl font-bold text-foreground"
    >
      {value}
    </motion.span>
  );
}

export function SummaryCards({ summary }: SummaryCardsProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      {cards.map((card, i) => {
        const Icon = card.icon;
        const value = summary[card.key];
        return (
          <motion.div
            key={card.key}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="glass rounded-xl p-5 space-y-3 hover:shadow-lg transition-shadow"
          >
            <div className={`inline-flex rounded-lg p-2 ${card.bg}`}>
              <Icon className={`h-5 w-5 ${card.color}`} />
            </div>
            <div>
              <AnimatedCounter value={value} />
              <p className="text-xs text-muted-foreground mt-1">{card.label}</p>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
