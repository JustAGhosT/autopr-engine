# AutoPR Engine Design Tokens

Quick reference for the AutoPR Engine design system tokens.

## Usage

Import the tokens CSS file in your application:

```css
/* In your global CSS file */
@import "path/to/design-system/tokens.css";
```

Then reference tokens using CSS custom properties:

```css
.my-component {
  background-color: var(--color-primary-600);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
}
```

## Quick Reference

### Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--color-primary-600` | #2563eb | Primary buttons, links |
| `--color-secondary-600` | #9333ea | Gradient accents |
| `--color-alpha-500` | #f59e0b | Alpha branding |
| `--color-neutral-800` | #1e293b | Text (light mode) |
| `--color-neutral-200` | #e2e8f0 | Text (dark mode) |

### Spacing

| Token | Value |
|-------|-------|
| `--space-2` | 8px |
| `--space-4` | 16px |
| `--space-6` | 24px |
| `--space-8` | 32px |

### Typography

| Token | Value |
|-------|-------|
| `--font-size-sm` | 14px |
| `--font-size-base` | 16px |
| `--font-size-lg` | 18px |
| `--font-size-xl` | 20px |

### Borders

| Token | Value |
|-------|-------|
| `--radius-md` | 6px |
| `--radius-lg` | 8px |
| `--radius-full` | 9999px |

### Animations

| Token | Value |
|-------|-------|
| `--duration-150` | 150ms |
| `--duration-200` | 200ms |
| `--duration-300` | 300ms |

## Full Documentation

See [DESIGN_SYSTEM.md](../DESIGN_SYSTEM.md) for complete documentation.
