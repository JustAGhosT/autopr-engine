# Authentication System Documentation

## Overview

The Tezos Liquidity Management platform implements a version-aware authentication system that
supports both standard and corporate user flows. The system is built on Supabase Auth and includes
route protection, social login options, and version-specific redirects.

## Table of Contents

- [Architecture](#architecture)
- [Setup Instructions](#setup-instructions)
- [Authentication Flow](#authentication-flow)
- [Protected Routes](#protected-routes)
- [Version-Aware Components](#version-aware-components)
- [Configuration Options](#configuration-options)
- [Social Authentication](#social-authentication)
- [Troubleshooting](#troubleshooting)
- [Extending the System](#extending-the-system)

## Architecture

The authentication system consists of several key components:

- **Auth Service**: Handles login, registration, and social authentication
- **Auth Middleware**: Protects routes and handles redirects
- **Version-Aware Components**: Adapts UI based on version (standard/corporate)
- **Protected Route Component**: Client-side protection for React components
- **Auth Callback Handler**: Processes OAuth callbacks and redirects

## Setup Instructions

### Prerequisites

- Supabase project with Auth enabled
- Environment variables configured

### Environment Variables

Add the following environment variables to your project:

```txt

NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### Social Login Configuration

1. Configure OAuth providers in your Supabase dashboard
2. Add the callback URL: `<https://your-domain.com/auth/callback`>
3. Update the allowed redirect URLs in your OAuth provider settings

## Authentication Flow

### Login Process

1. User visits a protected route
2. Middleware checks authentication status
3. If not authenticated, user is redirected to the version-specific login page
4. After successful login, user is redirected to the original URL

### Registration Process

1. User completes registration form
2. Account is created with version-specific metadata
3. User is redirected to the appropriate dashboard

### Version-Specific Redirects

The system automatically detects which version (standard/corporate) the user is using and redirects
accordingly:

- Standard users → `/standard/dashboard`
- Corporate users → `/corporate/dashboard`

## Protected Routes

### Route Protection Configuration

Protected routes are defined in `lib/auth/auth-middleware.ts`:

```typescript
const protectedPatterns = [
  "/standard/dashboard",
  "/corporate/dashboard",
  "/standard/settings",
  "/corporate/settings",
  "/standard/analytics",
  "/corporate/analytics",
  "/standard/strategies",
  "/corporate/strategies",
  "/standard/pools",
  "/corporate/pools",
];
```

### Adding New Protected Routes

To add new protected routes:

1. Add the route pattern to the `protectedPatterns` array
2. The middleware will automatically protect these routes

### Public Routes

Public routes are defined in the same file:

```typescript
const publicRoutes = [
  "/",
  "/standard",
  "/corporate",
  "/standard/login",
  "/standard/register",
  "/corporate/login",
  "/corporate/register",
  "/auth/callback",
  "/auth/login",
  "/auth/register",
  "/auth/reset-password",
];
```

## Version-Aware Components

### Login Form

The `VersionAwareLoginForm` component adapts its styling and behavior based on the version:

```tsx
<VersionAwareLoginForm version="corporate" redirectTo="/corporate/dashboard" />
```

### Social Logins

The `VersionAwareSocialLogins` component provides social login options with version-specific
redirects:

```tsx
<VersionAwareSocialLogins version="standard" redirectTo="/standard/dashboard" />
```

### Register Form

The `VersionAwareRegisterForm` component adapts its styling and behavior based on the version:

```tsx
<VersionAwareRegisterForm
  version="corporate"
  redirectTo="/corporate/dashboard"
/>
```

## Configuration Options

### Auth Service Options

The auth service accepts configuration options:

```typescript
type AuthRedirectOptions = {
  redirectTo?: string;
  version?: "standard" | "corporate";
};

signInWithEmail(email, password, {
  version: "corporate",
  redirectTo: "/corporate/dashboard/analytics",
});
```

### Protected Route Component Options

The `ProtectedRoute` component accepts a custom redirect URL:

```tsx
<ProtectedRoute redirectTo="/corporate/login">
  <DashboardContent />
</ProtectedRoute>
```

## Social Authentication

### Supported Providers

- Google
- GitHub

### Adding a New Provider

1. Configure the provider in your Supabase dashboard
2. Update the `signInWithProvider` function to support the new provider
3. Add the provider button to the `VersionAwareSocialLogins` component

### OAuth Callback Handling

The system includes a callback handler at `/auth/callback/route.ts` that processes OAuth redirects
and:

1. Exchanges the authorization code for a session
2. Updates user metadata with version information
3. Redirects to the appropriate dashboard
4. Sets analytics cookies for tracking

## Troubleshooting

### Common Issues

#### Redirect Loop

**Symptom**: User is caught in a redirect loop between login and dashboard

**Solution**: Check that the middleware is correctly identifying authenticated users. Verify that
cookies are being properly set and read.

#### Social Login Failure

**Symptom**: Social login redirects back without logging in

**Solution**: Check the OAuth configuration in Supabase and verify that the callback URL is correct.

#### Protected Route Still Accessible

**Symptom**: Unauthenticated users can access protected routes

**Solution**: Verify that the route is included in the `protectedPatterns` array and that the
middleware is running on that route.

#### Version-Specific Styling Not Applied

**Symptom**: Login/register forms don't show the correct styling for the version

**Solution**: Check that the version prop is being correctly passed to the version-aware components.

## Extending the System

### Adding Role-Based Access Control

To implement RBAC:

1. Add role information to user metadata during registration
2. Extend the middleware to check for specific roles
3. Create a `RoleProtectedRoute` component that checks for specific roles

### Custom Authentication Providers

To add a custom authentication provider:

1. Create a new authentication function in `auth-service.ts`
2. Add the provider to the login form
3. Update the callback handler to process the custom provider

### Session Management

To implement custom session behavior:

1. Modify the `checkAuthStatus` function to include additional checks
2. Update the `ProtectedRoute` component to handle session expiration
3. Add session refresh logic to maintain long-lived sessions

### Multi-Factor Authentication

To add MFA support:

1. Configure MFA in your Supabase project
2. Add MFA enrollment during registration or in user settings
3. Update the login flow to handle MFA challenges

---

## Additional Resources

- [Supabase Auth Documentation](<https://supabase.io/docs/guides/auth)>
- [Next.js Middleware Documentation](<https://nextjs.org/docs/advanced-features/middleware)>
- [OAuth 2.0 Flow Explained](<https://auth0.com/docs/authorization/flows)>

For further assistance, contact the development team at
[support@example.com](mailto:support@example.com).
