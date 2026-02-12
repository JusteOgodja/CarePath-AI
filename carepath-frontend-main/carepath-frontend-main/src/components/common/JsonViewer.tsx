import React from "react";
import { Copy, ChevronDown, ChevronUp, Check } from "lucide-react";
import { Button } from "@/components/ui/button";

interface JsonViewerProps {
  data: unknown;
  title?: string;
  defaultCollapsed?: boolean;
}

export function JsonViewer({ data, title = "JSON", defaultCollapsed = true }: JsonViewerProps) {
  const [collapsed, setCollapsed] = React.useState(defaultCollapsed);
  const [copied, setCopied] = React.useState(false);

  const jsonString = JSON.stringify(data, null, 2);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(jsonString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-lg border bg-muted/50">
      <div className="flex items-center justify-between px-4 py-2 border-b">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground"
        >
          {collapsed ? <ChevronDown className="h-4 w-4" /> : <ChevronUp className="h-4 w-4" />}
          {title}
        </button>
        <Button variant="ghost" size="sm" onClick={handleCopy} className="h-7 text-xs">
          {copied ? <Check className="h-3 w-3 mr-1" /> : <Copy className="h-3 w-3 mr-1" />}
          {copied ? "Copié" : "Copier"}
        </Button>
      </div>
      {!collapsed && (
        <pre className="p-4 text-xs font-mono overflow-auto max-h-64">{jsonString}</pre>
      )}
    </div>
  );
}
