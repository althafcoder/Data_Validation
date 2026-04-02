import { useState } from "react";
import { motion } from "framer-motion";
import { Search, Download } from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "@/components/ui/table";
import { exportValidationResult, type ValidationResult, type CellStatus } from "@/lib/api";

interface DetailTabsProps {
  result: ValidationResult;
}

function StatusBadge({ status }: { status: CellStatus }) {
  const variants: Record<CellStatus, string> = {
    MATCH: "bg-success/10 text-success border-success/20",
    MISMATCH: "bg-warning/10 text-warning border-warning/20",
    ERROR: "bg-destructive/10 text-destructive border-destructive/20",
    BLANK: "bg-muted text-muted-foreground border-border",
  };
  return (
    <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[10px] font-semibold ${variants[status]}`}>
      {status}
    </span>
  );
}

export function DetailTabs({ result }: DetailTabsProps) {
  const [search, setSearch] = useState("");

  const filteredSheet = result.validationSheet.filter(
    (r) => r.employeeName.toLowerCase().includes(search.toLowerCase()) || r.employeeId.includes(search)
  );

  const filteredDisc = result.discrepancies.filter(
    (r) => r.employeeName.toLowerCase().includes(search.toLowerCase()) || r.field.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
      <Tabs defaultValue="validation" className="space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <TabsList className="bg-muted/50">
            <TabsTrigger value="validation">Validation Sheet</TabsTrigger>
            <TabsTrigger value="discrepancies">
              Discrepancies
              <Badge variant="destructive" className="ml-2 h-5 px-1.5 text-[10px]">
                {result.discrepancies.length}
              </Badge>
            </TabsTrigger>
            <TabsTrigger value="missing-adp">Missing in ADP</TabsTrigger>
            <TabsTrigger value="missing-legacy">Missing in Legacy</TabsTrigger>
          </TabsList>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 h-9 w-[200px] bg-card"
              />
            </div>
            <Button variant="outline" size="sm" className="h-9 gap-1.5" onClick={() => exportValidationResult(result.sessionId, result.jobSessionId, result.taxSessionId, result.complianceSessionId)}>
              <Download className="h-3.5 w-3.5" />
              Export
            </Button>
          </div>
        </div>

        <TabsContent value="validation" className="glass rounded-xl overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="w-[180px]">Employee</TableHead>
                <TableHead className="w-[100px]">ID</TableHead>
                {Object.keys(result.validationSheet[0]?.fields || {}).map((f) => (
                  <TableHead key={f} className="text-center text-xs">{f}</TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredSheet.map((row) => (
                <TableRow key={row.id}>
                  <TableCell className="font-medium text-sm">{row.employeeName}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">{row.employeeId}</TableCell>
                  {Object.values(row.fields).map((field, i) => (
                    <TableCell key={i} className="text-center">
                      <StatusBadge status={field.status} />
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="discrepancies" className="glass rounded-xl overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>Employee</TableHead>
                <TableHead>ID</TableHead>
                <TableHead>Field</TableHead>
                <TableHead>Legacy Value</TableHead>
                <TableHead>ADP Value</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredDisc.map((row) => (
                <TableRow key={row.id}>
                  <TableCell className="font-medium text-sm">{row.employeeName}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">{row.employeeId}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="text-xs">{row.field}</Badge>
                  </TableCell>
                  <TableCell className="text-sm text-destructive/80 bg-destructive/5 font-mono">{row.legacyValue}</TableCell>
                  <TableCell className="text-sm text-success bg-success/5 font-mono">{row.adpValue}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="missing-adp" className="glass rounded-xl overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>Employee Name</TableHead>
                <TableHead>Employee ID</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {result.missingInADP.map((row) => (
                <TableRow key={row.id}>
                  <TableCell className="font-medium">{row.employeeName}</TableCell>
                  <TableCell className="text-muted-foreground">{row.employeeId}</TableCell>
                  <TableCell>
                    <Badge variant="destructive" className="text-xs">Not found in ADP</Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>

        <TabsContent value="missing-legacy" className="glass rounded-xl overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>Employee Name</TableHead>
                <TableHead>Employee ID</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {result.missingInLegacy.map((row) => (
                <TableRow key={row.id}>
                  <TableCell className="font-medium">{row.employeeName}</TableCell>
                  <TableCell className="text-muted-foreground">{row.employeeId}</TableCell>
                  <TableCell>
                    <Badge className="text-xs bg-secondary/10 text-secondary border-secondary/20">Not found in Legacy</Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TabsContent>
      </Tabs>
    </motion.div>
  );
}
