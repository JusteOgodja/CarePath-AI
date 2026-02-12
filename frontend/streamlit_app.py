import json
import subprocess
import sys
from pathlib import Path

import networkx as nx
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network
from sqlalchemy import select

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:  # pragma: no cover - optional dependency
    st_autorefresh = None


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.db.models import CentreModel, ReferenceModel, get_session, init_db
from app.services.recommender import Recommender
from app.services.schemas import RecommandationRequest

st.set_page_config(page_title="CarePath AI Demo (Offline)", layout="wide")
st.title("CarePath AI - Live Demo (Offline)")

init_db()


@st.cache_data(ttl=3)
def fetch_centres_local() -> list[dict]:
    with get_session() as session:
        rows = session.scalars(select(CentreModel).order_by(CentreModel.id)).all()
    return [
        {
            "id": row.id,
            "name": row.name,
            "level": row.level,
            "specialities": [s.strip() for s in row.specialities.split(",") if s.strip()],
            "capacity_available": int(row.capacity_available),
            "estimated_wait_minutes": int(row.estimated_wait_minutes),
            "catchment_population": int(row.catchment_population or 0),
        }
        for row in rows
    ]


@st.cache_data(ttl=3)
def fetch_references_local() -> list[dict]:
    with get_session() as session:
        rows = session.scalars(select(ReferenceModel).order_by(ReferenceModel.id)).all()
    return [
        {
            "id": int(row.id),
            "source_id": row.source_id,
            "dest_id": row.dest_id,
            "travel_minutes": int(row.travel_minutes),
        }
        for row in rows
    ]


def build_graph(centres: list[dict], refs: list[dict]) -> nx.DiGraph:
    graph = nx.DiGraph()
    for centre in centres:
        graph.add_node(
            centre["id"],
            label=centre["name"],
            level=centre["level"],
            capacity_available=centre["capacity_available"],
            estimated_wait_minutes=centre["estimated_wait_minutes"],
            specialities=centre["specialities"],
        )
    for ref in refs:
        if graph.has_node(ref["source_id"]) and graph.has_node(ref["dest_id"]):
            graph.add_edge(ref["source_id"], ref["dest_id"], travel=ref["travel_minutes"])
    return graph


def apply_graph_filters(
    centres: list[dict],
    refs: list[dict],
    *,
    levels: list[str],
    required_speciality: str,
    min_capacity: int,
) -> nx.DiGraph:
    filtered_centres = []
    for centre in centres:
        if levels and centre["level"] not in levels:
            continue
        if required_speciality != "all" and required_speciality not in centre["specialities"]:
            continue
        if centre["capacity_available"] < min_capacity:
            continue
        filtered_centres.append(centre)

    ids = {c["id"] for c in filtered_centres}
    filtered_refs = [r for r in refs if r["source_id"] in ids and r["dest_id"] in ids]
    return build_graph(filtered_centres, filtered_refs)


def node_color(capacity: int, wait: int) -> str:
    if capacity <= 0:
        return "#b71c1c"  # red
    pressure = wait / max(capacity, 1)
    if pressure > 20:
        return "#e65100"  # orange
    if pressure > 10:
        return "#f9a825"  # yellow
    return "#2e7d32"  # green


def render_graph(graph: nx.DiGraph, selected_path: list[str] | None = None) -> None:
    selected_path = selected_path or []
    selected_edges = set(zip(selected_path, selected_path[1:])) if len(selected_path) > 1 else set()

    net = Network(height="620px", width="100%", directed=True)
    for node_id, attrs in graph.nodes(data=True):
        in_path = node_id in selected_path
        base_color = node_color(int(attrs.get("capacity_available", 0)), int(attrs.get("estimated_wait_minutes", 0)))
        color = "#1565c0" if in_path else base_color
        title = (
            f"{attrs.get('label', node_id)}<br>"
            f"Level: {attrs.get('level', '-') }<br>"
            f"Capacity: {attrs.get('capacity_available', '-') }<br>"
            f"Wait: {attrs.get('estimated_wait_minutes', '-') } min<br>"
            f"Specialities: {', '.join(attrs.get('specialities', []))}"
        )
        net.add_node(node_id, label=f"{node_id}\n{attrs.get('label', node_id)}", color=color, title=title)

    for src, dst, attrs in graph.edges(data=True):
        in_path = (src, dst) in selected_edges
        net.add_edge(
            src,
            dst,
            label=str(attrs.get("travel", "")),
            color="#d32f2f" if in_path else "#9e9e9e",
            width=4 if in_path else 1,
            arrows="to",
        )

    net.set_options(
        """
        {
          "physics": {"enabled": true, "stabilization": {"iterations": 150}},
          "interaction": {"hover": true, "navigationButtons": true, "keyboard": true}
        }
        """
    )

    html = net.generate_html(notebook=False)
    components.html(html, height=650)


def run_primary_demo() -> tuple[bool, str]:
    cmd = [sys.executable, "scripts/run_primary_demo.py", "--patients", "120", "--output", "docs/primary_demo_report.json"]
    try:
        result = subprocess.run(cmd, cwd=BACKEND_DIR, capture_output=True, text=True, check=True)
        return True, result.stdout
    except subprocess.CalledProcessError as exc:
        return False, exc.stderr or exc.stdout


def load_primary_demo_report() -> dict | None:
    path = BACKEND_DIR / "docs" / "primary_demo_report.json"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_benchmark_report() -> tuple[str | None, dict | None]:
    candidates = [
        BACKEND_DIR / "docs" / "final_benchmark_kenya_mapped_v3.json",
        BACKEND_DIR / "docs" / "final_benchmark_kenya_mapped_v2.json",
        BACKEND_DIR / "docs" / "final_benchmark_kenya.json",
    ]
    for path in candidates:
        if path.exists():
            with open(path, "r", encoding="utf-8") as handle:
                return str(path), json.load(handle)
    return None, None


def recommend_local(current_centre_id: str, speciality: str, severity: str) -> dict:
    recommender = Recommender()
    response = recommender.recommend(
        RecommandationRequest(
            patient_id="DEMO_PATIENT",
            current_centre_id=current_centre_id,
            needed_speciality=speciality,
            severity=severity,
        )
    )
    return response.model_dump()


with st.sidebar:
    auto_refresh = st.checkbox("Auto refresh", value=False)
    refresh_seconds = st.slider("Refresh interval (sec)", min_value=2, max_value=30, value=5)

    if auto_refresh:
        if st_autorefresh is not None:
            st_autorefresh(interval=refresh_seconds * 1000, key="graph_refresh")
        else:
            st.warning("Install `streamlit-autorefresh` for automatic refresh support.")

    if st.button("Refresh now"):
        st.cache_data.clear()
        st.rerun()

    st.caption("Mode offline: SQLite + Recommender local (sans API).")

try:
    centres = fetch_centres_local()
    refs = fetch_references_local()
except Exception as exc:
    st.error(f"Impossible de charger les donnees locales: {exc}")
    st.stop()

centre_ids = [c["id"] for c in centres]
levels = sorted({c["level"] for c in centres})

st.subheader("Live Graph Controls")
ctl1, ctl2, ctl3 = st.columns(3)
with ctl1:
    level_filter = st.multiselect("Levels", options=levels, default=levels)
with ctl2:
    graph_speciality_filter = st.selectbox("Graph speciality filter", options=["all", "maternal", "pediatric", "general"], index=0)
with ctl3:
    min_capacity = st.slider("Min capacity (graph)", min_value=0, max_value=max([c["capacity_available"] for c in centres] + [1]), value=0)

graph = apply_graph_filters(
    centres,
    refs,
    levels=level_filter,
    required_speciality=graph_speciality_filter,
    min_capacity=min_capacity,
)

k1, k2, k3, k4 = st.columns(4)
node_count = graph.number_of_nodes()
edge_count = graph.number_of_edges()
avg_capacity = 0.0
high_pressure = 0
if node_count > 0:
    caps = [int(attrs.get("capacity_available", 0)) for _, attrs in graph.nodes(data=True)]
    waits = [int(attrs.get("estimated_wait_minutes", 0)) for _, attrs in graph.nodes(data=True)]
    avg_capacity = sum(caps) / len(caps)
    high_pressure = sum(1 for cap, wait in zip(caps, waits) if cap <= 0 or wait / max(cap, 1) > 20)
k1.metric("Visible Centers", str(node_count))
k2.metric("Visible Links", str(edge_count))
k3.metric("Avg Capacity", f"{avg_capacity:.2f}")
k4.metric("High Pressure Nodes", str(high_pressure))

col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("Patient Input")
    current_centre = st.selectbox("Current centre", options=centre_ids)
    speciality = st.selectbox("Needed speciality", options=["maternal", "pediatric", "general"])
    severity = st.selectbox("Severity", options=["low", "medium", "high"], index=1)

    if st.button("Get Recommendation", type="primary"):
        try:
            st.session_state["recommendation"] = recommend_local(current_centre, speciality, severity)
            st.cache_data.clear()
        except Exception as exc:
            st.error(f"Erreur recommendation locale: {exc}")

    if st.button("Run Demo Scenario"):
        ok, output = run_primary_demo()
        if ok:
            st.success("Primary demo scenario executed")
            st.code(output[:2000])
        else:
            st.error(output)

    selected_node = st.selectbox("Center details", options=centre_ids)
    centre_map = {c["id"]: c for c in centres}
    st.json(centre_map[selected_node])

    demo_report = load_primary_demo_report()
    if demo_report:
        st.subheader("Demo Scenario KPIs")
        metrics = demo_report["metrics"]
        kk1, kk2, kk3 = st.columns(3)
        kk1.metric("Failure Rate", f"{metrics['failure_rate']*100:.2f}%")
        kk2.metric("Avg Wait", f"{metrics['avg_wait_minutes']:.2f} min")
        kk3.metric("Entropy Norm", f"{metrics.get('entropy_norm', metrics.get('balance_entropy', 0.0)):.4f}")
        st.json(metrics)

    st.subheader("Model Status")
    st.success("Active production candidate: ppo_referral_kenya_mapped_v3.zip")

    benchmark_path, benchmark_report = load_benchmark_report()
    if benchmark_report:
        st.subheader("Policy Comparison")
        st.caption(f"Loaded benchmark report: {benchmark_path}")
        ranking = benchmark_report.get("ranking_composite") or benchmark_report.get("ranking_reward") or []
        if ranking:
            best = ranking[0]
            st.info(
                f"Top policy: {best.get('policy', 'unknown')} | "
                f"reward={best.get('metrics', {}).get('avg_reward_per_episode', 0):.3f} | "
                f"hhi={best.get('metrics', {}).get('hhi', 0):.4f} | "
                f"entropy={best.get('metrics', {}).get('entropy_norm', 0):.4f}"
            )
        st.json(benchmark_report.get("metrics", benchmark_report))

with col_right:
    st.subheader("Referral Graph")
    rec = st.session_state.get("recommendation")
    full_path = [step["centre_id"] for step in rec.get("path", [])] if rec else []

    if rec and len(full_path) > 1:
        animate = st.checkbox("Animate selected path", value=False)
        if animate:
            step = st.slider("Path step", min_value=1, max_value=len(full_path), value=len(full_path))
            selected_path_ids = full_path[:step]
        else:
            selected_path_ids = full_path
    else:
        selected_path_ids = full_path

    render_graph(graph, selected_path=selected_path_ids)

    if rec:
        st.subheader("Recommendation")
        st.write(f"Destination: **{rec['destination_name']}** ({rec['destination_centre_id']})")
        st.write(f"Path: {' -> '.join(full_path)}")

        m1, m2, m3 = st.columns(3)
        m1.metric("Estimated Travel", f"{rec['estimated_travel_minutes']:.2f} min")
        m2.metric("Estimated Wait", f"{rec['estimated_wait_minutes']:.2f} min")
        m3.metric("Final Score", f"{rec['score']:.2f}")

        st.subheader("Rationale")
        st.info(rec.get("rationale", rec.get("explanation", "")))

        st.subheader("Score Breakdown")
        st.json(rec.get("score_breakdown", {}))
