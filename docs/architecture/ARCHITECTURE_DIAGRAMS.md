# ARCHITECTURE_DIAGRAMS.md

> **Diagrammi Architetturali di Osservatorio**
> Questa documentazione contiene i diagrammi Mermaid che illustrano l'architettura e i flussi del sistema.

## 📊 Indice Diagrammi

1. [Architettura Generale](#architettura-generale)
2. [Flusso Dati (Raw → Clean → Business)](#flusso-dati)
3. [Componenti Dashboard](#componenti-dashboard)
4. [Database Architecture](#database-architecture)
5. [API Integration Flow](#api-integration-flow)
6. [Security & Rate Limiting](#security--rate-limiting)
7. [Deployment Architecture](#deployment-architecture)

## 🏗️ Architettura Generale

```mermaid
---
id: 134e43ec-6078-40d9-ae2f-fc781deaee20
---
graph TB
   subgraph "External APIs"
       ISTAT[ISTAT API]
       PBI[PowerBI API]
       TAB[Tableau API]
   end

   subgraph "Osservatorio Core"
       subgraph "API Layer"
           APIM[API Manager]
           CB[Circuit Breaker]
           RL[Rate Limiter]
           CACHE[Cache Layer]
       end

       subgraph "Processing Layer"
           DL[Data Loader]
           TRANS[Transformers]
           ANAL[Analyzers]
           VAL[Validators]
       end

       subgraph "Storage Layer"
           DUCK[(DuckDB<br/>Analytics)]
           PG[(PostgreSQL<br/>Metadata)]
           FS[File System<br/>Temp Storage]
       end

       subgraph "Presentation Layer"
           DASH[Streamlit Dashboard]
           API[FastAPI Server]
       end
   end

   subgraph "Users"
       WEB[Web Users]
       APIUSER[API Users]
   end

   %% Connections
   ISTAT --> CB
   PBI --> CB
   TAB --> CB

   CB --> RL
   RL --> CACHE
   CACHE --> APIM

   APIM --> DL
   DL --> VAL
   VAL --> TRANS
   TRANS --> ANAL

   ANAL --> DUCK
   ANAL --> PG
   DL --> FS

   DUCK --> DASH
   PG --> DASH
   DUCK --> API
   PG --> API

   WEB --> DASH
   APIUSER --> API

   classDef external fill:#f9f,stroke:#333,stroke-width:2px
   classDef storage fill:#bbf,stroke:#333,stroke-width:2px
   classDef processing fill:#bfb,stroke:#333,stroke-width:2px
   classDef presentation fill:#fbf,stroke:#333,stroke-width:2px

   class ISTAT,PBI,TAB external
   class DUCK,PG,FS storage
   class DL,TRANS,ANAL,VAL processing
   class DASH,API presentation

```

## 🔄 Flusso Dati

```mermaid
flowchart LR
    subgraph "RAW Stage"
        R1[XML/SDMX Data]
        R2[JSON Data]
        R3[CSV Data]
    end

    subgraph "Validation"
        V1{Schema<br/>Valid?}
        V2{Data<br/>Complete?}
        V3[Error Log]
    end

    subgraph "CLEAN Stage"
        C1[Parse & Extract]
        C2[Type Conversion]
        C3[Normalize Values]
        C4[Handle Missing]
    end

    subgraph "BUSINESS Stage"
        B1[Apply Business Rules]
        B2[Calculate Metrics]
        B3[Aggregate Data]
        B4[Enrich Metadata]
    end

    subgraph "Storage"
        S1[(DuckDB)]
        S2[(PostgreSQL)]
    end

    %% Flow
    R1 --> V1
    R2 --> V1
    R3 --> V1

    V1 -->|No| V3
    V1 -->|Yes| V2
    V2 -->|No| V3
    V2 -->|Yes| C1

    C1 --> C2
    C2 --> C3
    C3 --> C4

    C4 --> B1
    B1 --> B2
    B2 --> B3
    B3 --> B4

    B4 --> S1
    B4 --> S2

    style V3 fill:#f99,stroke:#333,stroke-width:2px
    style S1 fill:#bbf,stroke:#333,stroke-width:2px
    style S2 fill:#bbf,stroke:#333,stroke-width:2px
```

## 🎨 Componenti Dashboard

```mermaid
graph TD
    subgraph "Streamlit App Structure"
        MAIN[streamlit_app.py<br/>Entry Point]

        subgraph "Pages"
            P1[📊 Home]
            P2[👥 Popolazione]
            P3[🏥 Sanità]
            P4[💼 Lavoro]
            P5[📈 Analytics]
        end

        subgraph "Components"
            C1[Sidebar Navigator]
            C2[Data Selector]
            C3[Chart Builder]
            C4[Export Manager]
            C5[Filter Panel]
        end

        subgraph "Utils"
            U1[Session Manager]
            U2[Cache Manager]
            U3[Theme Manager]
            U4[Auth Handler]
        end
    end

    MAIN --> P1
    MAIN --> C1
    C1 --> P2
    C1 --> P3
    C1 --> P4
    C1 --> P5

    P1 --> C2
    P1 --> C3
    P2 --> C2
    P2 --> C3
    P2 --> C5

    C2 --> U2
    C3 --> C4
    C1 --> U1
    MAIN --> U3
    MAIN --> U4
```

## 🗄️ Database Architecture

```mermaid
erDiagram
    DATASETS {
        string dataset_id PK
        string name
        string category
        string source_api
        timestamp last_updated
        json metadata
        string status
    }

    DATA_POINTS {
        bigint id PK
        string dataset_id FK
        string dimension_1
        string dimension_2
        string dimension_3
        float value
        string unit
        date reference_date
        timestamp created_at
    }

    API_REQUESTS {
        bigint request_id PK
        string api_name
        string endpoint
        timestamp requested_at
        int response_time_ms
        int status_code
        json headers
        text error_message
    }

    CACHE_ENTRIES {
        string cache_key PK
        string dataset_id FK
        json data
        timestamp created_at
        timestamp expires_at
        int hit_count
    }

    USERS {
        int user_id PK
        string username
        string email
        string role
        timestamp created_at
        timestamp last_login
    }

    API_KEYS {
        string api_key PK
        int user_id FK
        string name
        timestamp created_at
        timestamp expires_at
        boolean is_active
        json permissions
    }

    EXPORT_LOGS {
        bigint export_id PK
        int user_id FK
        string dataset_id FK
        string format
        timestamp exported_at
        int row_count
        string file_path
    }

    DATASETS ||--o{ DATA_POINTS : contains
    DATASETS ||--o{ CACHE_ENTRIES : cached_in
    DATASETS ||--o{ EXPORT_LOGS : exported_in
    USERS ||--o{ API_KEYS : owns
    USERS ||--o{ EXPORT_LOGS : requested
```

## 🔌 API Integration Flow

```mermaid
sequenceDiagram
    participant User
    participant Dashboard
    participant APIManager
    participant CircuitBreaker
    participant RateLimiter
    participant Cache
    participant ISTATApi
    participant Storage

    User->>Dashboard: Request Data
    Dashboard->>APIManager: fetch_dataset("DCIS_POPRES1")
    APIManager->>CircuitBreaker: check_status()

    alt Circuit Open
        CircuitBreaker-->>APIManager: CircuitOpenError
        APIManager-->>Dashboard: Return cached/stale data
    else Circuit Closed
        CircuitBreaker->>RateLimiter: check_rate_limit()

        alt Rate Limit Exceeded
            RateLimiter-->>APIManager: RateLimitError
            APIManager-->>Dashboard: Return 429 error
        else Within Limits
            RateLimiter->>Cache: get(dataset_id)

            alt Cache Hit
                Cache-->>Dashboard: Return cached data
            else Cache Miss
                Cache->>ISTATApi: GET /SDMX/dataset
                ISTATApi-->>Cache: XML Response
                Cache->>Cache: Parse & Transform
                Cache->>Storage: Save to DuckDB
                Storage-->>Cache: Confirmation
                Cache-->>Dashboard: Return fresh data
            end
        end
    end

    Dashboard-->>User: Display results
```

## 🔒 Security & Rate Limiting

```mermaid
stateDiagram-v2
    [*] --> Idle

    Idle --> CheckingRate: API Request

    CheckingRate --> ValidatingToken: Rate OK
    CheckingRate --> RateLimited: Rate Exceeded

    ValidatingToken --> Authenticated: Token Valid
    ValidatingToken --> Unauthorized: Token Invalid

    Authenticated --> ProcessingRequest: Check Permissions
    Unauthorized --> [*]: Return 401

    ProcessingRequest --> CircuitCheck: Start Processing

    CircuitCheck --> Open: Too Many Failures
    CircuitCheck --> HalfOpen: Recovery Mode
    CircuitCheck --> Closed: Healthy

    Open --> [*]: Return 503
    HalfOpen --> Closed: Success
    HalfOpen --> Open: Failure

    Closed --> Success: Process Complete
    Closed --> Failed: Process Error

    Success --> UpdateMetrics: Log Success
    Failed --> UpdateMetrics: Log Failure

    UpdateMetrics --> [*]
    RateLimited --> [*]: Return 429

    note right of CircuitCheck
        Circuit Breaker Pattern
        - Open: Block all requests
        - Half-Open: Test recovery
        - Closed: Normal operation
    end note

    note right of CheckingRate
        Rate Limiting
        - 100 req/hour per API key
        - 10 req/min burst
    end note
```

## 🚀 Deployment Architecture

```mermaid
graph TB
    subgraph "Development"
        DEV[Local Machine]
        DOCKER[Docker Compose]
        DEV --> DOCKER
    end

    subgraph "CI/CD Pipeline"
        GH[GitHub]
        GHA[GitHub Actions]
        TEST[Test Suite]
        BUILD[Build]

        GH --> GHA
        GHA --> TEST
        TEST --> BUILD
    end

    subgraph "Staging"
        STREAM_STG[Streamlit Cloud<br/>Free Tier]
        NEON_STG[Neon PostgreSQL<br/>Free Tier]

        BUILD --> STREAM_STG
        STREAM_STG --> NEON_STG
    end

    subgraph "Production"
        subgraph "Frontend"
            CF[Cloudflare CDN]
            STREAM_PRD[Streamlit Cloud<br/>Pro]
        end

        subgraph "Backend"
            API_GW[API Gateway]
            FASTAPI[FastAPI<br/>Container]
            WORKER[Background Workers]
        end

        subgraph "Data Layer"
            DUCK_PRD[(DuckDB<br/>Analytics)]
            PG_PRD[(PostgreSQL<br/>Cloud)]
            REDIS[(Redis<br/>Cache)]
        end

        subgraph "Monitoring"
            GRAFANA[Grafana]
            LOKI[Loki Logs]
            PROM[Prometheus]
        end
    end

    BUILD --> CF
    CF --> STREAM_PRD
    CF --> API_GW

    API_GW --> FASTAPI
    FASTAPI --> WORKER

    FASTAPI --> DUCK_PRD
    FASTAPI --> PG_PRD
    FASTAPI --> REDIS

    WORKER --> DUCK_PRD
    WORKER --> PG_PRD

    FASTAPI --> PROM
    WORKER --> PROM
    PROM --> GRAFANA
    FASTAPI --> LOKI
    LOKI --> GRAFANA

    style DEV fill:#f9f,stroke:#333,stroke-width:2px
    style STREAM_STG fill:#bbf,stroke:#333,stroke-width:2px
    style STREAM_PRD fill:#bfb,stroke:#333,stroke-width:2px
```

---

> **Note**: Questi diagrammi sono stati generati con Mermaid.js e sono compatibili con GitHub, GitLab e la maggior parte dei viewer Markdown moderni.
>
> Per visualizzare correttamente i diagrammi:
> - **GitHub**: Supporto nativo
> - **VS Code**: Estensione "Mermaid Preview"
> - **Local**: Live Server con Mermaid.js CDN
