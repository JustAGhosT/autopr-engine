# 18. AutoPR SaaS Offering Consideration

## Status

Proposed

## Context

AutoPR Engine is currently available as an open-source project that users can self-host. There is
an existing deployed instance at `app.autopr.io` that provides a managed experience. We need to
decide whether to formally offer AutoPR as a Software-as-a-Service (SaaS) product.

Key considerations include:

- Growing demand for managed solutions to reduce operational overhead
- Current `app.autopr.io` deployment serves as a limited-time trial instance
- Competitive landscape includes other AI code review tools with SaaS offerings
- Revenue generation potential for sustainability of the project
- Security and compliance requirements for enterprise customers
- Resource requirements for maintaining a production SaaS environment

## Decision

We will adopt a **hybrid model** that supports both self-hosted and SaaS deployments:

### 1. SaaS Offering (AutoPR Cloud)

#### 1.1 Tier Structure

| Tier | Target | Features | Pricing Model |
|------|--------|----------|---------------|
| **Free** | Individual developers, small projects | Limited repos, basic AI analysis, community support | Free |
| **Pro** | Small teams, startups | Unlimited repos, advanced AI models, priority support | Per seat/month |
| **Enterprise** | Large organizations | Custom AI models, SSO, audit logs, SLAs, dedicated support | Custom pricing |

#### 1.2 Core SaaS Features

- **Multi-tenant Architecture**: Secure isolation between customer data
- **Automated Scaling**: Handle variable workloads automatically
- **Managed Updates**: Automatic security patches and feature updates
- **Global CDN**: Low-latency access from anywhere
- **99.9% SLA**: For Pro and Enterprise tiers

### 2. Self-Hosted Option (AutoPR Engine)

Maintain the open-source self-hosted option for users who:

- Require complete data control
- Have compliance requirements preventing cloud usage
- Prefer to manage their own infrastructure
- Want to customize the codebase

### 3. Feature Parity Strategy

| Feature | Self-Hosted | SaaS Free | SaaS Pro | SaaS Enterprise |
|---------|-------------|-----------|----------|-----------------|
| Basic AI Analysis | ✅ | ✅ | ✅ | ✅ |
| GitHub Integration | ✅ | ✅ | ✅ | ✅ |
| Multi-agent Collaboration | ✅ | ❌ | ✅ | ✅ |
| Custom Workflows | ✅ | Limited | ✅ | ✅ |
| Linear/Jira Integration | ✅ | ❌ | ✅ | ✅ |
| Slack/Teams Integration | ✅ | ❌ | ✅ | ✅ |
| SSO/SAML | ✅ | ❌ | ❌ | ✅ |
| Audit Logs | ✅ | ❌ | ❌ | ✅ |
| Custom AI Models | ✅ | ❌ | ❌ | ✅ |
| Dedicated Support | ❌ | ❌ | Email | 24/7 + Slack |
| SLA | N/A | N/A | 99.5% | 99.9% |

### 4. Technical Architecture for SaaS

#### 4.1 Infrastructure Requirements

- **Cloud Provider**: Azure (primary), with multi-cloud capability
- **Container Orchestration**: Kubernetes (AKS)
- **Database**: PostgreSQL with connection pooling
- **Caching**: Redis Cluster
- **Message Queue**: Azure Service Bus or RabbitMQ
- **CDN**: Azure Front Door

#### 4.2 Security Requirements

- SOC 2 Type II compliance roadmap
- Data encryption at rest and in transit
- Regular penetration testing
- Customer data isolation (tenant separation)
- GDPR compliance for EU customers
- GitHub/GitLab OAuth for authentication

### 5. Revenue Projections (Year 1)

| Metric | Conservative | Moderate | Optimistic |
|--------|--------------|----------|------------|
| Free Users | 1,000 | 2,500 | 5,000 |
| Pro Subscriptions | 50 | 150 | 300 |
| Enterprise Contracts | 2 | 5 | 10 |
| Annual Revenue | $30K | $100K | $250K |

### 6. Go-to-Market Strategy

1. **Phase 1 (Months 1-3)**: Limited beta with current `app.autopr.io` users
2. **Phase 2 (Months 4-6)**: Public launch of Free and Pro tiers
3. **Phase 3 (Months 7-12)**: Enterprise tier with dedicated sales

## Consequences

### Positive

- **Revenue Stream**: Creates sustainable funding for project development
- **Broader Adoption**: Lower barrier to entry for non-technical users
- **Operational Control**: Better ability to gather telemetry and improve the product
- **Support Model**: Clearer support tiers and response expectations
- **Competitive Position**: Matches offerings from competitors like CodeRabbit

### Negative

- **Resource Requirements**: Significant investment in infrastructure and support
- **Complexity**: Managing both self-hosted and SaaS increases maintenance burden
- **Security Responsibility**: Higher stakes for protecting customer code
- **Support Costs**: Pro and Enterprise tiers require dedicated support resources
- **Vendor Lock-in Concerns**: Some users may be hesitant about SaaS dependency

### Neutral

- **Pricing Sensitivity**: Need to balance accessibility with sustainability
- **Feature Divergence**: Risk of features being SaaS-only over time
- **Community Dynamics**: Open source community may have mixed reactions

## Implementation Plan

### Phase 1: Foundation (Weeks 1-4)

- [ ] Finalize technical architecture
- [ ] Set up production Kubernetes cluster
- [ ] Implement multi-tenant database schema
- [ ] Design billing integration (Stripe)

### Phase 2: Core Platform (Weeks 5-8)

- [ ] Build user management and onboarding
- [ ] Implement usage tracking and limits
- [ ] Create admin dashboard
- [ ] Set up monitoring and alerting

### Phase 3: Beta Launch (Weeks 9-12)

- [ ] Invite beta testers from `app.autopr.io`
- [ ] Gather feedback and iterate
- [ ] Finalize pricing model
- [ ] Prepare marketing materials

### Phase 4: Public Launch (Weeks 13-16)

- [ ] Launch Free and Pro tiers
- [ ] Enable self-service signup
- [ ] Begin enterprise sales outreach
- [ ] Establish support processes

## Monitoring and Success Metrics

- **User Activation**: % of signups that complete first PR analysis
- **Conversion Rate**: % of free users upgrading to Pro
- **Churn Rate**: Monthly/annual subscription cancellations
- **Net Promoter Score (NPS)**: Customer satisfaction metric
- **Time to Value**: Time from signup to first successful analysis
- **Support Ticket Volume**: Tickets per customer by tier
- **Uptime**: Service availability percentage

## Alternatives Considered

### 1. SaaS Only

Abandon self-hosted option entirely. Rejected because:
- Alienates existing community
- Limits adoption in regulated industries

### 2. Self-Hosted Only

Continue without SaaS offering. Rejected because:
- Limits market reach
- No sustainable revenue model
- Higher barrier to entry for casual users

### 3. Open Core Model

More aggressive feature gating. Rejected because:
- Could fragment community
- May create perception of "crippled" open source version

## Related Decisions

- [ADR-0012: Deployment Strategy](0012-deployment-strategy.md)
- [ADR-0013: Security Strategy](0013-security-strategy.md)
- [ADR-0007: Authentication and Authorization](0007-authn-authz.md)
