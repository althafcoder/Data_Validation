import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, Circle, Loader2 } from "lucide-react";
import type { PipelineStep } from "@/lib/api";
import { PIPELINE_STEPS } from "@/lib/api";

interface ProcessingPipelineProps {
  onComplete: () => void;
}

export function ProcessingPipeline({ onComplete }: ProcessingPipelineProps) {
  const [steps, setSteps] = useState<PipelineStep[]>(
    PIPELINE_STEPS.map((s) => ({ ...s, status: "pending" }))
  );
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    if (currentStep >= steps.length) {
      const timer = setTimeout(onComplete, 600);
      return () => clearTimeout(timer);
    }

    setSteps((prev) =>
      prev.map((s, i) => ({
        ...s,
        status: i < currentStep ? "complete" : i === currentStep ? "in-progress" : "pending",
      }))
    );

    const delay = 800 + Math.random() * 1200;
    const timer = setTimeout(() => setCurrentStep((c) => c + 1), delay);
    return () => clearTimeout(timer);
  }, [currentStep, steps.length, onComplete]);

  const progress = Math.round((currentStep / steps.length) * 100);

  return (
    <div className="w-full max-w-xl mx-auto space-y-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-2"
      >
        <h2 className="text-2xl font-bold text-foreground">Processing Your Files</h2>
        <p className="text-muted-foreground text-sm">
          Our AI pipeline is validating your payroll data
        </p>
      </motion.div>

      {/* Progress bar */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }}>
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-muted-foreground">Progress</span>
          <span className="text-xs font-bold text-secondary">{progress}%</span>
        </div>
        <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
          <motion.div
            className="h-full rounded-full gradient-accent"
            initial={{ width: "0%" }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        </div>
      </motion.div>

      {/* Steps */}
      <div className="space-y-1">
        {steps.map((step, i) => (
          <motion.div
            key={step.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.08 }}
            className={`flex items-center gap-4 rounded-lg px-4 py-3 transition-all duration-300 ${
              step.status === "in-progress"
                ? "bg-secondary/10 border border-secondary/20"
                : step.status === "complete"
                ? "bg-success/5"
                : ""
            }`}
          >
            <div className="flex-shrink-0">
              {step.status === "complete" ? (
                <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring" }}>
                  <CheckCircle2 className="h-5 w-5 text-success" />
                </motion.div>
              ) : step.status === "in-progress" ? (
                <Loader2 className="h-5 w-5 text-secondary animate-spin" />
              ) : (
                <Circle className="h-5 w-5 text-muted-foreground/30" />
              )}
            </div>
            <div className="flex-1">
              <span
                className={`text-sm font-medium ${
                  step.status === "in-progress"
                    ? "text-secondary"
                    : step.status === "complete"
                    ? "text-foreground"
                    : "text-muted-foreground/50"
                }`}
              >
                {step.label}
              </span>
            </div>
            <span className="text-xs text-muted-foreground">
              {step.status === "complete" ? "Done" : step.status === "in-progress" ? "Running..." : ""}
            </span>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
