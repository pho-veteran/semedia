# UI Components

This directory contains shadcn/ui-style components built with Tailwind CSS and class-variance-authority.

## Available Components

### Button
A flexible button component with 6 variants and 4 sizes.

**Import:**
```tsx
import { Button } from "@/components/ui/Button"
// or
import { Button } from "@/components/ui"
```

**Quick Reference:**
```tsx
// Variants
<Button variant="default">Primary</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="destructive">Delete</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="link">Link</Button>

// Sizes
<Button size="sm">Small</Button>
<Button size="md">Medium</Button>
<Button size="lg">Large</Button>
<Button size="icon"><Icon /></Button>

// States
<Button loading>Loading...</Button>
<Button disabled>Disabled</Button>
```

See `Button.md` for full documentation.

## Design System

All components use CSS variables from `src/index.css`:
- Color tokens: `--primary`, `--secondary`, `--destructive`, etc.
- Transitions: `--transition-fast` (150ms), `--transition-normal` (250ms)
- Shadows: `--shadow-sm`, `--shadow-md`, `--shadow-lg`
- Radius: `--radius-sm`, `--radius-md`, `--radius-lg`

## Principles

1. **Owned components** - Copy/paste, not npm packages
2. **Tailwind utilities** - Styled with utility classes
3. **CSS variables** - Theme-aware via HSL tokens
4. **Type-safe** - Full TypeScript support
5. **Accessible** - WCAG AA compliant by default

## Adding New Components

1. Create component file in `src/components/ui/`
2. Use CVA for variants if needed
3. Export from `index.ts`
4. Add documentation in `.md` file
5. Create demo page for visual testing

## Testing

Visual testing via demo pages:
- `ButtonDemo.tsx` - Button component showcase

Run `npm run dev` and navigate to demo pages to verify components.
