# Application Architecture

## System Flow Diagram

```mermaid
flowchart TD
    Start([User visits Homepage]) --> Input[Enter Recipe URL]
    Input --> Submit[Click 'Go']
    Submit --> RateLimit{Rate Limit Check<br/>20 requests/hour}

    RateLimit -->|Exceeded| RateLimitPage[Show Rate Limit Page<br/>with countdown timer]
    RateLimit -->|Within Limit| SSRF{SSRF Protection<br/>Check URL}

    SSRF -->|Blocked| ErrorPage[Show Error:<br/>Invalid URL]
    SSRF -->|Valid| Duplicate{Recipe Already<br/>in Database?}

    Duplicate -->|Yes| ShowRecipe[Redirect to<br/>Existing Recipe]
    Duplicate -->|No| Parse[Parse Recipe with<br/>GPT-4o-mini API]

    Parse --> Budget{Daily Budget<br/>Check}
    Budget -->|Exceeded| BudgetPage[Show Budget<br/>Exceeded Page]
    Budget -->|Within Budget| ExtractData[Extract:<br/>• Title<br/>• Ingredients<br/>• Directions<br/>• Prep/Cook Time]

    ExtractData --> SaveDB[(Save to<br/>PostgreSQL)]
    SaveDB --> ShowRecipe

    ShowRecipe --> ViewRecipe[View Recipe Page]
    ViewRecipe --> UserActions{User Action?}

    UserActions -->|Copy Ingredients| Clipboard[Copy to Clipboard]
    UserActions -->|Browse All| AllRecipes[All Recipes Page]
    UserActions -->|Search| SearchRecipes[Search Results]
    UserActions -->|Create Shopping List| ShoppingFlow

    AllRecipes --> ShoppingFlow[Shopping List Page]
    ShoppingFlow --> SelectRecipes[Select Multiple Recipes<br/>with Search & Filter]
    SelectRecipes --> GenerateList[Generate Combined<br/>Shopping List]
    GenerateList --> ShowList[Shopping List Results<br/>with Checkboxes]

    ShowList --> EndFlow([End])
    Clipboard --> EndFlow
    SearchRecipes --> EndFlow

    style Start fill:#f97316,stroke:#ea580c,color:#fff
    style EndFlow fill:#f97316,stroke:#ea580c,color:#fff
    style Parse fill:#fbbf24,stroke:#f59e0b
    style SaveDB fill:#10b981,stroke:#059669
    style RateLimit fill:#ef4444,stroke:#dc2626
    style SSRF fill:#ef4444,stroke:#dc2626
    style Budget fill:#ef4444,stroke:#dc2626
```

## Technology Stack

```mermaid
graph LR
    subgraph Frontend
        HTML[HTML5 Templates]
        TW[TailwindCSS v4]
        JS[Vanilla JavaScript]
    end

    subgraph Backend
        Flask[Flask Framework]
        SA[SQLAlchemy ORM]
        FM[Flask-Migrate]
    end

    subgraph External
        OpenAI[OpenAI GPT-4o-mini<br/>Recipe Parsing]
        DB[(PostgreSQL<br/>Supabase)]
    end

    subgraph Security
        RL[Rate Limiting<br/>20/hour]
        SSRF[SSRF Protection]
        BC[Budget Control<br/>$1/day]
    end

    HTML --> Flask
    TW --> HTML
    JS --> HTML
    Flask --> SA
    SA --> DB
    Flask --> OpenAI
    Flask --> RL
    Flask --> SSRF
    Flask --> BC
    FM --> DB

    style OpenAI fill:#10b981,stroke:#059669
    style DB fill:#3b82f6,stroke:#2563eb
    style Flask fill:#f97316,stroke:#ea580c,color:#fff
    style RL fill:#ef4444,stroke:#dc2626
    style SSRF fill:#ef4444,stroke:#dc2626
    style BC fill:#ef4444,stroke:#dc2626
```

## Database Schema

```mermaid
erDiagram
    RECIPES ||--o{ INGREDIENTS : has
    RECIPES ||--o{ DIRECTIONS : has
    RECIPES ||--o{ GROCERY_LISTS : has

    RECIPES {
        int id PK
        string title
        string source_url
        datetime date_added
        string prep_time
        string cook_time
    }

    INGREDIENTS {
        int id PK
        int recipe_id FK
        string ingredient
    }

    DIRECTIONS {
        int id PK
        int recipe_id FK
        int step_number
        string direction
    }

    GROCERY_LISTS {
        int id PK
        int recipe_id FK
        string category
        json items
    }

    RATE_LIMITS {
        int id PK
        string ip_address
        string endpoint
        datetime window_start
        int request_count
    }

    API_USAGE {
        int id PK
        date date
        int request_count
        decimal estimated_cost
        int tokens_used
    }

    BLOCKED_IPS {
        int id PK
        string ip_address
        string reason
        datetime blocked_at
        datetime blocked_until
    }
```

## Security & Protection Flow

```mermaid
sequenceDiagram
    participant User
    participant App
    participant RateLimit
    participant SSRF
    participant Budget
    participant OpenAI
    participant DB

    User->>App: Submit Recipe URL
    App->>RateLimit: Check IP Address

    alt Rate Limit Exceeded
        RateLimit-->>User: 429 Rate Limited
    else Within Limit
        RateLimit->>SSRF: Validate URL

        alt Blocked URL (localhost/private)
            SSRF-->>User: Show SSRF Error
        else Valid URL
            SSRF->>DB: Check if Recipe Exists

            alt Recipe Exists
                DB-->>User: Redirect to Existing Recipe
            else New Recipe
                DB->>Budget: Check Daily Budget

                alt Budget Exceeded
                    Budget-->>User: 503 Budget Exceeded
                else Within Budget
                    Budget->>OpenAI: Parse Recipe
                    OpenAI->>App: Return Parsed Data
                    App->>DB: Save Recipe
                    DB-->>User: Show Recipe Page
                end
            end
        end
    end
```

## Key Features

### 1. Recipe Parsing
- Extracts clean recipe data from any URL
- Uses GPT-4o-mini for intelligent parsing
- Automatic duplicate detection

### 2. Abuse Protection
- **Rate Limiting**: 20 requests/hour per IP
- **SSRF Protection**: Blocks localhost and private IPs
- **Budget Control**: $1/day API spending cap
- **Cost Tracking**: ~$0.00045 per request

### 3. Multi-Recipe Shopping Lists
- Select multiple recipes with search/filter
- Combined ingredient list
- Interactive checkboxes for shopping

### 4. Mobile-First Design
- Responsive on all screen sizes
- 44px touch targets for mobile
- Progressive enhancement

## Deployment Architecture

```mermaid
graph TB
    subgraph User
        Browser[Web Browser]
    end

    subgraph Render.com
        App[Flask Application<br/>Free Tier]
        Gunicorn[Gunicorn WSGI Server]
    end

    subgraph Supabase
        PG[(PostgreSQL Database<br/>Free Tier)]
        Pooler[PgBouncer Connection Pooler]
    end

    subgraph OpenAI
        API[GPT-4o-mini API<br/>Pay-per-use]
    end

    Browser <-->|HTTPS| App
    App --> Gunicorn
    Gunicorn <-->|Connection Pooling| Pooler
    Pooler <--> PG
    App <-->|API Calls| API

    style App fill:#f97316,stroke:#ea580c,color:#fff
    style PG fill:#3b82f6,stroke:#2563eb
    style API fill:#10b981,stroke:#059669
```

## Cost Breakdown

- **Hosting**: $0/month (Render free tier)
- **Database**: $0/month (Supabase free tier)
- **API Costs**: ~$0.22/day at full capacity (480 requests)
- **Safety Buffer**: $1/day budget cap (4.5x safety margin)

**Total Monthly Cost**: < $7/month for full usage
