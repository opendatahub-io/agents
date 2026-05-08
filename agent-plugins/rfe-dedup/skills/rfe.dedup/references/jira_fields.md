# Jira Custom Field Reference

Custom fields require `cf[ID]` syntax in JQL — Jira does not accept the
human-readable name.

## Custom Fields (RHAISTRAT / RHAIRFE)

| Human name | JQL syntax | Type | Example |
|------------|-----------|------|---------|
| Target Version | `cf[10855]` | Multi-version | `cf[10855] = "rhoai-3.5"` |
| Color Status | `cf[10712]` | Select | `cf[10712] = Red` |
| Team | `cf[10001]` | Teams plugin | (unreliable via API — prefer component) |
| Epic Link | `cf[10014]` | Key reference | `cf[10014] = RHAIENG-1234` |
| Epic Name | `cf[10011]` | String | `cf[10011] ~ "Agent"` |
| Story Points | `cf[10028]` | Float | `cf[10028] is not EMPTY` |
| Parent Link | `cf[10018]` | Key reference | `cf[10018] = RHAISTRAT-100` |
| Contributors | `cf[10466]` | Multi-user | — |
| Sprint | `cf[10020]` | Sprint | — |
| Activity Type | `cf[10464]` | Select | Values: "New Features", "Tech Debt & Quality", "Learning & Enablement" |
| Status Summary | `cf[10814]` | Textarea | `cf[10814] is not EMPTY` |

## RHAISTRAT Workflow Statuses

```
New → Backlog → Refinement → To Do → In Progress → Review → Release Pending → Closed
```

## RHAIENG / RHOAIENG Workflow Statuses

```
New → Backlog → In Progress → Review → Testing → Resolved → Closed
```

## Priority Names (Red Hat, not Atlassian defaults)

Blocker → Critical → Major → Normal → Minor → Undefined

## Common JQL Patterns

```sql
-- All open RHAIRFE feature requests
project = RHAIRFE AND issuetype = "Feature Request" AND status != Closed

-- Features targeting a specific release
project = RHAISTRAT AND issuetype = Feature AND cf[10855] = "rhoai-3.5"

-- Red status features in a component
project = RHAISTRAT AND component = AgentOps AND cf[10712] = Red

-- Our org's components
component in (AgentOps, AgentDev, Agentic, "Data Processing",
    "Llama Stack Core", Notebooks, "Tooling Experience",
    "AAET DevOps", "RAG + Vector DB")
```
