import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CentresTable } from "@/components/admin/CentresTable";
import { ReferencesTable } from "@/components/admin/ReferencesTable";
import { Building2, GitBranch, Network } from "lucide-react";
import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n";

export default function AdminNetworkPage() {
  const { language } = useI18n();
  const isFr = language === "fr";

  return (
    <div className="space-y-8 pb-20 lg:pb-0">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="page-header">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl shadow-card" style={{ background: "var(--gradient-primary)" }}>
            <Network className="h-5 w-5 text-primary-foreground" />
          </div>
          <div>
            <h1>{isFr ? "Administration du réseau" : "Network Administration"}</h1>
            <p>{isFr ? "Gérez les centres de santé et leurs connexions" : "Manage health centers and their links"}</p>
          </div>
        </div>
      </motion.div>

      <Tabs defaultValue="centres">
        <TabsList className="bg-muted/60 p-1">
          <TabsTrigger value="centres" className="gap-2 data-[state=active]:shadow-sm">
            <Building2 className="h-4 w-4" /> {isFr ? "Centres" : "Centers"}
          </TabsTrigger>
          <TabsTrigger value="references" className="gap-2 data-[state=active]:shadow-sm">
            <GitBranch className="h-4 w-4" /> {isFr ? "Références" : "Referrals routes"}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="centres" className="mt-6">
          <CentresTable />
        </TabsContent>

        <TabsContent value="references" className="mt-6">
          <ReferencesTable />
        </TabsContent>
      </Tabs>
    </div>
  );
}
