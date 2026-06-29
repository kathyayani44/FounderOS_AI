You are working on the FounderOS AI backend. The project uses:
FastAPI
PostgreSQL + SQLAlchemy
Qdrant
LangGraph agents
Gemini

The system currently has three Qdrant collections:

investor_memories
meeting_transcripts
investor_notes

Currently, the Retrieval Agent searches only:

investor_memories

I do NOT want to search all three collections every time because it will create redundancy and noisy context.

Desired Architecture
Purpose of each collection
1. investor_memories

Contains:

investor preferences
concerns
action items
relationship notes
durable facts

Examples:

Prefers B2B SaaS.
Concerned about revenue.
Asked for unit economics.
Interested in healthcare AI.

This should remain the PRIMARY knowledge store and should be searched by default.

2. investor_notes

Contains:

manually written notes
summaries of meetings
contextual information

Examples:

Met at TechCrunch event.
Former operator.
Likes founder-market fit.

This should be searched only when additional context is needed.

3. meeting_transcripts

Contains:

raw meeting transcripts
entire conversations
Zoom recordings converted to text

Examples:

Founder: Thank you...
Investor: Tell me about your margins...

This collection should NOT be searched by default because:

transcripts are large
information overlaps with memories
increases token usage
lowers retrieval quality
causes duplicate context.
New Retrieval Strategy

Implement hierarchical retrieval.

Step 1

Search:

collections = ["investor_memories"]
Step 2

If the planner or query requires more context:

Search:

collections = [
    "investor_memories",
    "investor_notes"
]
Step 3

Only search meeting transcripts when the user explicitly asks about meetings.

Examples:

What did Sequoia say in our last meeting?
Summarize our meeting with Accel.
Did the investor mention pricing?
What concerns came up during the meeting?

Then:

collections = [
    "investor_memories",
    "meeting_transcripts"
]
Planner Changes

Modify PlannerAgent so it can determine which collections should be searched.

Planner output should become:

{
    "workflow": ["retrieval", "scoring"],
    "collections": ["investor_memories"]
}

or

{
    "workflow": ["retrieval"],
    "collections": [
        "investor_memories",
        "investor_notes"
    ]
}

or

{
    "workflow": ["retrieval"],
    "collections": [
        "investor_memories",
        "meeting_transcripts"
    ]
}
Retrieval Agent Changes

Update RetrievalAgent so it:

Reads:
state["collections"]
Searches only the specified collections.
Combines results.
Deduplicates results using:
memory_id
transcript_id
text similarity
Returns:
{
    "retrieved_context": {
        "investor": {...},
        "memories": [...],
        "notes": [...],
        "transcripts": [...]
    }
}
Transcript Processing Improvement

Whenever a meeting transcript is saved:

Pipeline:

Transcript
      ↓
LLM extraction
      ↓
Investor Memories
      ↓
Investor Notes

Store:

meeting_transcripts

Full raw transcript.

investor_memories

Durable facts extracted from the transcript.

investor_notes

Concise meeting summary.

This allows most future retrieval to use:

investor_memories

without needing to retrieve large transcripts.

Desired Retrieval Behaviour
User Query	Collections
"What does Sequoia care about?"	investor_memories
"Give me context on Sequoia."	investor_memories + investor_notes
"What happened in our last meeting?"	investor_memories + meeting_transcripts
"Did they mention pricing?"	investor_memories + meeting_transcripts
Goal

Implement a tiered retrieval system that:

minimizes redundancy
improves retrieval quality
reduces token usage
avoids retrieving large transcripts unnecessarily
keeps meeting transcripts available for meeting-specific questions only.

Do not merge all three collections into one global search. Use intent-aware retrieval instead.     and there are Missing agents:
The planner knows about:
extraction agent
recommendation agent
communication agent , but it does not know about, explanation agent, we also have that to be included, as the agent must explain why they recommended so to the user
Missing agents:
The planner knows about:
extraction agent
recommendation agent
communication agent , but it does not know about, explanation agent, we also have that to be included, as the agent must explain why they recommended so to the user