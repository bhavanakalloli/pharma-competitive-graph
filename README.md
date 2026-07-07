# Pharma Competitive Intelligence Graph

A graph-based competitive intelligence tool built with **Neo4j** and **Streamlit**, modeling relationships between pharmaceutical and biotech companies — competitors, executives, sectors, and markets.

This project was built as a demonstration of graph database concepts applied to a real-world use case: **competitive intelligence**, similar to products like GlobalData's Companies Database and Competitive Intelligence platform.

🔗 **Live app:** https://pharma-competitive-graph.streamlit.app/

---

## What it does

- **Company Lookup** — search any of 20 major pharma/biotech companies to see their CEO, sector, headquarters, and full list of competitors
- **Most Contested Companies** — ranks companies by degree centrality (number of competitor connections), surfacing which companies are most central to the competitive landscape
- **Shortest Path Finder** — finds indirect connections between any two companies, even when they're not direct competitors, by traversing the competitor graph

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

## Tech stack

- **Neo4j AuraDB** (free tier) — graph database
- **Cypher** — query language for data loading and graph traversal
- **Python** — application logic
- **Streamlit** — interactive web app framework
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

- Expand dataset to more sectors.
- Add `DEALS` relationships to model M&A activity
- Add `Patent` nodes for an innovation/IP intelligence layer
- Integrate Neo4j Graph Data Science (PageRank, community detection) for deeper network analysis
