# Pharma Competitive Intelligence Graph

A graph-based competitive intelligence tool built with **Neo4j** and **Streamlit**, modeling relationships between pharmaceutical and biotech companies — competitors, executives, sectors, and markets.

This project was built as a demonstration of graph database concepts applied to a real-world use case: **competitive intelligence**, similar to products like GlobalData's Companies Database and Competitive Intelligence platform.

🔗 **Live app:** https://pharma-competitive-graph.streamlit.app/

---

## What it does

### 🌐 Full Network Map
An interactive, force-directed graph of all 20+ companies and every competitor relationship between them — draggable, zoomable, color-coded by sector (blue = Pharmaceuticals, orange = Biotechnology). Includes a **country filter**, so you can isolate competitive relationships within or across specific headquarters countries (e.g. "only show US companies" or compare regional clusters).

### 🔍 Company Lookup
A full profile card for any company: CEO, sector, headquarters country, and a list of competitors shown as clickable pills. Clicking a competitor's pill jumps straight to their profile — letting you "walk" the competitive graph by clicking through it, rather than searching each company manually. A mini network view alongside the card shows that company's direct neighborhood visually.

### 🏆 Most Contested Companies
Ranks every company by **degree centrality** — the number of competitor connections it has — as a proxy for how central it is to the overall competitive landscape. Each row is clickable: selecting a company instantly renders its network graph below the ranking, connecting the numeric insight directly to the visual structure.

### 🔗 Shortest Path Finder
Pick any two companies and find the shortest chain of competitor relationships connecting them — even if they're not direct competitors. Results are shown two ways:
- The **full network graph**, with the discovered path highlighted in green against the rest of the graph
- An **animated step-by-step reveal** below it: each company in the path fades in one at a time, with connecting lines drawing themselves in sequence, finishing with a plain-English explanation of how (or whether) the two companies are connected

If no path exists, the app explains that the two companies sit in disconnected parts of the competitive landscape — itself a meaningful finding (e.g. Western pharma majors vs. the Japanese pharma cluster in this dataset don't share any competitor links).

## Why a graph database

Competitive intelligence data is inherently relational — companies compete with, are owned by, and are led by other entities, and those relationships form a network rather than a flat table. Neo4j's graph model makes traversal queries (e.g. "how are these two companies connected?") and network analysis (e.g. "which company is most central?") natural and efficient, compared to modeling the same relationships in a relational database.

## Data model

**Nodes:**
- `Company` — pharma/biotech companies
- `Executive` — CEOs
- `Sector` — industry sector (Pharmaceuticals, Biotechnology)
- `Country` — headquarters location

**Relationships:**
- `(:Company)-[:COMPETES_WITH]-(:Company)`
- `(:Executive)-[:LEADS]->(:Company)`
- `(:Company)-[:OPERATES_IN]->(:Sector)`
- `(:Company)-[:HEADQUARTERED_IN]->(:Country)`
- `(:Company)-[:OWNS]->(:Company)` (parent/subsidiary, where applicable)

Note: some companies (e.g. those only ever referenced as someone else's competitor, like Novavax or CureVac) exist as `Company` nodes without a `Sector`, `Country`, or `Executive` attached — the app handles this gracefully, rendering them as unclassified/gray nodes in the network views.

## Tech stack

- **Neo4j AuraDB** (free tier) — graph database
- **Cypher** — query language for data loading and graph traversal
- **Python** — application logic
- **Streamlit** — interactive web app framework
- **pyvis** — interactive network graph rendering (draggable, zoomable, physics-based layout)
- **Streamlit Community Cloud** — hosting/deployment

## Example queries

Find a company's competitive landscape:
```cypher
MATCH (c:Company {name: 'Pfizer'})-[:COMPETES_WITH]-(competitor)
RETURN c, competitor
```

Rank companies by competitor count (degree centrality):
```cypher
MATCH (c:Company)-[r:COMPETES_WITH]-()
RETURN c.name AS company, count(r) AS competitorCount
ORDER BY competitorCount DESC
```

Find the shortest path between two companies:
```cypher
MATCH path = shortestPath(
  (a:Company {name: 'BioNTech'})-[:COMPETES_WITH*1..6]-(b:Company {name: 'AstraZeneca'})
)
RETURN path
```

Filter the network by headquarters country:
```cypher
MATCH (c:Company)-[:HEADQUARTERED_IN]->(country:Country)
WHERE country.name IN ['USA', 'Japan']
OPTIONAL MATCH (c)-[:OPERATES_IN]->(s:Sector)
RETURN c.name AS name, s.name AS sector
```

## Running locally

```bash
pip install -r requirements.txt
```

Create a `.streamlit/secrets.toml` file with your own Neo4j Aura credentials:
```toml
NEO4J_URI = "neo4j+s://your-instance-id.databases.neo4j.io"
NEO4J_USERNAME = "your-username"
NEO4J_PASSWORD = "your-password"
```

Then run:
```bash
streamlit run app.py
```

## Data loading

The `load_graph.cypher` script loads `companies.csv` into Neo4j, creating all nodes and relationships. Run each block in the Neo4j Query console against your own Aura instance.

## Future extensions

- Expand dataset to more sectors covered by GlobalData (technology, consumer, energy)
- Add `DEALS` relationships to model M&A activity
- Add `Patent` nodes for an innovation/IP intelligence layer
- Integrate Neo4j Graph Data Science (PageRank, community detection) for deeper network analysis on larger datasets
- Add a side-by-side company comparison view
