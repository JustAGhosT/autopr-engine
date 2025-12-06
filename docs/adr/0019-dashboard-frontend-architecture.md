# 19. Dashboard Frontend Architecture

## Status

Accepted

## Context

AutoPR Engine requires a user-facing dashboard at `app.autopr.io` to provide:

- Repository management and configuration
- Bot exclusion management
- Workflow monitoring and control
- Integration status and configuration
- User settings and API key management

We need to decide on the frontend architecture that will best serve these needs while maintaining consistency with the existing codebase and enabling rapid development.

### Current State

- **Marketing site** (`autopr.io`): Next.js with Tailwind CSS and shadcn/ui
- **API server** (`app.autopr.io`): FastAPI returning JSON
- **Flask dashboard**: Exists at `autopr/dashboard/` but not deployed to app.autopr.io
- **Desktop app**: Tauri + React (in `autopr-desktop/`)

### Options Considered

1. **Next.js SSR** - Extend marketing site with dashboard pages
2. **React SPA** - Standalone single-page application
3. **FastAPI + Jinja2** - Server-rendered templates
4. **Vue/Svelte SPA** - Alternative frontend frameworks

## Decision

We will build the dashboard as a **React Single Page Application (SPA)** that communicates with the FastAPI backend via REST API.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      app.autopr.io                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐    ┌─────────────────────┐        │
│  │     React SPA       │    │      FastAPI        │        │
│  │   (Static Files)    │───►│   (/api/* routes)   │        │
│  │                     │    │                     │        │
│  │  - Dashboard UI     │    │  - Auth endpoints   │        │
│  │  - State (Zustand)  │    │  - CRUD operations  │        │
│  │  - React Query      │    │  - GitHub webhooks  │        │
│  └─────────────────────┘    └─────────────────────┘        │
│           │                          │                      │
│           │                          ▼                      │
│           │                 ┌─────────────────────┐        │
│           │                 │    PostgreSQL       │        │
│           │                 │    + Redis          │        │
│           │                 └─────────────────────┘        │
│           ▼                                                 │
│  ┌─────────────────────┐                                   │
│  │   GitHub OAuth      │                                   │
│  │   (Authentication)  │                                   │
│  └─────────────────────┘                                   │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Framework** | React 18+ | Team familiarity, ecosystem, existing desktop app uses React |
| **Language** | TypeScript | Type safety, better DX, matches marketing site |
| **Build Tool** | Vite | Fast builds, modern ESM support |
| **Styling** | Tailwind CSS + shadcn/ui | Matches marketing site, rapid development |
| **State** | TanStack Query + Zustand | Server state + client state separation |
| **Routing** | React Router v6 | Industry standard, nested routes |
| **Forms** | React Hook Form + Zod | Validation, performance |
| **HTTP** | Axios or Fetch | API communication |

### Directory Structure

```
dashboard/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── ui/              # shadcn/ui components
│   │   ├── layout/          # Header, Sidebar, Footer
│   │   └── features/        # Feature-specific components
│   ├── pages/               # Route pages
│   │   ├── Dashboard.tsx
│   │   ├── Repositories.tsx
│   │   ├── Bots.tsx
│   │   ├── Workflows.tsx
│   │   └── Settings.tsx
│   ├── hooks/               # Custom React hooks
│   ├── lib/                 # Utilities, API client
│   ├── stores/              # Zustand stores
│   ├── types/               # TypeScript types
│   └── App.tsx
├── public/                  # Static assets
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

### Deployment Strategy

1. **Build**: Vite builds static files (HTML, JS, CSS)
2. **Serve**: FastAPI serves static files at root, API at `/api/*`
3. **Routing**: Client-side routing with fallback to index.html

```python
# FastAPI static file serving
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="dashboard/dist", html=True), name="dashboard")
```

### Why Not Next.js?

While extending the marketing site would provide consistency, we chose React SPA because:

1. **Deployment Simplicity**: Single deployment unit with FastAPI
2. **No SSR Needed**: Dashboard doesn't need SEO/SSR
3. **Cleaner Separation**: Marketing (public) vs App (authenticated) concerns
4. **Familiar to Backend**: FastAPI team can serve static files easily
5. **Avoid Complexity**: No need for two Node.js deployments

### Why Not Server-Rendered (Jinja2)?

1. **Limited Interactivity**: Dashboards need rich client-side state
2. **Development Speed**: React ecosystem is faster for complex UIs
3. **Reusability**: Can share components with desktop app
4. **Modern UX**: SPAs provide smoother user experience

## Consequences

### Positive

- **Fast Development**: Rich React ecosystem, existing component libraries
- **Consistent Design**: Same Tailwind/shadcn as marketing site
- **Team Familiarity**: React is widely known, easy to onboard
- **Component Reuse**: Desktop app shares components
- **Single Deployment**: One container for both API and frontend
- **Strong Typing**: TypeScript catches errors early

### Negative

- **Initial Load Time**: SPA requires JS bundle download
- **Build Step**: Additional build process for frontend
- **Two Codebases**: Separate from marketing site (some duplication)
- **SEO**: Not applicable for dashboard, but limits if needed later

### Neutral

- **State Management**: Need to choose and maintain state solution
- **API Design**: Frontend drives API contract requirements
- **Testing**: Need frontend testing strategy (Vitest, Playwright)

## Implementation Notes

### Component Library Strategy

Reuse shadcn/ui components from marketing site:

```bash
# Initialize shadcn/ui in dashboard
npx shadcn-ui@latest init

# Add components as needed
npx shadcn-ui@latest add button card dialog table
```

### API Client Setup

```typescript
// lib/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  withCredentials: true, // For session cookies
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.location.href = '/api/auth/github/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

### Route Protection

```typescript
// components/ProtectedRoute.tsx
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) return <LoadingSpinner />;
  if (!user) return <Navigate to="/login" state={{ from: location }} replace />;

  return <>{children}</>;
}
```

## Related Decisions

- [ADR-0007: Authentication and Authorization](0007-authn-authz.md)
- [ADR-0018: AutoPR SaaS Consideration](0018-autopr-saas-consideration.md)
- [ADR-0020: Dashboard API Design](0020-dashboard-api-design.md)
- [ADR-0022: Session Management](0022-session-management.md)
