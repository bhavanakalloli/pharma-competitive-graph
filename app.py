import streamlit as st
from neo4j import GraphDatabase
import pandas as pd

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
# UI
# ---------------------------
st.title("🧬 Pharma Competitive Intelligence Graph")
st.caption("A Neo4j-powered graph of pharma/biotech companies, competitors, executives, and markets — modeled after GlobalData's Companies Database.")

tab1, tab2, tab3 = st.tabs(["🔍 Company Lookup", "🏆 Most Contested Companies", "🔗 Shortest Path Finder"])

# --- TAB 1: Company Lookup ---
with tab1:
    st.subheader("Explore a company's competitive landscape")

    all_companies = run_query("MATCH (c:Company) RETURN c.name AS name ORDER BY name")
    company_names = [c["name"] for c in all_companies]

    selected = st.selectbox("Select a company", company_names)

    if selected:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"### {selected}")
            info = run_query("""
                MATCH (c:Company {name: $name})
                OPTIONAL MATCH (c)-[:HEADQUARTERED_IN]->(country)
                OPTIONAL MATCH (c)-[:OPERATES_IN]->(sector)
                OPTIONAL MATCH (exec:Executive)-[:LEADS]->(c)
                RETURN country.name AS country, sector.name AS sector, exec.name AS ceo
            """, {"name": selected})
            if info:
                st.write(f"**CEO:** {info[0]['ceo']}")
                st.write(f"**Sector:** {info[0]['sector']}")
                st.write(f"**Headquartered in:** {info[0]['country']}")

        with col2:
            competitors = run_query("""
                MATCH (c:Company {name: $name})-[:COMPETES_WITH]-(competitor)
                RETURN competitor.name AS name
                ORDER BY name
            """, {"name": selected})
            st.markdown(f"**Competitors ({len(competitors)}):**")
            for comp in competitors:
                st.write(f"- {comp['name']}")

# --- TAB 2: Centrality ---
with tab2:
    st.subheader("Which companies are most contested in the market?")
    st.caption("Ranked by number of competitor connections (degree centrality) — a proxy for how competitively central a company is.")

    centrality = run_query("""
        MATCH (c:Company)-[r:COMPETES_WITH]-()
        RETURN c.name AS Company, count(r) AS CompetitorCount
        ORDER BY CompetitorCount DESC
    """)
    df = pd.DataFrame(centrality)
    st.bar_chart(df.set_index("Company"))
    st.dataframe(df, use_container_width=True)

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
        else:
            st.warning(f"No connection found between {company_a} and {company_b} — they sit in disconnected competitive clusters.")

st.divider()
st.caption("Built with Neo4j + Streamlit — a small-scale demo of graph-based competitive intelligence, inspired by GlobalData's Companies & Competitive Intelligence products.")
