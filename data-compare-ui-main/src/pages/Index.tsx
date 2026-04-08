import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Zap, ArrowRight, RotateCcw, Shield } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { FileDropZone } from "@/components/FileDropZone";
import { ProcessingPipeline } from "@/components/ProcessingPipeline";
import { SummaryCards } from "@/components/SummaryCards";
import { ResultsChart } from "@/components/ResultsChart";
import { DetailTabs } from "@/components/DetailTabs";
import { submitValidation, type ValidationResult } from "@/lib/api";

type AppState = "upload" | "processing" | "results";

const Index = () => {
  const [appState, setAppState] = useState<AppState>("upload");
  const [legacyFile, setLegacyFile] = useState<File | null>(null);
  const [adpFile, setAdpFile] = useState<File | null>(null);
  const [result, setResult] = useState<ValidationResult | null>(null);

  const canStart = legacyFile && adpFile;

  const handleStart = useCallback(() => {
    if (!canStart) return;
    setAppState("processing");
  }, [canStart]);

  const [activeGroup, setActiveGroup] = useState<string | null>(null);

  const handleProcessingComplete = useCallback(async () => {
    if (legacyFile && adpFile) {
      try {
        console.log("Starting Sequential Validation...");
        
        setActiveGroup("Personal Data");
        const personalRes = await submitValidation({ legacyFile, adpFile }, "personal");
        
        setActiveGroup("Job Information");
        const jobRes = await submitValidation({ legacyFile, adpFile }, "job");
        
        setActiveGroup("Tax Information");
        const taxRes = await submitValidation({ legacyFile, adpFile }, "tax");
        
        setActiveGroup("Compliance Data");
        const complianceRes = await submitValidation({ legacyFile, adpFile }, "compliance");
        
        setActiveGroup("Direct Deposit Info");
        const ddRes = await submitValidation({ legacyFile, adpFile }, "direct_deposit");
        
        setActiveGroup("Deduction Data");
        const dedRes = await submitValidation({ legacyFile, adpFile }, "deduction");

        setResult({
          ...personalRes,
          jobSessionId: jobRes.sessionId,
          taxSessionId: taxRes.sessionId,
          complianceSessionId: complianceRes.sessionId,
          ddSessionId: ddRes.sessionId,
          dedSessionId: dedRes.sessionId
        });
        setAppState("results");
        setActiveGroup(null);
      } catch (err: any) {
        console.error(err);
        alert(`Verification failed: ${err.message || "Unknown error"}`);
        setAppState("upload");
        setActiveGroup(null);
      }
    }
  }, [legacyFile, adpFile]);

  const handleReset = useCallback(() => {
    setAppState("upload");
    setLegacyFile(null);
    setAdpFile(null);
    setResult(null);
  }, []);

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b">
        <div className="container flex items-center justify-between h-16">
          <div className="flex items-center gap-2.5">
            <div className="rounded-lg gradient-accent p-2">
              <Shield className="h-5 w-5 text-accent-foreground" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-foreground leading-none">PayrollValidator</h1>
              <p className="text-[10px] text-muted-foreground">AI-Powered Data Validation</p>
            </div>
          </div>
          {appState === "results" && (
            <Button variant="outline" size="sm" onClick={handleReset} className="gap-1.5">
              <RotateCcw className="h-3.5 w-3.5" />
              New Validation
            </Button>
          )}
        </div>
      </header>

      <main className="container py-8">
        <AnimatePresence mode="wait">
          {/* UPLOAD STATE */}
          {appState === "upload" && (
            <motion.div
              key="upload"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="max-w-2xl mx-auto space-y-8"
            >
              {/* Hero */}
              <div className="text-center space-y-3 pt-8">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", delay: 0.1 }}
                  className="inline-flex rounded-full gradient-accent p-3 mb-2 animate-pulse-glow"
                >
                  <Zap className="h-7 w-7 text-accent-foreground" />
                </motion.div>
                <h1 className="text-3xl md:text-4xl font-bold text-foreground">
                  Validate your payroll data{" "}
                  <span className="text-gradient">in seconds</span>
                </h1>
                <p className="text-muted-foreground max-w-md mx-auto">
                  Upload your Legacy/Paycor and ADP files. Our AI pipeline detects, maps, and compares every field automatically.
                </p>
              </div>

              {/* Upload Tabs */}
              <div className="glass rounded-2xl p-6 space-y-6">
                <Tabs defaultValue="legacy" className="space-y-4">
                  <TabsList className="w-full grid grid-cols-2">
                    <TabsTrigger value="legacy" className="gap-2">
                      {legacyFile && <span className="h-2 w-2 rounded-full bg-success" />}
                      Legacy / Paycor
                    </TabsTrigger>
                    <TabsTrigger value="adp" className="gap-2">
                      {adpFile && <span className="h-2 w-2 rounded-full bg-success" />}
                      ADP File
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="legacy">
                    <FileDropZone
                      label="Upload your Legacy or Paycor payroll file"
                      file={legacyFile}
                      onFileSelect={setLegacyFile}
                    />
                  </TabsContent>

                  <TabsContent value="adp">
                    <FileDropZone
                      label="Upload your ADP payroll file"
                      file={adpFile}
                      onFileSelect={setAdpFile}
                    />
                  </TabsContent>
                </Tabs>

                <Button
                  onClick={handleStart}
                  disabled={!canStart}
                  className="w-full h-12 text-base font-semibold gradient-accent text-accent-foreground border-0 gap-2 glow-cyan disabled:opacity-40 disabled:shadow-none"
                >
                  Start Validation
                  <ArrowRight className="h-5 w-5" />
                </Button>
              </div>

              {/* Status pills */}
              <div className="flex items-center justify-center gap-6 text-xs text-muted-foreground">
                <span className="flex items-center gap-1.5">
                  <span className={`h-2 w-2 rounded-full ${legacyFile ? "bg-success" : "bg-border"}`} />
                  Legacy file {legacyFile ? "ready" : "pending"}
                </span>
                <span className="flex items-center gap-1.5">
                  <span className={`h-2 w-2 rounded-full ${adpFile ? "bg-success" : "bg-border"}`} />
                  ADP file {adpFile ? "ready" : "pending"}
                </span>
              </div>
            </motion.div>
          )}

          {/* PROCESSING STATE */}
          {appState === "processing" && (
            <motion.div
              key="processing"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="pt-16 max-w-md mx-auto"
            >
              {activeGroup && (
                <div className="text-center mb-6">
                  <span className="px-3 py-1 rounded-full bg-accent/20 text-accent text-xs font-medium animate-pulse">
                    Currently Validating: {activeGroup}
                  </span>
                </div>
              )}
              <ProcessingPipeline onComplete={handleProcessingComplete} />
            </motion.div>
          )}

          {/* RESULTS STATE */}
          {appState === "results" && result && (
            <motion.div
              key="results"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              <div>
                <h2 className="text-2xl font-bold text-foreground">Validation Results</h2>
                <p className="text-sm text-muted-foreground">
                  Comparison complete — review your payroll data below
                </p>
              </div>

              <SummaryCards summary={result.summary} />

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                  <DetailTabs result={result} />
                </div>
                <div>
                  <ResultsChart summary={result.summary} />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
};

export default Index;
