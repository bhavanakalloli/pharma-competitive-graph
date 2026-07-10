import streamlit as st
from neo4j import GraphDatabase
import pandas as pd
from pyvis.network import Network
import streamlit.components.v1 as components

st.set_page_config(page_title="Pharma Competitive Intelligence Graph", layout="wide")

# ---------------------------
# Connection (uses Streamlit secrets)
# ---------------------------
@st.cache_resource
def get_driver():
    uri = st.secrets["NEO4J_URI"]
    user = st.secrets["NEO4J_USERNAME"]
    password = st.secrets["NEO4J_PASSWORD"]
    return GraphDatabase.driver(uri, auth=(user, password))

driver = get_driver()

def run_query(query, params=None):
    with driver.session() as session:
        result = session.run(query, params or {})
        return [record.data() for record in result]

# ---------------------------
# Sector color mapping
# ---------------------------
SECTOR_COLORS = {
    "Pharmaceuticals": "#4C9AFF",
    "Biotechnology": "#FF8B00",
}

def render_network(nodes, edges, highlight=None, height="600px"):
    net = Network(height=height, width="100%", bgcolor="#0e1117", font_color="white", directed=False)
    net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=120, spring_strength=0.04)

    highlight = highlight or set()
    added = set()
    for n in nodes:
        if n["id"] in added:
            continue
        added.add(n["id"])
        color = SECTOR_COLORS.get(n.get("sector"), "#B0B0B0")
        size = 30
        border_width = 1
        if n["id"] in highlight:
            size = 45
            border_width = 4
        net.add_node(
            n["id"],
            label=n["label"],
            color={"background": color, "border": "#FFFFFF" if n["id"] in highlight else color},
            size=size,
            borderWidth=border_width,
            font={"size": 16, "color": "white"},
        )

    for src, tgt in edges:
        if src not in added or tgt not in added:
            continue
        is_path_edge = src in highlight and tgt in highlight
        net.add_edge(
            src, tgt,
            color="#00FF9C" if is_path_edge else "#4a4a4a",
            width=4 if is_path_edge else 1,
        )

    net.set_options("""
    {
      "physics": {"stabilization": {"iterations": 150}},
      "interaction": {"hover": true, "navigationButtons": true, "zoomView": true}
    }
    """)
    html = net.generate_html()
    components.html(html, height=int(height.replace("px", "")) + 20, scrolling=False)


def get_company_info(name):
    info = run_query("""
        MATCH (c:Company {name: $name})
        OPTIONAL MATCH (c)-[:HEADQUARTERED_IN]->(country)
        OPTIONAL MATCH (c)-[:OPERATES_IN]->(sector)
        OPTIONAL MATCH (exec:Executive)-[:LEADS]->(c)
        RETURN country.name AS country, sector.name AS sector, exec.name AS ceo
    """, {"name": name})
    return info[0] if info else {"country": None, "sector": None, "ceo": None}


def get_competitors(name):
    return run_query("""
        MATCH (c:Company {name: $name})-[:COMPETES_WITH]-(competitor)
        OPTIONAL MATCH (competitor)-[:OPERATES_IN]->(s:Sector)
        RETURN competitor.name AS name, s.name AS sector
        ORDER BY name
    """, {"name": name})


def render_company_card(name):
    info = get_company_info(name)
    competitors = get_competitors(name)
    sector = info.get("sector") or "Unclassified"
    accent = SECTOR_COLORS.get(sector, "#B0B0B0")

    col1, col2 = st.columns([1, 1.3])

    with col1:
        st.markdown(f"""
        <div style="background:#1a1d23; border:1px solid #2a2d34; border-radius:12px; padding:1.25rem 1.5rem;">
          <div style="display:flex; align-items:center; gap:12px; margin-bottom:14px;">
            <div style="width:48px; height:48px; border-radius:50%; background:{accent}; display:flex; align-items:center; justify-content:center; font-weight:600; color:white; font-size:18px;">
              {name[0]}
            </div>
            <div>
              <p style="font-weight:600; font-size:17px; margin:0; color:white;">{name}</p>
              <p style="font-size:13px; margin:0; color:#9a9a9a;">{info.get('ceo') or 'Unknown CEO'}</p>
            </div>
          </div>
          <div style="display:flex; gap:8px; margin-bottom:14px;">
            <span style="background:{accent}22; color:{accent}; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:500;">{sector}</span>
            <span style="background:#2a2d3422; color:#c0c0c0; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:500; border:1px solid #3a3d44;">📍 {info.get('country') or 'Unknown'}</span>
          </div>
          <p style="font-size:13px; color:#9a9a9a; margin-bottom:8px;">Competitors ({len(competitors)})</p>
        </div>
        """, unsafe_allow_html=True)

        st.write("")
        pill_cols = st.columns(3)
        for i, comp in enumerate(competitors):
            with pill_cols[i % 3]:
                if st.button(comp["name"], key=f"pill_{name}_{comp['name']}", use_container_width=True):
                    st.session_state["selected_company"] = comp["name"]
                    st.rerun()

    with col2:
        st.markdown("**Neighborhood view:**")
        neighborhood_nodes = [{"id": name, "label": name, "sector": sector}]
        neighborhood_nodes += [{"id": c["name"], "label": c["name"], "sector": c["sector"]} for c in competitors]
        neighborhood_edges = [(name, c["name"]) for c in competitors]
        render_network(neighborhood_nodes, neighborhood_edges, highlight={name}, height="420px")


# ---------------------------
# UI
# ---------------------------
st.title("🧬 Pharma Competitive Intelligence Graph")
st.caption("A Neo4j-powered graph of pharma/biotech companies, competitors, executives, and markets — modeled after GlobalData's Companies Database.")

if "selected_company" not in st.session_state:
    st.session_state["selected_company"] = None

tab0, tab1, tab2, tab3 = st.tabs(["🌐 Full Network Map", "🔍 Company Lookup", "🏆 Most Contested Companies", "🔗 Shortest Path Finder"])

# --- TAB 0: Full Network Map ---
with tab0:
    st.subheader("The entire competitive network")

    all_countries = run_query("MATCH (c:Country) RETURN c.name AS name ORDER BY name")
    country_names = [c["name"] for c in all_countries]

    selected_countries = st.multiselect(
        "Filter by headquarters country (leave empty to show all)",
        country_names,
        default=[]
    )
    st.caption("🔵 Pharmaceuticals   🟠 Biotechnology — drag nodes, scroll to zoom, hover for details.")

    if selected_countries:
        all_companies_full = run_query("""
            MATCH (c:Company)-[:HEADQUARTERED_IN]->(country:Country)
            WHERE country.name IN $countries
            OPTIONAL MATCH (c)-[:OPERATES_IN]->(s:Sector)
            RETURN c.name AS name, s.name AS sector
        """, {"countries": selected_countries})
        allowed_names = {c["name"] for c in all_companies_full}
        all_edges = run_query("""
            MATCH (c1:Company)-[:COMPETES_WITH]-(c2:Company)
            RETURN DISTINCT c1.name AS source, c2.name AS target
        """)
        edges = [(e["source"], e["target"]) for e in all_edges
                 if e["source"] in allowed_names and e["target"] in allowed_names]
    else:
        all_companies_full = run_query("""
            MATCH (c:Company)
            OPTIONAL MATCH (c)-[:OPERATES_IN]->(s:Sector)
            RETURN c.name AS name, s.name AS sector
        """)
        all_edges = run_query("""
            MATCH (c1:Company)-[:COMPETES_WITH]-(c2:Company)
            RETURN DISTINCT c1.name AS source, c2.name AS target
        """)
        edges = [(e["source"], e["target"]) for e in all_edges]

    nodes = [{"id": c["name"], "label": c["name"], "sector": c["sector"]} for c in all_companies_full]

    if not nodes:
        st.info("No companies headquartered in the selected countries.")
    else:
        render_network(nodes, edges, height="650px")
        if selected_countries:
            st.caption(f"Showing {len(nodes)} companies headquartered in: {', '.join(selected_countries)} — including their competitor links to companies outside this filter is not shown, only connections between companies within the filtered set.")

# --- TAB 1: Company Lookup ---
with tab1:
    st.subheader("Explore a company's competitive landscape")

    all_companies = run_query("MATCH (c:Company) RETURN c.name AS name ORDER BY name")
    company_names = [c["name"] for c in all_companies]

    default_index = 0
    if st.session_state["selected_company"] in company_names:
        default_index = company_names.index(st.session_state["selected_company"])

    selected = st.selectbox("Select a company", company_names, index=default_index, key="company_select")
    st.session_state["selected_company"] = selected

    if selected:
        render_company_card(selected)

# --- TAB 2: Centrality ---
with tab2:
    st.subheader("Which companies are most contested in the market?")
    st.caption("Ranked by number of competitor connections (degree centrality). Click a company to see its network below.")

    centrality = run_query("""
        MATCH (c:Company)-[r:COMPETES_WITH]-()
        RETURN c.name AS Company, count(r) AS CompetitorCount
        ORDER BY CompetitorCount DESC
    """)
    max_count = max((row["CompetitorCount"] for row in centrality), default=1)

    clicked_company = None
    for row in centrality:
        bar_pct = int((row["CompetitorCount"] / max_count) * 100)
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(f"{row['Company']}", key=f"rank_{row['Company']}", use_container_width=True):
                clicked_company = row["Company"]
            st.markdown(f"""
            <div style="background:#2a2d34; border-radius:6px; height:8px; margin:-8px 0 12px 0;">
              <div style="background:#4C9AFF; width:{bar_pct}%; height:8px; border-radius:6px;"></div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"<p style='margin-top:6px; color:#9a9a9a;'>{row['CompetitorCount']} competitors</p>", unsafe_allow_html=True)

    if clicked_company:
        st.session_state["centrality_selected"] = clicked_company

    if st.session_state.get("centrality_selected"):
        st.divider()
        st.markdown(f"### {st.session_state['centrality_selected']}'s network")
        sel = st.session_state["centrality_selected"]
        info = get_company_info(sel)
        competitors = get_competitors(sel)
        nodes = [{"id": sel, "label": sel, "sector": info.get("sector")}]
        nodes += [{"id": c["name"], "label": c["name"], "sector": c["sector"]} for c in competitors]
        edges = [(sel, c["name"]) for c in competitors]
        render_network(nodes, edges, highlight={sel}, height="420px")

# --- TAB 3: Shortest Path ---
with tab3:
    st.subheader("Find the indirect connection between two companies")

    all_companies = run_query("MATCH (c:Company) RETURN c.name AS name ORDER BY name")
    company_names = [c["name"] for c in all_companies]

    col1, col2 = st.columns(2)
    with col1:
        company_a = st.selectbox("From company", company_names, key="a")
    with col2:
        company_b = st.selectbox("To company", company_names, index=1, key="b")

    if st.button("Find shortest path"):
        path_result = run_query("""
            MATCH path = shortestPath(
                (a:Company {name: $a})-[:COMPETES_WITH*1..6]-(b:Company {name: $b})
            )
            RETURN [n IN nodes(path) | n.name] AS pathNames
        """, {"a": company_a, "b": company_b})

        if path_result and path_result[0]["pathNames"]:
            path_names = path_result[0]["pathNames"]
            st.success(" → ".join(path_names))
            st.caption(f"{len(path_names) - 1} hop(s) between {company_a} and {company_b}")

            path_edges_query = run_query("""
                MATCH (c:Company)-[:COMPETES_WITH]-(neighbor)
                WHERE c.name IN $path_names
                RETURN c.name AS source, neighbor.name AS target
            """, {"path_names": path_names})

            all_sectors = run_query("""
                MATCH (c:Company)-[:OPERATES_IN]->(s:Sector)
                RETURN c.name AS name, s.name AS sector
            """)
            sector_lookup = {row["name"]: row["sector"] for row in all_sectors}

            node_ids = set(path_names)
            edges = []
            for row in path_edges_query:
                node_ids.add(row["source"])
                node_ids.add(row["target"])
                edges.append((row["source"], row["target"]))

            nodes = [{"id": nid, "label": nid, "sector": sector_lookup.get(nid)} for nid in node_ids]

            st.markdown("**Path visualization** (highlighted = the shortest path found):")
            render_network(nodes, edges, highlight=set(path_names), height="450px")
        else:
            st.warning(f"No connection found between {company_a} and {company_b} — they sit in disconnected competitive clusters.")

st.divider()
st.caption("Built with Neo4j + Streamlit — a small-scale demo of graph-based competitive intelligence, inspired by GlobalData's Companies & Competitive Intelligence products.")
