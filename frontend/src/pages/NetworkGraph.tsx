import React from "react";
import { useQuery } from "@tanstack/react-query";
import { Network, Loader2 } from "lucide-react";
import { listCentres, listReferences } from "@/lib/api/endpoints";
import type { Centre, Reference } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ErrorState } from "@/components/common/ErrorState";
import { EmptyState } from "@/components/common/EmptyState";
import { useI18n } from "@/lib/i18n";

type SimNode = {
  centre: Centre;
  x: number;
  y: number;
  z: number;
  vx: number;
  vy: number;
  vz: number;
};

type SimLink = {
  source: number;
  target: number;
  travelMinutes: number;
};

type RenderPoint = {
  i: number;
  sx: number;
  sy: number;
  sr: number;
  depth: number;
};

const levelColors: Record<string, string> = {
  primary: "#23b19d",
  secondary: "#f0c95f",
  tertiary: "#f47b5c",
};

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function normalizeAngle(angle: number): number {
  let a = angle;
  while (a > Math.PI) a -= Math.PI * 2;
  while (a < -Math.PI) a += Math.PI * 2;
  return a;
}

function buildSimulation(centres: Centre[], refs: Reference[]): { nodes: SimNode[]; links: SimLink[] } {
  const nodes: SimNode[] = centres.map((centre, idx) => {
    const angle = (idx / Math.max(centres.length, 1)) * Math.PI * 2;
    const ring = 220 + (idx % 3) * 28;
    return {
      centre,
      x: Math.cos(angle) * ring,
      y: Math.sin(angle) * ring * 0.65,
      z: ((idx % 7) - 3) * 42,
      vx: 0,
      vy: 0,
      vz: 0,
    };
  });

  const idxById = new Map(nodes.map((n, i) => [n.centre.id, i]));
  const links: SimLink[] = refs
    .map((ref) => {
      const source = idxById.get(ref.source_id);
      const target = idxById.get(ref.dest_id);
      if (source == null || target == null || source === target) return null;
      return { source, target, travelMinutes: ref.travel_minutes };
    })
    .filter((link): link is SimLink => link !== null);

  return { nodes, links };
}

function project(node: SimNode, width: number, height: number): RenderPoint {
  const fov = 640;
  const perspective = fov / (fov - node.z);
  const sx = width / 2 + node.x * perspective;
  const sy = height / 2 + node.y * perspective;
  const sr = clamp(5.5 * perspective, 3, 16);
  return { i: -1, sx, sy, sr, depth: node.z };
}

export default function NetworkGraphPage() {
  const { language } = useI18n();
  const isFr = language === "fr";
  const [levelFilter, setLevelFilter] = React.useState("all");
  const [hovered, setHovered] = React.useState<Centre | null>(null);
  const [searchTerm, setSearchTerm] = React.useState("");
  const [focusTargetId, setFocusTargetId] = React.useState<string | null>(null);
  const [canvasSize, setCanvasSize] = React.useState({ w: 1100, h: 680 });

  const containerRef = React.useRef<HTMLDivElement | null>(null);
  const canvasRef = React.useRef<HTMLCanvasElement | null>(null);
  const hoveredIdxRef = React.useRef<number | null>(null);
  const hoveredIdRef = React.useRef<string | null>(null);
  const zoomRef = React.useRef(1);
  const rotXRef = React.useRef(-0.18);
  const rotYRef = React.useRef(0.32);
  const dragRef = React.useRef<{ active: boolean; x: number; y: number; moved: boolean }>({ active: false, x: 0, y: 0, moved: false });
  const spinRef = React.useRef({ vx: 0, vy: 0 });
  const renderNodesRef = React.useRef<Array<{ sx: number; sy: number; sr: number; centre: Centre }>>([]);
  const lowerSearchTerm = searchTerm.trim().toLowerCase();

  const centresQuery = useQuery({
    queryKey: ["centres"],
    queryFn: listCentres,
    refetchInterval: 5000,
  });

  const refsQuery = useQuery({
    queryKey: ["references"],
    queryFn: listReferences,
    refetchInterval: 5000,
  });

  const isLoading = centresQuery.isLoading || refsQuery.isLoading;
  const error = centresQuery.error || refsQuery.error;

  const filteredCentres = React.useMemo(() => {
    const centres = centresQuery.data ?? [];
    if (levelFilter === "all") return centres;
    return centres.filter((c) => c.level === levelFilter);
  }, [centresQuery.data, levelFilter]);

  const centreMap = React.useMemo(
    () => Object.fromEntries(filteredCentres.map((c) => [c.id, c])),
    [filteredCentres]
  );

  const filteredRefs = React.useMemo(
    () => (refsQuery.data ?? []).filter((r) => Boolean(centreMap[r.source_id] && centreMap[r.dest_id])),
    [refsQuery.data, centreMap]
  );

  const focusedCentre = React.useMemo(() => {
    if (!focusTargetId) return null;
    return filteredCentres.find((c) => c.id === focusTargetId) ?? null;
  }, [filteredCentres, focusTargetId]);

  const resetCamera = React.useCallback(() => {
    setFocusTargetId(null);
    zoomRef.current = 1;
    rotXRef.current = -0.18;
    rotYRef.current = 0.32;
    spinRef.current = { vx: 0, vy: 0 };
  }, []);

  const handleSearchFocus = React.useCallback(() => {
    if (!lowerSearchTerm) {
      setFocusTargetId(null);
      setHovered(null);
      return;
    }

    const match = filteredCentres.find(
      (c) => c.id.toLowerCase().includes(lowerSearchTerm) || c.name.toLowerCase().includes(lowerSearchTerm)
    );

    if (!match) return;

    setFocusTargetId(match.id);
    setHovered(match);
    hoveredIdRef.current = match.id;
  }, [filteredCentres, lowerSearchTerm]);

  React.useEffect(() => {
    const node = containerRef.current;
    if (!node) return;

    const observer = new ResizeObserver((entries) => {
      const rect = entries[0]?.contentRect;
      if (!rect) return;
      const width = Math.floor(rect.width) - 8;
      setCanvasSize({
        w: Math.max(320, width),
        h: Math.max(360, Math.floor(width < 640 ? width * 0.8 : width * 0.56)),
      });
    });

    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  React.useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || filteredCentres.length === 0) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.floor(canvasSize.w * dpr);
    canvas.height = Math.floor(canvasSize.h * dpr);
    canvas.style.width = `${canvasSize.w}px`;
    canvas.style.height = `${canvasSize.h}px`;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const sim = buildSimulation(filteredCentres, filteredRefs);
    const nodes = sim.nodes;
    const links = sim.links;
    const indexById = new Map(nodes.map((n, i) => [n.centre.id, i]));

    const mouse = { x: -10000, y: -10000 };
    let raf = 0;
    let t = 0;

    const onMove = (ev: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const x = ev.clientX - rect.left;
      const y = ev.clientY - rect.top;
      const drag = dragRef.current;

      if (drag.active) {
        const dx = x - drag.x;
        const dy = y - drag.y;
        if (Math.abs(dx) + Math.abs(dy) > 1.5) drag.moved = true;
        rotYRef.current += dx * 0.006;
        rotXRef.current = clamp(rotXRef.current + dy * 0.005, -1.2, 1.2);
        spinRef.current.vy = dx * 0.00035;
        spinRef.current.vx = dy * 0.00025;
        drag.x = x;
        drag.y = y;
      }

      mouse.x = x;
      mouse.y = y;
    };
    const onLeave = () => {
      mouse.x = -10000;
      mouse.y = -10000;
      dragRef.current.active = false;
      hoveredIdxRef.current = null;
      hoveredIdRef.current = null;
      setHovered(null);
    };
    const onDown = (ev: MouseEvent) => {
      if (ev.button !== 0) return;
      const rect = canvas.getBoundingClientRect();
      dragRef.current = { active: true, x: ev.clientX - rect.left, y: ev.clientY - rect.top, moved: false };
    };
    const onCanvasUp = (ev: MouseEvent) => {
      const drag = dragRef.current;
      if (!drag.active) return;

      const rect = canvas.getBoundingClientRect();
      const x = ev.clientX - rect.left;
      const y = ev.clientY - rect.top;

      if (!drag.moved) {
        let nearest: { centre: Centre; d: number } | null = null;
        for (const rn of renderNodesRef.current) {
          const dx = x - rn.sx;
          const dy = y - rn.sy;
          const d = Math.sqrt(dx * dx + dy * dy);
          if (d < rn.sr + 9 && (!nearest || d < nearest.d)) {
            nearest = { centre: rn.centre, d };
          }
        }

        if (nearest) {
          setFocusTargetId(nearest.centre.id);
          setHovered(nearest.centre);
          hoveredIdRef.current = nearest.centre.id;
        }
      }

      dragRef.current.active = false;
    };
    const onUp = () => {
      dragRef.current.active = false;
    };
    const onWheel = (ev: WheelEvent) => {
      ev.preventDefault();
      const factor = Math.exp(-ev.deltaY * 0.0012);
      zoomRef.current = clamp(zoomRef.current * factor, 0.45, 2.6);
    };

    canvas.addEventListener("mousedown", onDown);
    canvas.addEventListener("mouseup", onCanvasUp);
    window.addEventListener("mouseup", onUp);
    canvas.addEventListener("mousemove", onMove);
    canvas.addEventListener("mouseleave", onLeave);
    canvas.addEventListener("wheel", onWheel, { passive: false });

    const animate = () => {
      t += 1;

      for (let i = 0; i < nodes.length; i += 1) {
        const n = nodes[i];
        n.vx += (-n.x) * 0.0007;
        n.vy += (-n.y) * 0.0007;
        n.vz += (-n.z) * 0.0007;
      }

      for (let i = 0; i < nodes.length; i += 1) {
        const a = nodes[i];
        for (let j = i + 1; j < nodes.length; j += 1) {
          const b = nodes[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dz = a.z - b.z;
          const d2 = dx * dx + dy * dy + dz * dz + 80;
          const force = 1400 / d2;
          a.vx += (dx * force) * 0.0022;
          a.vy += (dy * force) * 0.0022;
          a.vz += (dz * force) * 0.0022;
          b.vx -= (dx * force) * 0.0022;
          b.vy -= (dy * force) * 0.0022;
          b.vz -= (dz * force) * 0.0022;
        }
      }

      for (const link of links) {
        const s = nodes[link.source];
        const d = nodes[link.target];
        const dx = d.x - s.x;
        const dy = d.y - s.y;
        const dz = d.z - s.z;
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1;
        const target = 190 + Math.min(link.travelMinutes, 90) * 0.65;
        const k = 0.00058;
        const f = (dist - target) * k;
        const ux = dx / dist;
        const uy = dy / dist;
        const uz = dz / dist;
        s.vx += ux * f;
        s.vy += uy * f;
        s.vz += uz * f;
        d.vx -= ux * f;
        d.vy -= uy * f;
        d.vz -= uz * f;
      }

      for (const n of nodes) {
        n.vx *= 0.94;
        n.vy *= 0.94;
        n.vz *= 0.94;

        n.x += n.vx;
        n.y += n.vy;
        n.z += n.vz;
      }

      const focusIdx = focusTargetId ? indexById.get(focusTargetId) : undefined;

      if (!dragRef.current.active && focusIdx != null) {
        const target = nodes[focusIdx];
        const targetYaw = Math.atan2(-target.x, target.z);
        const z1AtTargetYaw = -target.x * Math.sin(targetYaw) + target.z * Math.cos(targetYaw);
        const targetPitch = clamp(Math.atan2(target.y, Math.max(28, z1AtTargetYaw)), -0.95, 0.95);

        const yawDelta = normalizeAngle(targetYaw - rotYRef.current);
        rotYRef.current += yawDelta * 0.08;
        rotXRef.current += (targetPitch - rotXRef.current) * 0.08;
        zoomRef.current += (1.42 - zoomRef.current) * 0.06;
        spinRef.current.vx *= 0.75;
        spinRef.current.vy *= 0.75;
      } else {
        rotYRef.current += spinRef.current.vy;
        rotXRef.current = clamp(rotXRef.current + spinRef.current.vx, -1.2, 1.2);
        spinRef.current.vx *= 0.93;
        spinRef.current.vy *= 0.93;
      }

      if (
        !focusTargetId &&
        !dragRef.current.active &&
        Math.abs(spinRef.current.vx) + Math.abs(spinRef.current.vy) < 0.00006
      ) {
        rotYRef.current += 0.0015;
      }

      ctx.clearRect(0, 0, canvasSize.w, canvasSize.h);

      const grd = ctx.createRadialGradient(
        canvasSize.w / 2,
        canvasSize.h / 2,
        40,
        canvasSize.w / 2,
        canvasSize.h / 2,
        canvasSize.w * 0.65
      );
      grd.addColorStop(0, "rgba(20, 28, 37, 0.14)");
      grd.addColorStop(1, "rgba(20, 28, 37, 0.32)");
      ctx.fillStyle = grd;
      ctx.fillRect(0, 0, canvasSize.w, canvasSize.h);

      const rx = rotXRef.current;
      const ry = rotYRef.current;
      const cx = Math.cos(rx);
      const sx = Math.sin(rx);
      const cy = Math.cos(ry);
      const sy = Math.sin(ry);
      const zoom = zoomRef.current;

      const transformed = nodes.map((n) => {
        const x1 = n.x * cy + n.z * sy;
        const z1 = -n.x * sy + n.z * cy;
        const y2 = n.y * cx - z1 * sx;
        const z2 = n.y * sx + z1 * cx;
        return { x: x1 * zoom, y: y2 * zoom, z: z2 };
      });

      const projected = transformed.map((n, i) => {
        const p = project({ ...nodes[i], x: n.x, y: n.y, z: n.z }, canvasSize.w, canvasSize.h);
        p.i = i;
        return p;
      });

      renderNodesRef.current = projected.map((p) => ({
        sx: p.sx,
        sy: p.sy,
        sr: p.sr,
        centre: nodes[p.i].centre,
      }));

      for (let i = 0; i < links.length; i += 1) {
        const link = links[i];
        const a = projected[link.source];
        const b = projected[link.target];
        const alpha = clamp((a.sr + b.sr) / 26, 0.12, 0.34);

        ctx.beginPath();
        ctx.strokeStyle = `rgba(170, 190, 210, ${alpha})`;
        ctx.lineWidth = 0.8 + alpha * 1.2;
        ctx.moveTo(a.sx, a.sy);
        ctx.lineTo(b.sx, b.sy);
        ctx.stroke();

        if (i % 2 === (t >> 4) % 2) {
          const p = (Math.sin((t + i * 25) * 0.05) + 1) / 2;
          const x = a.sx + (b.sx - a.sx) * p;
          const y = a.sy + (b.sy - a.sy) * p;
          ctx.beginPath();
          ctx.fillStyle = "rgba(91, 181, 255, 0.85)";
          ctx.arc(x, y, 1.8, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      projected.sort((a, b) => a.depth - b.depth);

      let nearest: { idx: number; d: number } | null = null;

      for (const p of projected) {
        const node = nodes[p.i];
        const color = levelColors[node.centre.level] ?? "#4fa3ff";
        const isFocused = focusTargetId != null && node.centre.id === focusTargetId;

        ctx.beginPath();
        ctx.fillStyle = isFocused ? "rgba(255, 255, 255, 0.45)" : `${color}33`;
        ctx.arc(p.sx, p.sy, isFocused ? p.sr * 2.4 : p.sr * 1.8, 0, Math.PI * 2);
        ctx.fill();

        ctx.beginPath();
        ctx.fillStyle = color;
        ctx.arc(p.sx, p.sy, isFocused ? p.sr * 1.25 : p.sr, 0, Math.PI * 2);
        ctx.fill();

        ctx.beginPath();
        ctx.fillStyle = "rgba(255,255,255,0.85)";
        ctx.arc(p.sx - p.sr * 0.25, p.sy - p.sr * 0.2, Math.max(1, p.sr * 0.22), 0, Math.PI * 2);
        ctx.fill();

        const dx = mouse.x - p.sx;
        const dy = mouse.y - p.sy;
        const d = Math.sqrt(dx * dx + dy * dy);
        if (d < p.sr + 9 && (!nearest || d < nearest.d)) {
          nearest = { idx: p.i, d };
        }
      }

      if (nearest) {
        hoveredIdxRef.current = nearest.idx;
        const targetCentre = nodes[nearest.idx].centre;
        if (hoveredIdRef.current !== targetCentre.id) {
          hoveredIdRef.current = targetCentre.id;
          setHovered(targetCentre);
        }
      } else if (hoveredIdxRef.current != null) {
        hoveredIdxRef.current = null;
        hoveredIdRef.current = null;
        setHovered(null);
      }

      raf = requestAnimationFrame(animate);
    };

    raf = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(raf);
      canvas.removeEventListener("mousedown", onDown);
      canvas.removeEventListener("mouseup", onCanvasUp);
      window.removeEventListener("mouseup", onUp);
      canvas.removeEventListener("mousemove", onMove);
      canvas.removeEventListener("mouseleave", onLeave);
      canvas.removeEventListener("wheel", onWheel);
    };
  }, [canvasSize.h, canvasSize.w, filteredCentres, filteredRefs, focusTargetId]);

  return (
    <div className="space-y-6 pb-20 lg:pb-0">
      <div className="page-header">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl shadow-card" style={{ background: "var(--gradient-primary)" }}>
            <Network className="h-5 w-5 text-primary-foreground" />
          </div>
          <div>
            <h1>{isFr ? "Graphe Réseau 3D" : "3D Network Graph"}</h1>
            <p>{isFr ? "Vue dynamique des connexions entre hôpitaux" : "Dynamic view of hospital connections"}</p>
          </div>
        </div>
      </div>

      <div className="premium-card p-4 flex flex-wrap items-center gap-3">
        <div className="space-y-1.5">
          <p className="stat-label">{isFr ? "Filtre niveau" : "Level filter"}</p>
          <Select value={levelFilter} onValueChange={setLevelFilter}>
            <SelectTrigger className="w-48 h-10">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">{isFr ? "Tous" : "All"}</SelectItem>
              <SelectItem value="primary">Primary</SelectItem>
              <SelectItem value="secondary">Secondary</SelectItem>
              <SelectItem value="tertiary">Tertiary</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="ml-auto flex gap-3 text-xs">
          <div className="kpi-card py-3 px-4 min-w-[120px]">
            <p className="stat-label">{isFr ? "Hôpitaux" : "Hospitals"}</p>
            <p className="text-xl font-bold">{filteredCentres.length}</p>
          </div>
          <div className="kpi-card py-3 px-4 min-w-[120px]">
            <p className="stat-label">{isFr ? "Connexions" : "Connections"}</p>
            <p className="text-xl font-bold">{filteredRefs.length}</p>
          </div>
        </div>
      </div>

      {isLoading && (
        <div className="premium-card p-8 flex items-center gap-3 text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          {isFr ? "Chargement du graphe..." : "Loading graph..."}
        </div>
      )}

      {error && (
        <ErrorState
          message={isFr ? "Impossible de charger le graphe réseau" : "Unable to load network graph"}
          onRetry={() => {
            centresQuery.refetch();
            refsQuery.refetch();
          }}
        />
      )}

      {!isLoading && !error && filteredCentres.length === 0 && (
        <EmptyState title={isFr ? "Aucun hôpital visible" : "No visible hospitals"} description={isFr ? "Vérifiez le filtre ou ajoutez des centres." : "Check filter or add centers."} />
      )}

      {!isLoading && !error && filteredCentres.length > 0 && (
        <div ref={containerRef} className="premium-card p-2 md:p-2 p-3 relative overflow-hidden">
          <div className="z-10 rounded-lg bg-card/95 border border-border/60 px-3 py-2 text-xs text-muted-foreground backdrop-blur-sm md:absolute md:left-4 md:top-4">
            {isFr ? "Molette: zoom | Glisser: rotation | Survol: détails du nœud" : "Wheel: zoom | Drag: rotate | Hover: node details"}
          </div>

          <div className="z-10 mt-2 flex flex-col gap-2 md:mt-0 md:absolute md:right-4 md:top-4 md:items-end">
            <div className="flex w-full items-center gap-2 rounded-lg border border-border/60 bg-card/95 p-2 backdrop-blur-sm md:w-auto">
              <Input
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSearchFocus();
                }}
                className="h-9 flex-1 text-xs md:w-56 md:flex-none md:h-8"
                placeholder={isFr ? "Chercher centre (nom ou ID)" : "Search center (name or ID)"}
              />
              <Button size="sm" variant="outline" className="h-9 text-xs md:h-8" onClick={handleSearchFocus}>
                {isFr ? "Focus" : "Focus"}
              </Button>
            </div>

            <div className="flex w-full flex-wrap items-center gap-2 rounded-lg border border-border/60 bg-card/95 p-2 backdrop-blur-sm md:w-auto md:flex-nowrap">
              <Button size="sm" variant="outline" className="h-9 w-9 p-0 md:h-8 md:w-8" onClick={() => (zoomRef.current = clamp(zoomRef.current * 1.12, 0.45, 2.6))}>+</Button>
              <Button size="sm" variant="outline" className="h-9 w-9 p-0 md:h-8 md:w-8" onClick={() => (zoomRef.current = clamp(zoomRef.current / 1.12, 0.45, 2.6))}>-</Button>
              <Button size="sm" variant="outline" className="h-9 text-xs md:h-8" onClick={resetCamera}>{isFr ? "Reset caméra" : "Reset camera"}</Button>
              {focusedCentre && (
                <Button size="sm" variant="outline" className="h-9 text-xs md:h-8" onClick={() => setFocusTargetId(null)}>{isFr ? "Stop focus" : "Stop focus"}</Button>
              )}
            </div>

            <div className="rounded-lg border border-border/60 bg-card/95 px-3 py-2 text-xs backdrop-blur-sm">
              <p className="font-semibold mb-1">{isFr ? "Légende" : "Legend"}</p>
              <div className="space-y-1">
                <div className="flex items-center gap-2"><span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: levelColors.primary }} /> Primary</div>
                <div className="flex items-center gap-2"><span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: levelColors.secondary }} /> Secondary</div>
                <div className="flex items-center gap-2"><span className="inline-block h-2.5 w-2.5 rounded-full" style={{ backgroundColor: levelColors.tertiary }} /> Tertiary</div>
              </div>
            </div>
          </div>

          <canvas ref={canvasRef} className="mt-3 md:mt-0 w-full rounded-xl bg-muted/20 cursor-crosshair" />

          {hovered && (
            <div className="mt-2 rounded-xl border border-border/60 bg-card/95 p-4 shadow-card backdrop-blur-md md:absolute md:right-4 md:top-[170px] md:mt-0 md:max-w-[320px]">
              <p className="text-xs uppercase tracking-wider text-muted-foreground">{isFr ? "Hôpital" : "Hospital"}</p>
              <p className="text-sm font-semibold mt-1">{hovered.name}</p>
              <p className="text-xs text-muted-foreground font-mono mt-0.5">{hovered.id}</p>
              <div className="mt-3 space-y-1.5 text-xs">
                <p><span className="text-muted-foreground">{isFr ? "Niveau:" : "Level:"}</span> {hovered.level}</p>
                <p><span className="text-muted-foreground">{isFr ? "Capacité:" : "Capacity:"}</span> {hovered.capacity_available}/{hovered.capacity_max}</p>
                <p><span className="text-muted-foreground">{isFr ? "Attente:" : "Wait:"}</span> {hovered.estimated_wait_minutes} min</p>
                <p><span className="text-muted-foreground">{isFr ? "Spécialités:" : "Specialties:"}</span> {hovered.specialities.join(", ") || "—"}</p>
              </div>
            </div>
          )}

          {focusedCentre && (
            <div className="mt-2 rounded-lg border border-border/60 bg-card/95 px-3 py-2 text-xs backdrop-blur-sm md:absolute md:left-4 md:bottom-4 md:mt-0">
              Focus: <span className="font-semibold">{focusedCentre.name}</span> <span className="text-muted-foreground font-mono">({focusedCentre.id})</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
