"""
Neo4j Knowledge Graph service.
Manages nodes and relationships for the Digital Brain.

Nodes:  User, Memory, Topic, Interview, Audience, ContentStyle, Platform
Edges:  HAS_MEMORY, ABOUT_TOPIC, SUPPORTS, CONTRADICTS,
        ILLUSTRATES, EVOLVED_FROM, EXPERT_IN, CURIOUS_ABOUT, PRODUCED,
        SPECIALIZES_IN, OPERATES_IN, SPEAKS_TO, WRITES_IN, CONDUCTED, RELATED_TO,
        FOCUSES_ON, PUBLISHES_ON
"""

import logging
from neo4j import GraphDatabase
from app.core.config import settings

logger = logging.getLogger(__name__)

# Module-level singleton driver. Reused across every Neo4j call for the
# lifetime of the worker process. Avoids the ~1.1s TCP+TLS handshake that
# previously happened on every operation. Internal connection pool keeps
# up to 20 sessions warm. Closed cleanly via close_driver() in app shutdown.
_driver = None


def _get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
            max_connection_lifetime=300,    # recycle conns every 5min
            max_connection_pool_size=20,    # plenty for 5-50 concurrent users
            connection_acquisition_timeout=30,
        )
    return _driver


def close_driver():
    """Call from FastAPI lifespan shutdown so connections close cleanly."""
    global _driver
    if _driver is not None:
        try:
            _driver.close()
        except Exception as exc:
            logger.warning("Neo4j driver close failed: %s", exc)
        _driver = None


def _relation_label(relation: str) -> str:
    mapping = {
        "HAS_MEMORY": "Has Memory",
        "ABOUT_TOPIC": "About Topic",
        "PRODUCED": "Produced",
        "SUPPORTS": "Supports",
        "CONTRADICTS": "Contradicts",
        "ILLUSTRATES": "Illustrates",
        "EVOLVED_FROM": "Evolved From",
        "SPECIALIZES_IN": "Specializes In",
        "OPERATES_IN": "Operates In",
        "SPEAKS_TO": "Speaks To",
        "WRITES_IN": "Writes In",
        "FOCUSES_ON": "Focuses On",
        "PUBLISHES_ON": "Publishes On",
        "RELATED_TO": "Related To",
        "EXPERT_IN": "Expert In",
        "KNOWS_ABOUT": "Knows About",
        "CURIOUS_ABOUT": "Curious About",
        "CONDUCTED": "Conducted",
    }
    return mapping.get(relation, relation.replace("_", " ").title())


# ==============================================================================
# CONSTRAINTS â€” run once at startup to ensure uniqueness
# ==============================================================================
def init_constraints():
    driver = _get_driver()
    with driver.session() as s:
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE")
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (m:Memory) REQUIRE m.neon_id IS UNIQUE")
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (t:Topic) REQUIRE (t.user_id, t.name) IS UNIQUE")
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (i:Interview) REQUIRE i.interview_id IS UNIQUE")
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (a:Audience) REQUIRE (a.user_id, a.name) IS UNIQUE")
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:ContentStyle) REQUIRE (c.user_id, c.name) IS UNIQUE")
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Platform) REQUIRE (p.user_id, p.name) IS UNIQUE")


# ==============================================================================
# USER NODE
# ==============================================================================
def ensure_user_node(user_id: str):
    driver = _get_driver()
    with driver.session() as s:
        s.run(
            "MERGE (u:User {user_id: $user_id})",
            user_id=user_id,
        )


def sync_onboarding_to_neo4j(
    user_id: str,
    niche: str | None,
    industry: str | None,
    content_tone: str | None,
    target_audience: str | None,
    display_name: str | None = None,
    bio: str | None = None,
    icp: str | None = None,
    offer: str | None = None,
    pain_solved: str | None = None,
    differentiator: str | None = None,
    primary_goal: str | None = None,
    key_themes: list[str] | None = None,
    platforms: list[str] | None = None,
):
    """
    Called after onboarding is saved to Neon.
    Syncs profile data into Neo4j so the KG has context from day 1,
    even before the first interview.

    Creates:
      - User node with profile properties
      - Topic(niche)       â†’ SPECIALIZES_IN
      - Topic(industry)    â†’ OPERATES_IN
      - Audience node      â†’ SPEAKS_TO
      - ContentStyle node  â†’ WRITES_IN
      - Topic(niche) â†” Topic(industry) â†’ RELATED_TO
    """
    driver = _get_driver()
    with driver.session() as s:
        # Update User node with profile properties
        s.run(
            """
            MERGE (u:User {user_id: $user_id})
            SET u.niche = $niche,
                u.industry = $industry,
                u.content_tone = $content_tone,
                u.target_audience = $target_audience,
                u.display_name = $display_name,
                u.bio = $bio,
                u.icp = $icp,
                u.offer = $offer,
                u.pain_solved = $pain_solved,
                u.differentiator = $differentiator,
                u.primary_goal = $primary_goal,
                u.key_themes = $key_themes,
                u.platforms = $platforms
            """,
            user_id=user_id,
            niche=niche or "",
            industry=industry or "",
            content_tone=content_tone or "",
            target_audience=target_audience or "",
            display_name=display_name or "You",
            bio=bio or "",
            icp=icp or "",
            offer=offer or "",
            pain_solved=pain_solved or "",
            differentiator=differentiator or "",
            primary_goal=primary_goal or "",
            key_themes=[v for v in (key_themes or []) if v],
            platforms=[v for v in (platforms or []) if v],
        )

        # Niche â†’ SPECIALIZES_IN (user's declared domain of expertise)
        if niche:
            s.run(
                """
                MERGE (u:User {user_id: $user_id})
                MERGE (t:Topic {user_id: $user_id, name: $name})
                SET t.category = 'Niche', t.depth = 'deep'
                MERGE (u)-[:SPECIALIZES_IN]->(t)
                """,
                user_id=user_id,
                name=niche,
            )

        # Industry â†’ OPERATES_IN (the market/sector they work in)
        if industry and industry != niche:
            s.run(
                """
                MERGE (u:User {user_id: $user_id})
                MERGE (t:Topic {user_id: $user_id, name: $name})
                SET t.category = 'Industry', t.depth = 'deep'
                MERGE (u)-[:OPERATES_IN]->(t)
                """,
                user_id=user_id,
                name=industry,
            )

        # Target audience â†’ SPEAKS_TO (who the content is for)
        if target_audience:
            s.run(
                """
                MERGE (u:User {user_id: $user_id})
                MERGE (a:Audience {user_id: $user_id, name: $name})
                MERGE (u)-[:SPEAKS_TO]->(a)
                """,
                user_id=user_id,
                name=target_audience,
            )

        # Content tone â†’ WRITES_IN (how the content sounds)
        if content_tone:
            s.run(
                """
                MERGE (u:User {user_id: $user_id})
                MERGE (c:ContentStyle {user_id: $user_id, name: $name})
                MERGE (u)-[:WRITES_IN]->(c)
                """,
                user_id=user_id,
                name=content_tone,
            )

        # Link niche and industry topics as related (if both exist)
        if niche and industry and niche != industry:
            s.run(
                """
                MATCH (t1:Topic {user_id: $user_id, name: $niche})
                MATCH (t2:Topic {user_id: $user_id, name: $industry})
                MERGE (t1)-[:RELATED_TO]->(t2)
                """,
                user_id=user_id,
                niche=niche,
                industry=industry,
            )

        for theme in [value for value in (key_themes or []) if value]:
            s.run(
                """
                MERGE (u:User {user_id: $user_id})
                MERGE (t:Topic {user_id: $user_id, name: $theme})
                ON CREATE SET t.category = 'Theme'
                MERGE (u)-[:FOCUSES_ON]->(t)
                """,
                user_id=user_id,
                theme=theme,
            )

        for platform in [value for value in (platforms or []) if value]:
            s.run(
                """
                MERGE (u:User {user_id: $user_id})
                MERGE (p:Platform {user_id: $user_id, name: $platform})
                MERGE (u)-[:PUBLISHES_ON]->(p)
                """,
                user_id=user_id,
                platform=platform,
            )



# ==============================================================================
# INTERVIEW NODE
# ==============================================================================
def create_interview_node(interview_id: str, user_id: str, topic: str):
    driver = _get_driver()
    with driver.session() as s:
        s.run(
            """
            MERGE (i:Interview {interview_id: $interview_id})
            SET i.topic = $topic
            WITH i
            MATCH (u:User {user_id: $user_id})
            MERGE (u)-[:CONDUCTED]->(i)
            """,
            interview_id=interview_id,
            user_id=user_id,
            topic=topic,
        )


def delete_interview_node(interview_id: str, user_id: str):
    """
    Hard-delete an Interview node and any memories produced ONLY by this
    interview. Topics that were touched by other interviews are kept.

    Cypher: DETACH DELETE removes node + all incident edges atomically.
    Memories that have no other relationships beyond this interview also
    get cleaned (orphan cleanup). Topic nodes are left alone — they may
    be referenced by other memories.
    """
    driver = _get_driver()
    with driver.session() as s:
        # Drop memories produced only by this interview, then the interview itself.
        s.run(
            """
            MATCH (u:User {user_id: $user_id})-[:CONDUCTED]->(i:Interview {interview_id: $interview_id})
            OPTIONAL MATCH (i)-[:PRODUCED]->(m:Memory)
            WHERE NOT EXISTS {
                MATCH (otherI:Interview)-[:PRODUCED]->(m)
                WHERE otherI.interview_id <> $interview_id
            }
            DETACH DELETE m
            """,
            interview_id=interview_id,
            user_id=user_id,
        )
        s.run(
            """
            MATCH (u:User {user_id: $user_id})-[:CONDUCTED]->(i:Interview {interview_id: $interview_id})
            DETACH DELETE i
            """,
            interview_id=interview_id,
            user_id=user_id,
        )


# ==============================================================================
# MEMORY NODE + HAS_MEMORY edge
# ==============================================================================
def create_memory_node(
    neon_id: str,
    user_id: str,
    memory_type: str,
    content: str,
    trust_tier: str,
    interview_id: str | None = None,
):
    driver = _get_driver()
    with driver.session() as s:
        s.run(
            """
            MERGE (m:Memory {neon_id: $neon_id})
            SET m.type = $memory_type,
                m.content = $content,
                m.trust_tier = $trust_tier
            WITH m
            MATCH (u:User {user_id: $user_id})
            MERGE (u)-[:HAS_MEMORY]->(m)
            """,
            neon_id=neon_id,
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            trust_tier=trust_tier,
        )
        # Link to interview if provided
        if interview_id:
            s.run(
                """
                MATCH (i:Interview {interview_id: $interview_id})
                MATCH (m:Memory {neon_id: $neon_id})
                MERGE (i)-[:PRODUCED]->(m)
                """,
                interview_id=interview_id,
                neon_id=neon_id,
            )


def update_memory_node(neon_id: str, *, content: str | None = None,
                       trust_tier: str | None = None) -> None:
    """Patch the matching Memory node to keep Neo4j in sync with Postgres edits."""
    sets = []
    params: dict = {"neon_id": neon_id}
    if content is not None:
        sets.append("m.content = $content")
        params["content"] = content
    if trust_tier is not None:
        sets.append("m.trust_tier = $trust_tier")
        params["trust_tier"] = trust_tier
    if not sets:
        return
    cypher = f"MATCH (m:Memory {{neon_id: $neon_id}}) SET {', '.join(sets)}"
    driver = _get_driver()
    with driver.session() as s:
        s.run(cypher, **params)


def delete_memory_node(neon_id: str) -> None:
    """
    Remove a Memory node and all its incident edges from the graph.
    Idempotent: silent if the node doesn't exist.
    """
    driver = _get_driver()
    with driver.session() as s:
        s.run(
            "MATCH (m:Memory {neon_id: $neon_id}) DETACH DELETE m",
            neon_id=neon_id,
        )


# ==============================================================================
# TOPIC NODE + ABOUT_TOPIC edge from memory
# ==============================================================================
def link_memory_to_topic(neon_id: str, user_id: str, topic_name: str, category: str):
    driver = _get_driver()
    with driver.session() as s:
        s.run(
            """
            MERGE (t:Topic {user_id: $user_id, name: $topic_name})
            SET t.category = $category
            WITH t
            MATCH (m:Memory {neon_id: $neon_id})
            MERGE (m)-[:ABOUT_TOPIC]->(t)
            """,
            user_id=user_id,
            topic_name=topic_name,
            category=category,
            neon_id=neon_id,
        )


# ==============================================================================
# MEMORY â†’ MEMORY relationships
# ==============================================================================
def link_memories(from_neon_id: str, to_neon_id: str, rel_type: str):
    """
    rel_type: SUPPORTS | CONTRADICTS | ILLUSTRATES | EVOLVED_FROM
    """
    allowed = {"SUPPORTS", "CONTRADICTS", "ILLUSTRATES", "EVOLVED_FROM"}
    if rel_type not in allowed:
        raise ValueError(f"Invalid relationship type: {rel_type}")

    driver = _get_driver()
    with driver.session() as s:
        s.run(
            f"""
            MATCH (a:Memory {{neon_id: $from_id}})
            MATCH (b:Memory {{neon_id: $to_id}})
            MERGE (a)-[:{rel_type}]->(b)
            """,
            from_id=from_neon_id,
            to_id=to_neon_id,
        )


# ==============================================================================
# USER â†’ TOPIC expertise edges (auto-updated based on times_discussed)
# ==============================================================================
def update_user_topic_expertise(user_id: str, topic_name: str, times_discussed: int):
    """
    Updates User â†’ Topic relationship based on how many times topic was discussed.
    < 2  interviews: CURIOUS_ABOUT (exploring)
    2-3  interviews: KNOWS_ABOUT   (familiar)
    4+   interviews: EXPERT_IN     (deep expertise, earned through interviews)
    """
    driver = _get_driver()
    with driver.session() as s:
        # Remove old expertise edges for this topic first
        s.run(
            """
            MATCH (u:User {user_id: $user_id})-[r:EXPERT_IN|KNOWS_ABOUT|CURIOUS_ABOUT]->(t:Topic {user_id: $user_id, name: $topic_name})
            DELETE r
            """,
            user_id=user_id,
            topic_name=topic_name,
        )
        if times_discussed >= 4:
            rel = "EXPERT_IN"
        elif times_discussed >= 2:
            rel = "KNOWS_ABOUT"
        else:
            rel = "CURIOUS_ABOUT"
        s.run(
            f"""
            MATCH (u:User {{user_id: $user_id}})
            MATCH (t:Topic {{user_id: $user_id, name: $topic_name}})
            MERGE (u)-[:{rel}]->(t)
            """,
            user_id=user_id,
            topic_name=topic_name,
        )


# ==============================================================================
# QUERY â€” get related memory neon_ids for a topic (for memory pack)
# ==============================================================================
def get_memory_ids_for_topic(user_id: str, topic_name: str, limit: int = 15) -> list[str]:
    driver = _get_driver()
    results = []
    with driver.session() as s:
        # Direct topic memories + memories that SUPPORT or ILLUSTRATE them
        records = s.run(
            """
            MATCH (u:User {user_id: $user_id})-[:HAS_MEMORY]->(m:Memory)
            OPTIONAL MATCH (m)-[:ABOUT_TOPIC]->(t:Topic {name: $topic_name})
            OPTIONAL MATCH (m2:Memory)-[:SUPPORTS|ILLUSTRATES]->(m)
            WITH m, t, m2
            WHERE t IS NOT NULL OR m2 IS NOT NULL
            RETURN DISTINCT m.neon_id AS neon_id
            LIMIT $limit
            """,
            user_id=user_id,
            topic_name=topic_name,
            limit=limit,
        )
        results = [r["neon_id"] for r in records]
    return results


# ==============================================================================
# QUERY â€” check if two memories contradict (for evolution detection)
# ==============================================================================
def memories_contradict(neon_id_a: str, neon_id_b: str) -> bool:
    driver = _get_driver()
    result = False
    with driver.session() as s:
        record = s.run(
            """
            MATCH (a:Memory {neon_id: $a})-[:CONTRADICTS]-(b:Memory {neon_id: $b})
            RETURN count(*) AS cnt
            """,
            a=neon_id_a,
            b=neon_id_b,
        ).single()
        result = record["cnt"] > 0 if record else False
    return result


# ==============================================================================
# QUERY â€” full user knowledge graph for visualization
# ==============================================================================
def get_user_graph(user_id: str) -> dict:
    """
    Returns the user's full knowledge subgraph for the Digital Brain visualizer.
    Nodes: User, Memory, Topic, Interview, Audience, ContentStyle, Platform
    Links: HAS_MEMORY, ABOUT_TOPIC, PRODUCED, SUPPORTS, CONTRADICTS, ILLUSTRATES,
           EVOLVED_FROM, SPECIALIZES_IN, OPERATES_IN, SPEAKS_TO, WRITES_IN,
           FOCUSES_ON, PUBLISHES_ON, RELATED_TO, EXPERT_IN, KNOWS_ABOUT, CURIOUS_ABOUT
    """
    driver = _get_driver()
    nodes: dict[str, dict] = {}
    links: list[dict] = []
    seen_links: set[tuple[str, str, str]] = set()

    with driver.session() as s:
        # User node (anchor for onboarding-only graphs)
        for r in s.run(
            """
            MATCH (u:User {user_id: $uid})
            RETURN u.user_id AS id, u.niche AS niche, u.industry AS industry,
                   u.target_audience AS target_audience, u.content_tone AS content_tone,
                   u.display_name AS display_name
            """,
            uid=user_id,
        ):
            uid = "user:" + r["id"]
            display_name = (r["display_name"] or "").strip() or "You"
            nodes[uid] = {
                "id": uid,
                "type": "user",
                "node_kind": "user",
                "label": display_name,
                "display_name": display_name,
                "niche": r["niche"] or "",
                "industry": r["industry"] or "",
                "target_audience": r["target_audience"] or "",
                "content_tone": r["content_tone"] or "",
            }

        # Memory nodes
        for r in s.run(
            """
            MATCH (u:User {user_id: $uid})-[:HAS_MEMORY]->(m:Memory)
            RETURN m.neon_id AS id, m.type AS mem_type,
                   m.content AS content, m.trust_tier AS trust_tier
            """,
            uid=user_id,
        ):
            nid = r["id"]
            content = r["content"] or ""
            nodes[nid] = {
                "id": nid,
                "type": "memory",
                "node_kind": "memory",
                "memory_type": r["mem_type"] or "opinion",
                "trust_tier": r["trust_tier"] or "B",
                "label": content[:50] + ("â€¦" if len(content) > 50 else ""),
                "display_name": content[:50] + ("..." if len(content) > 50 else ""),
                "content": content,
            }

        # Topic nodes + ABOUT_TOPIC links
        for r in s.run(
            """
            MATCH (u:User {user_id: $uid})-[:HAS_MEMORY]->(m:Memory)-[:ABOUT_TOPIC]->(t:Topic)
            RETURN m.neon_id AS mem_id, t.name AS topic_name,
                   t.category AS category, t.depth AS depth
            """,
            uid=user_id,
        ):
            tid = "topic:" + r["topic_name"]
            if tid not in nodes:
                nodes[tid] = {
                    "id": tid,
                    "type": "topic",
                    "node_kind": "topic",
                    "label": r["topic_name"],
                    "display_name": r["topic_name"],
                    "category": r["category"] or "Other",
                    "depth": r["depth"] or "surface",
                }
            if r["mem_id"] in nodes:
                key = (r["mem_id"], tid, "ABOUT_TOPIC")
                if key not in seen_links:
                    seen_links.add(key)
                    links.append({"source": r["mem_id"], "target": tid, "relation": "ABOUT_TOPIC"})

        # User onboarding/expertise edges to Topic
        for r in s.run(
            """
            MATCH (u:User {user_id: $uid})-[rel]->(t:Topic)
            WHERE type(rel) IN ['SPECIALIZES_IN', 'OPERATES_IN', 'FOCUSES_ON', 'EXPERT_IN', 'KNOWS_ABOUT', 'CURIOUS_ABOUT']
            RETURN t.name AS topic_name, t.category AS category, t.depth AS depth, type(rel) AS rel_type
            """,
            uid=user_id,
        ):
            tid = "topic:" + r["topic_name"]
            if tid not in nodes:
                nodes[tid] = {
                    "id": tid,
                    "type": "topic",
                    "node_kind": "topic",
                    "label": r["topic_name"],
                    "display_name": r["topic_name"],
                    "category": r["category"] or "Other",
                    "depth": r["depth"] or "surface",
                }
            user_node_id = "user:" + user_id
            if user_node_id in nodes:
                rel_type = r["rel_type"]
                key = (user_node_id, tid, rel_type)
                if key not in seen_links:
                    seen_links.add(key)
                    links.append({"source": user_node_id, "target": tid, "relation": rel_type})

        # Audience onboarding nodes
        for r in s.run(
            """
            MATCH (u:User {user_id: $uid})-[rel]->(a:Audience)
            WHERE type(rel) = 'SPEAKS_TO'
            RETURN a.name AS audience_name
            """,
            uid=user_id,
        ):
            aid = "audience:" + r["audience_name"]
            if aid not in nodes:
                nodes[aid] = {
                    "id": aid,
                    "type": "audience",
                    "node_kind": "audience",
                    "label": r["audience_name"],
                    "display_name": r["audience_name"],
                }
            user_node_id = "user:" + user_id
            if user_node_id in nodes:
                key = (user_node_id, aid, "SPEAKS_TO")
                if key not in seen_links:
                    seen_links.add(key)
                    links.append({"source": user_node_id, "target": aid, "relation": "SPEAKS_TO"})

        # Content style onboarding nodes
        for r in s.run(
            """
            MATCH (u:User {user_id: $uid})-[rel]->(c:ContentStyle)
            WHERE type(rel) = 'WRITES_IN'
            RETURN c.name AS style_name
            """,
            uid=user_id,
        ):
            cid = "content_style:" + r["style_name"]
            if cid not in nodes:
                nodes[cid] = {
                    "id": cid,
                    "type": "content_style",
                    "node_kind": "content_style",
                    "label": r["style_name"],
                    "display_name": r["style_name"],
                }
            user_node_id = "user:" + user_id
            if user_node_id in nodes:
                key = (user_node_id, cid, "WRITES_IN")
                if key not in seen_links:
                    seen_links.add(key)
                    links.append({"source": user_node_id, "target": cid, "relation": "WRITES_IN"})

        # Platform onboarding nodes
        for r in s.run(
            """
            MATCH (u:User {user_id: $uid})-[rel]->(p:Platform)
            WHERE type(rel) = 'PUBLISHES_ON'
            RETURN p.name AS platform_name
            """,
            uid=user_id,
        ):
            pid = "platform:" + r["platform_name"]
            if pid not in nodes:
                nodes[pid] = {
                    "id": pid,
                    "type": "platform",
                    "node_kind": "platform",
                    "label": r["platform_name"],
                    "display_name": r["platform_name"],
                }
            user_node_id = "user:" + user_id
            if user_node_id in nodes:
                key = (user_node_id, pid, "PUBLISHES_ON")
                if key not in seen_links:
                    seen_links.add(key)
                    links.append({"source": user_node_id, "target": pid, "relation": "PUBLISHES_ON"})

        # Topic-to-topic links from onboarding context
        for r in s.run(
            """
            MATCH (t1:Topic {user_id: $uid})-[rel:RELATED_TO]->(t2:Topic {user_id: $uid})
            RETURN t1.name AS from_topic, t2.name AS to_topic, type(rel) AS rel_type
            """,
            uid=user_id,
        ):
            from_tid = "topic:" + r["from_topic"]
            to_tid = "topic:" + r["to_topic"]
            if from_tid not in nodes:
                nodes[from_tid] = {
                    "id": from_tid,
                    "type": "topic",
                    "node_kind": "topic",
                    "label": r["from_topic"],
                    "display_name": r["from_topic"],
                    "category": "Other",
                    "depth": "surface",
                }
            if to_tid not in nodes:
                nodes[to_tid] = {
                    "id": to_tid,
                    "type": "topic",
                    "node_kind": "topic",
                    "label": r["to_topic"],
                    "display_name": r["to_topic"],
                    "category": "Other",
                    "depth": "surface",
                }
            rel_type = r["rel_type"]
            key = (from_tid, to_tid, rel_type)
            if key not in seen_links:
                seen_links.add(key)
                links.append({"source": from_tid, "target": to_tid, "relation": rel_type})

        # Interview nodes + PRODUCED links
        for r in s.run(
            """
            MATCH (u:User {user_id: $uid})-[:CONDUCTED]->(i:Interview)-[:PRODUCED]->(m:Memory)
            RETURN i.interview_id AS iid, i.topic AS itopic, m.neon_id AS mem_id
            """,
            uid=user_id,
        ):
            iid = "interview:" + str(r["iid"])
            if iid not in nodes:
                nodes[iid] = {
                    "id": iid,
                    "type": "interview",
                    "node_kind": "interview",
                    "label": r["itopic"] or "Interview",
                    "display_name": r["itopic"] or "Interview",
                }
            if r["mem_id"] in nodes:
                key = (iid, r["mem_id"], "PRODUCED")
                if key not in seen_links:
                    seen_links.add(key)
                    links.append({"source": iid, "target": r["mem_id"], "relation": "PRODUCED"})

            user_node_id = "user:" + user_id
            if user_node_id in nodes:
                key = (user_node_id, iid, "CONDUCTED")
                if key not in seen_links:
                    seen_links.add(key)
                    links.append({"source": user_node_id, "target": iid, "relation": "CONDUCTED"})

        # Memory to Memory relationships
        for r in s.run(
            """
            MATCH (u:User {user_id: $uid})-[:HAS_MEMORY]->(m1:Memory)
            MATCH (u)-[:HAS_MEMORY]->(m2:Memory)
            MATCH (m1)-[rel]->(m2)
            WHERE type(rel) IN ['SUPPORTS', 'CONTRADICTS', 'ILLUSTRATES', 'EVOLVED_FROM']
            RETURN m1.neon_id AS from_id, m2.neon_id AS to_id, type(rel) AS rel_type
            """,
            uid=user_id,
        ):
            if r["from_id"] in nodes and r["to_id"] in nodes:
                rel_type = r["rel_type"]
                key = (r["from_id"], r["to_id"], rel_type)
                if key not in seen_links:
                    seen_links.add(key)
                    links.append({
                        "source": r["from_id"],
                        "target": r["to_id"],
                        "relation": rel_type,
                    })

        # Add User -> Memory links so user anchor is connected in all KG states.
        for r in s.run(
            """
            MATCH (u:User {user_id: $uid})-[:HAS_MEMORY]->(m:Memory)
            RETURN m.neon_id AS mem_id
            """,
            uid=user_id,
        ):
            user_node_id = "user:" + user_id
            mem_id = r["mem_id"]
            if user_node_id in nodes and mem_id in nodes:
                key = (user_node_id, mem_id, "HAS_MEMORY")
                if key not in seen_links:
                    seen_links.add(key)
                    links.append({"source": user_node_id, "target": mem_id, "relation": "HAS_MEMORY"})


    node_values = []
    for node in nodes.values():
        if "node_kind" not in node:
            node["node_kind"] = node.get("type", "unknown")
        if "display_name" not in node:
            node["display_name"] = node.get("label", "")
        node_values.append(node)

    for link in links:
        link["label"] = _relation_label(link["relation"])

    return {"nodes": node_values, "links": links}
