# Agentic-Geospatial-Route-Planner
I noticed field agents spend hours manually planning village visits. Google Maps doesn't understand the operational constraints. I started building an Agentic AI Route Planner that retrieves village data, validates locations, and optimizes routes automatically.

## Architecture

```mermaid
flowchart TD
    U["User / Field Employee"] --> FE["Frontend<br/>Route Planning UI"]

    FE --> API["API Gateway / FastAPI Backend"]
    API --> PA["Planner Agent<br/>Understand intent and extract route request"]

    PA --> VA["Village Validation Agent<br/>Detect duplicates, spelling issues, ambiguity"]
    VA --> CLARIFY{"Need clarification?"}
    CLARIFY -->|Yes| FE
    CLARIFY -->|No| GA["Geospatial Retrieval Agent"]

    GA --> DATA["Village Dataset<br/>Census / Internal Data"]
    GA --> OSM["OpenStreetMap / Nominatim"]
    GA --> DB["PostgreSQL + PostGIS"]

    GA --> ROA["Route Optimization Agent<br/>Optimize visit order"]
    ROA --> OSRM["OSRM / Distance Matrix"]
    ROA --> ORTOOLS["OR-Tools / NetworkX"]

    ROA --> MA["Map Generation Agent<br/>Markers, route overlay, interactive map"]
    MA --> MAP["Folium / Leaflet / Mapbox"]

    MA --> RA["Response Agent<br/>Explain route and decisions"]
    RA --> RESULT["Final Output<br/>Optimized route, map, reasoning, warnings"]
    RESULT --> FE

    subgraph OBS["Observability"]
        LOGS["CloudWatch Logs"]
        TRACE["OpenTelemetry Traces"]
        LF["Langfuse Agent Tracing"]
    end

    API --> LOGS
    PA --> TRACE
    VA --> TRACE
    GA --> TRACE
    ROA --> TRACE
    RA --> LF

    subgraph AWS["AWS Deployment"]
        ECS["ECS Fargate"]
        S3["S3<br/>Datasets / artifacts / logs"]
        RDS["RDS PostgreSQL"]
        OPENSEARCH["OpenSearch<br/>Future retrieval layer"]
    end

    API --> ECS
    DATA --> S3
    DB --> RDS
    GA --> OPENSEARCH

    subgraph CICD["Infrastructure & CI/CD"]
        GH["GitHub Actions"]
        TF["Terraform"]
    end

    GH --> TF
    TF --> AWS

    classDef user fill:#E0F2FE,stroke:#0284C7,color:#0C4A6E,stroke-width:2px
    classDef api fill:#F0FDF4,stroke:#16A34A,color:#14532D,stroke-width:2px
    classDef agent fill:#FEF3C7,stroke:#D97706,color:#78350F,stroke-width:2px
    classDef decision fill:#FCE7F3,stroke:#DB2777,color:#831843,stroke-width:2px
    classDef data fill:#EEF2FF,stroke:#4F46E5,color:#312E81,stroke-width:2px
    classDef output fill:#DCFCE7,stroke:#15803D,color:#14532D,stroke-width:2px
    classDef observability fill:#F3E8FF,stroke:#9333EA,color:#581C87,stroke-width:2px
    classDef cloud fill:#FFEDD5,stroke:#EA580C,color:#7C2D12,stroke-width:2px
    classDef cicd fill:#E5E7EB,stroke:#4B5563,color:#111827,stroke-width:2px

    class U,FE user
    class API api
    class PA,VA,GA,ROA,MA,RA agent
    class CLARIFY decision
    class DATA,OSM,DB,OSRM,ORTOOLS,MAP data
    class RESULT output
    class LOGS,TRACE,LF observability
    class ECS,S3,RDS,OPENSEARCH cloud
    class GH,TF cicd
```
