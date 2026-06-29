# FounderOS Multi-Tenant Isolation Implementation Prompt

You are working on the FounderOS AI backend. The application uses:

* FastAPI
* PostgreSQL + SQLAlchemy
* Qdrant
* JWT authentication with a custom `users` table (NOT Supabase Auth)
* LangGraph Agents

The database has been updated so that all tenant-owned tables contain:

```python
owner_id INT4 REFERENCES users(id)
```

The goal is to implement **complete multi-tenant isolation**, ensuring that no founder can access another founder's data, either in PostgreSQL or in Qdrant.

---

# Part 1: PostgreSQL Multi-Tenant Isolation

## Rule

Every table that contains founder-specific data must be filtered by:

```python
Model.owner_id == current_user.id
```

This applies to:

* investors
* meetings
* memories
* followups
* notes
* reminders
* emails
* activity_logs
* notifications
* recommendations

---

# 1. All CREATE operations

Whenever a new row is created, automatically assign ownership:

```python
owner_id = current_user.id
```

Example:

```python
memory = Memory(
    investor_id=investor_id,
    memory=memory_text,
    memory_type=memory_type,
    owner_id=current_user.id
)
```

Example:

```python
meeting = Meeting(
    investor_id=investor_id,
    summary=summary,
    owner_id=current_user.id
)
```

---

# 2. All SELECT operations

Never query tables without owner filtering.

Incorrect:

```python
db.query(Memory).all()
```

Correct:

```python
db.query(Memory).filter(
    Memory.owner_id == current_user.id
)
```

Incorrect:

```python
db.query(Investor).all()
```

Correct:

```python
db.query(Investor).filter(
    Investor.owner_id == current_user.id
)
```

---

# 3. All UPDATE operations

Always ensure:

```python
.filter(
    Model.owner_id == current_user.id
)
```

Example:

```python
db.query(Memory).filter(
    Memory.id == memory_id,
    Memory.owner_id == current_user.id
)
```

---

# 4. All DELETE operations

Always ensure:

```python
.filter(
    Model.owner_id == current_user.id
)
```

Example:

```python
db.query(Investor).filter(
    Investor.id == investor_id,
    Investor.owner_id == current_user.id
)
```

---

# 5. Services that must be updated

Review all service methods and add owner filtering:

* InvestorService
* MemoryService
* MeetingService
* RecommendationService
* NotificationService
* ReminderService
* EmailService
* ActivityLogService

Every database query should be scoped to:

```python
current_user.id
```

---

# 6. API endpoints

Every API endpoint should pass:

```python
current_user.id
```

into service methods.

Example:

```python
memory_service.get_memories(
    owner_id=current_user.id
)
```

---

# Part 2: Qdrant Multi-Tenant Isolation

Qdrant currently stores vectors globally.

Without filtering, semantic search can return memories belonging to another founder.

This must be fixed.

---

# 1. Add owner_id to all vector payloads

Whenever vectors are inserted into Qdrant, include:

```python
payload = {
    "owner_id": current_user.id,
    ...
}
```

This applies to:

* investor_memories
* meeting_transcripts
* investor_notes

---

# Example payload

```python
payload = {
    "owner_id": current_user.id,
    "investor_id": investor_id,
    "memory_type": memory.memory_type,
    "memory": memory.memory
}
```

---

# 2. Update vector insertion code

Review:

* MemoryService
* MeetingService
* NotesService
* QdrantTool

Any place that calls:

```python
qdrant.upsert(...)
```

must include:

```python
owner_id
```

inside the payload.

---

# 3. Semantic Search Filtering

All Qdrant searches must filter by owner.

Incorrect:

```python
client.search(
    collection_name="investor_memories",
    query_vector=embedding,
    limit=5
)
```

Correct:

```python
client.search(
    collection_name="investor_memories",
    query_vector=embedding,
    limit=5,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="owner_id",
                match=MatchValue(
                    value=owner_id
                )
            )
        ]
    )
)
```

---

# 4. Update semantic_search()

Change:

```python
semantic_search(query)
```

to:

```python
semantic_search(
    query,
    owner_id=current_user.id
)
```

---

# 5. Retrieval Agent

Update RetrievalAgent.

Incorrect:

```python
memories = memory_service.semantic_search(query)
```

Correct:

```python
memories = memory_service.semantic_search(
    query,
    owner_id=current_user.id
)
```

---

# 6. Memory Agent

When creating memories:

```python
memory_service.create_memory(
    ...,
    owner_id=current_user.id
)
```

---

# 7. Meeting and Notes Agents

Apply the same pattern.

Whenever embeddings are stored:

```python
payload["owner_id"] = current_user.id
```

Whenever embeddings are searched:

```python
owner_id == current_user.id
```

---

# Final Goal

The architecture should become:

Founder A
↓
PostgreSQL rows filtered by owner_id
↓
Qdrant vectors filtered by owner_id
↓
Only Founder A's data

Founder B
↓
PostgreSQL rows filtered by owner_id
↓
Qdrant vectors filtered by owner_id
↓
Only Founder B's data

No founder should ever be able to retrieve another founder's:

* investors
* meetings
* memories
* notes
* transcripts
* recommendations
* reminders
* emails
* activity logs
* notifications

Implement this across the entire backend.
