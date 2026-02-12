import React from "react";
import { useQuery } from "@tanstack/react-query";
import { listLatestIndicators, listIndicators } from "@/lib/api/endpoints";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { CardSkeleton, TableSkeleton } from "@/components/common/LoadingSkeleton";
import { ErrorState } from "@/components/common/ErrorState";
import { EmptyState } from "@/components/common/EmptyState";
import { Copy, Download, BarChart3, TrendingUp, Search } from "lucide-react";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { useDebounce } from "@/hooks/useDebounce";

const countries = [
  { code: "KEN", label: "Kenya" },
  { code: "TZA", label: "Tanzania" },
  { code: "UGA", label: "Uganda" },
  { code: "ETH", label: "Ethiopia" },
  { code: "NGA", label: "Nigeria" },
];

export function IndicatorsDashboard() {
  const [country, setCountry] = React.useState("KEN");
  const [indicatorCode, setIndicatorCode] = React.useState("");
  const debouncedCode = useDebounce(indicatorCode, 400);

  const latestQuery = useQuery({
    queryKey: ["indicators-latest", country],
    queryFn: () => listLatestIndicators(country),
  });

  const exploreQuery = useQuery({
    queryKey: ["indicators-explore", country, debouncedCode],
    queryFn: () => listIndicators({ country_code: country, indicator_code: debouncedCode || undefined }),
    enabled: true,
  });

  const handleCopyJson = async (data: unknown) => {
    await navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    toast.success("JSON copié");
  };

  const handleCsv = (data: object[]) => {
    if (!data.length) return;
    const headers = Object.keys(data[0]);
    const csv = [headers.join(","), ...data.map((r) => headers.map((h) => String((r as Record<string, unknown>)[h] ?? "")).join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `indicators-${country}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const chartData = React.useMemo(() => {
    const items = exploreQuery.data || [];
    if (!debouncedCode || items.length < 2) return [];
    return items
      .filter((i) => i.year != null && i.value != null)
      .sort((a, b) => (a.year || 0) - (b.year || 0))
      .map((i) => ({ year: i.year, value: i.value }));
  }, [exploreQuery.data, debouncedCode]);

  return (
    <div className="space-y-6">
      {/* Country selector */}
      <div className="premium-card p-5 flex items-end gap-4 flex-wrap">
        <div className="space-y-1.5">
          <Label className="stat-label">Pays</Label>
          <Select value={country} onValueChange={setCountry}>
            <SelectTrigger className="w-52 h-11"><SelectValue /></SelectTrigger>
            <SelectContent>
              {countries.map((c) => (
                <SelectItem key={c.code} value={c.code}>
                  <span className="font-medium">{c.label}</span> <span className="text-muted-foreground">({c.code})</span>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <Tabs defaultValue="latest">
        <TabsList className="bg-muted/60 p-1">
          <TabsTrigger value="latest" className="data-[state=active]:shadow-sm gap-2">
            <TrendingUp className="h-3.5 w-3.5" /> Dernières valeurs
          </TabsTrigger>
          <TabsTrigger value="explore" className="data-[state=active]:shadow-sm gap-2">
            <Search className="h-3.5 w-3.5" /> Explorer
          </TabsTrigger>
        </TabsList>

        <TabsContent value="latest" className="space-y-5 mt-6">
          {latestQuery.isLoading && (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3, 4, 5, 6].map((i) => <CardSkeleton key={i} />)}
            </div>
          )}
          {latestQuery.error && <ErrorState message="Impossible de charger les indicateurs" onRetry={() => latestQuery.refetch()} />}
          {latestQuery.data && latestQuery.data.length === 0 && <EmptyState title="Aucun indicateur" />}
          {latestQuery.data && latestQuery.data.length > 0 && (
            <>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {latestQuery.data.map((ind, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.04 }}
                    className="kpi-card"
                  >
                    <p className="text-2xs font-mono text-muted-foreground">{ind.indicator_code}</p>
                    <p className="stat-value mt-2">
                      {ind.value != null ? ind.value.toLocaleString() : "N/A"}
                    </p>
                    {ind.indicator_name && <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{ind.indicator_name}</p>}
                    <div className="flex gap-1.5 mt-3">
                      {ind.year && <Badge variant="outline" className="text-2xs shadow-none">{ind.year}</Badge>}
                      {ind.unit && <Badge variant="secondary" className="text-2xs shadow-none">{ind.unit}</Badge>}
                    </div>
                  </motion.div>
                ))}
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => handleCopyJson(latestQuery.data)} className="shadow-card">
                  <Copy className="mr-2 h-3.5 w-3.5" /> Copier JSON
                </Button>
                <Button variant="outline" size="sm" onClick={() => handleCsv(latestQuery.data as unknown as object[])} className="shadow-card">
                  <Download className="mr-2 h-3.5 w-3.5" /> CSV
                </Button>
              </div>
            </>
          )}
        </TabsContent>

        <TabsContent value="explore" className="space-y-5 mt-6">
          <div className="premium-card p-5 flex gap-4 flex-wrap items-end">
            <div className="space-y-1.5 flex-1 max-w-sm">
              <Label className="stat-label">Code indicateur</Label>
              <Input placeholder="ex: SH.XPD.CHEX.GD.ZS" value={indicatorCode} onChange={(e) => setIndicatorCode(e.target.value)} className="h-11" />
            </div>
          </div>

          {chartData.length >= 2 && (
            <div className="premium-card p-6">
              <h3 className="stat-label mb-5 flex items-center gap-2">
                <BarChart3 className="h-3.5 w-3.5 text-primary" /> Évolution temporelle
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
                  <XAxis dataKey="year" className="text-xs" tick={{ fontSize: 11 }} />
                  <YAxis className="text-xs" tick={{ fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "0.75rem",
                      fontSize: "12px",
                    }}
                  />
                  <Line type="monotone" dataKey="value" stroke="hsl(var(--primary))" strokeWidth={2.5} dot={{ r: 3, fill: "hsl(var(--primary))" }} activeDot={{ r: 5 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {exploreQuery.isLoading && <TableSkeleton cols={4} />}
          {exploreQuery.error && <ErrorState message="Erreur lors de l'exploration" onRetry={() => exploreQuery.refetch()} />}
          {exploreQuery.data && exploreQuery.data.length === 0 && <EmptyState title="Aucun résultat" />}
          {exploreQuery.data && exploreQuery.data.length > 0 && (
            <>
              <div className="premium-card overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-muted/30">
                      <TableHead className="text-2xs uppercase tracking-wider font-semibold">Code</TableHead>
                      <TableHead className="text-2xs uppercase tracking-wider font-semibold">Nom</TableHead>
                      <TableHead className="text-2xs uppercase tracking-wider font-semibold">Année</TableHead>
                      <TableHead className="text-2xs uppercase tracking-wider font-semibold">Valeur</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {exploreQuery.data.map((ind, i) => (
                      <TableRow key={i} className="hover:bg-muted/30 transition-colors">
                        <TableCell className="font-mono text-xs">{ind.indicator_code}</TableCell>
                        <TableCell className="text-sm">{ind.indicator_name || "—"}</TableCell>
                        <TableCell className="text-sm">{ind.year || "—"}</TableCell>
                        <TableCell className="text-sm font-semibold">{ind.value != null ? ind.value.toLocaleString() : "—"}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => handleCopyJson(exploreQuery.data)} className="shadow-card">
                  <Copy className="mr-2 h-3.5 w-3.5" /> Copier JSON
                </Button>
                <Button variant="outline" size="sm" onClick={() => handleCsv(exploreQuery.data as unknown as object[])} className="shadow-card">
                  <Download className="mr-2 h-3.5 w-3.5" /> CSV
                </Button>
              </div>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
