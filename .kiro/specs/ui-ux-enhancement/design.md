# Design Document: Semedia UI/UX Redesign (shadcn/ui)



## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Design System](#2-design-system)
   - 2.1 [Color Tokens (HSL)](#21-color-tokens-hsl)
   - 2.2 [Typography](#22-typography)
   - 2.3 [Spacing & Sizing](#23-spacing--sizing)
   - 2.4 [Shadows](#24-shadows)
   - 2.5 [Border Radius](#25-border-radius)
   - 2.6 [Motion & Timing](#26-motion--timing)
   - 2.7 [Z-Index Hierarchy](#27-z-index-hierarchy)
3. [Layout Architecture](#3-layout-architecture)
   - 3.1 [Global Shell](#31-global-shell)
   - 3.2 [Sidebar](#32-sidebar)
   - 3.3 [Main Content Area](#33-main-content-area)
   - 3.4 [Responsive Breakpoints](#34-responsive-breakpoints)
4. [Page Designs](#4-page-designs)
   - 4.1 [Dashboard](#41-dashboard)
   - 4.2 [Search Page](#42-search-page)
   - 4.3 [Library Page](#43-library-page)
   - 4.4 [Media Detail Page](#44-media-detail-page)
5. [Component Designs](#5-component-designs)
   - 5.1 [Button](#51-button)
   - 5.2 [Input](#52-input)
   - 5.3 [Card](#53-card)
   - 5.4 [Badge](#54-badge)
   - 5.5 [Upload Dropzone](#55-upload-dropzone)
   - 5.6 [Upload Queue Panel](#56-upload-queue-panel)
   - 5.7 [Media List Panel](#57-media-list-panel)
   - 5.8 [Search Result Card](#58-search-result-card)
   - 5.9 [Runtime Badge](#59-runtime-badge)
   - 5.10 [Data Table](#510-data-table)
   - 5.11 [Skeleton Screens](#511-skeleton-screens)
   - 5.12 [Empty States](#512-empty-states)
   - 5.13 [Error States](#513-error-states)
   - 5.14 [Toast / Notifications](#514-toast--notifications)
   - 5.15 [Dialog / Modal](#515-dialog--modal)
   - 5.16 [Error Boundary](#516-error-boundary)
6. [Interaction Patterns](#6-interaction-patterns)
   - 6.1 [Hover & Focus](#61-hover--focus)
   - 6.2 [Micro-Animations](#62-micro-animations)
   - 6.3 [Keyboard Shortcuts](#63-keyboard-shortcuts)
   - 6.4 [Dark Mode Toggle](#64-dark-mode-toggle)
7. [Accessibility Design](#7-accessibility-design)
8. [Icon System](#8-icon-system)
9. [index.css — Complete Token File](#9-indexcss--complete-token-file)

---

## 1. Design Philosophy

Semedia's redesign follows **shadcn/ui design principles**: components are owned (not overridden), styled with Tailwind utilities and CSS variables, and built on Radix UI accessibility primitives. The visual language is **minimalist and professional** — no glassmorphism, no decorative gradients, generous whitespace, and meaningful micro-interactions only.

**Four design rules that govern every decision:**

1. **Flat over decorative** — Subtle 1px borders, soft shadows, and muted backgrounds replace frosted glass effects.
2. **Semantic color only** — All colors are referenced via HSL CSS variables (`hsl(var(--primary))`), never hardcoded.
3. **Accessibility first** — Every interactive element is keyboard-navigable, has ARIA attributes, and meets WCAG AA contrast.
4. **Motion is functional** — Animations communicate state changes (150ms), not aesthetics.

---

## 2. Design System

### 2.1 Color Tokens (HSL)

All colors are defined as HSL channel values (no `hsl()` wrapper) in CSS variables, consumed via `hsl(var(--token))`.

#### Light Theme (`:root`)

| Token | HSL Value | Usage |
|---|---|---|
| `--background` | `0 0% 100%` | Page background |
| `--foreground` | `222.2 84% 4.9%` | Primary text |
| `--primary` | `222.2 47.4% 11.2%` | Brand, primary actions |
| `--primary-foreground` | `210 40% 98%` | Text on primary |
| `--secondary` | `210 40% 96.1%` | Secondary surfaces |
| `--secondary-foreground` | `222.2 47.4% 11.2%` | Text on secondary |
| `--muted` | `210 40% 96.1%` | Muted backgrounds |
| `--muted-foreground` | `215.4 16.3% 46.9%` | Secondary/hint text |
| `--accent` | `210 40% 96.1%` | Highlights, hover fills |
| `--accent-foreground` | `222.2 47.4% 11.2%` | Text on accent |
| `--destructive` | `0 84.2% 60.2%` | Delete, danger actions |
| `--destructive-foreground` | `210 40% 98%` | Text on destructive |
| `--border` | `214.3 31.8% 91.4%` | All borders |
| `--input` | `214.3 31.8% 91.4%` | Input borders |
| `--ring` | `222.2 84% 4.9%` | Focus rings |
| `--card` | `0 0% 100%` | Card background |
| `--card-foreground` | `222.2 84% 4.9%` | Text on cards |
| `--popover` | `0 0% 100%` | Popover background |
| `--popover-foreground` | `222.2 84% 4.9%` | Text on popovers |

#### Dark Theme (`[data-theme='dark']`)

| Token | HSL Value |
|---|---|
| `--background` | `222.2 84% 4.9%` |
| `--foreground` | `210 40% 98%` |
| `--primary` | `210 40% 98%` |
| `--primary-foreground` | `222.2 47.4% 11.2%` |
| `--secondary` | `217.2 32.6% 17.5%` |
| `--secondary-foreground` | `210 40% 98%` |
| `--muted` | `217.2 32.6% 17.5%` |
| `--muted-foreground` | `215 20.2% 65.1%` |
| `--accent` | `217.2 32.6% 17.5%` |
| `--accent-foreground` | `210 40% 98%` |
| `--destructive` | `0 62.8% 30.6%` |
| `--destructive-foreground` | `210 40% 98%` |
| `--border` | `217.2 32.6% 17.5%` |
| `--input` | `217.2 32.6% 17.5%` |
| `--ring` | `212.7 26.8% 83.9%` |
| `--card` | `222.2 84% 4.9%` |
| `--card-foreground` | `210 40% 98%` |

#### Status Colors (Upload Queue badges)

| Status | Color class | Tailwind equivalent |
|---|---|---|
| Uploading | Blue | `bg-blue-100 text-blue-700` |
| Processing | Orange | `bg-orange-100 text-orange-700` |
| Completed | Green | `bg-green-100 text-green-700` |
| Failed | Red | `bg-red-100 text-red-700` |

---

### 2.2 Typography

**Font stack (system):**
```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
             "Helvetica Neue", Arial, sans-serif;
```

**Scale:**

| Role | Size | Weight | Line Height | Tailwind |
|---|---|---|---|---|
| h1 | 2rem (32px) | 700 | 1.2 | `text-3xl font-bold leading-tight` |
| h2 | 1.5rem (24px) | 600 | 1.2 | `text-2xl font-semibold leading-tight` |
| h3 | 1.25rem (20px) | 600 | 1.2 | `text-xl font-semibold leading-tight` |
| h4 | 1.125rem (18px) | 500 | 1.2 | `text-lg font-medium leading-tight` |
| h5 | 1rem (16px) | 500 | 1.2 | `text-base font-medium leading-tight` |
| h6 | 0.875rem (14px) | 500 | 1.2 | `text-sm font-medium leading-tight` |
| body-lg | 1.125rem | 400 | 1.6 | `text-lg leading-relaxed` |
| body | 1rem | 400 | 1.6 | `text-base leading-relaxed` |
| body-sm | 0.875rem | 400 | 1.6 | `text-sm leading-relaxed` |
| caption | 0.75rem | 400 | 1.5 | `text-xs leading-normal` |
| code | 0.875rem | 400 | 1.5 | `text-sm font-mono` |

**Max line length:** `max-w-prose` (65ch) for body text blocks.

---

### 2.3 Spacing & Sizing

Tailwind spacing scale used throughout. Key values:

| Token | rem | px | Usage |
|---|---|---|---|
| `space-1` | 0.25rem | 4px | Tight gaps |
| `space-2` | 0.5rem | 8px | Inner padding sm |
| `space-3` | 0.75rem | 12px | Mobile content padding |
| `space-4` | 1rem | 16px | Standard padding, sidebar top |
| `space-6` | 1.5rem | 24px | Desktop section gap |
| `space-8` | 2rem | 32px | Section vertical rhythm |
| `space-12` | 3rem | 48px | Upload icon size |

**Content padding by breakpoint:**

| Breakpoint | Padding |
|---|---|
| Mobile (`< sm`) | `px-3` (12px) |
| Tablet (`md`) | `px-4` (16px) |
| Desktop (`lg+`) | `px-6` (24px) |

**Section gap by breakpoint:**

| Breakpoint | Gap |
|---|---|
| Mobile | `gap-4` (16px) |
| Desktop | `gap-6` (24px) |

**Touch targets:** minimum `min-h-[44px] min-w-[44px]` on all interactive elements for mobile.

---

### 2.4 Shadows

```css
--shadow-sm:  0 1px 2px 0 rgb(0 0 0 / 0.05);
--shadow-md:  0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
--shadow-lg:  0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
--shadow-xl:  0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
```

**Usage mapping:**
- Cards (default): `shadow-sm`
- Cards (hover): `shadow-md`
- Dropdowns / Popovers: `shadow-lg`
- Modals / Sheets: `shadow-xl`

---

### 2.5 Border Radius

| Token | Value | Usage |
|---|---|---|
| `--radius-sm` | `0.375rem` (6px) | Badges, chips, small elements |
| `--radius-md` | `0.5rem` (8px) | Inputs, buttons |
| `--radius-lg` | `0.75rem` (12px) | Cards |
| `--radius-xl` | `1rem` (16px) | Modals, sheets, large surfaces |

In Tailwind: `rounded-sm`, `rounded-md`, `rounded-lg`, `rounded-xl`.

---

### 2.6 Motion & Timing

```css
--transition-fast:   150ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-normal: 250ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-slow:   350ms cubic-bezier(0.4, 0, 0.2, 1);
--transition-theme:  300ms cubic-bezier(0.4, 0, 0.2, 1); /* dark mode switch */
```

| Duration | Used for |
|---|---|
| 150ms | Micro-interactions: hover, focus, button press |
| 250ms | Panel open/close, sidebar collapse, slide-in |
| 300ms | Theme color transition |
| 350ms | Page-level fade transitions |

**Reduced motion:** All animations wrapped in `@media (prefers-reduced-motion: no-preference)`. When reduced motion is preferred, transitions collapse to instant (`duration-0`) and keyframe animations are disabled.

---

### 2.7 Z-Index Hierarchy

| Layer | z-index | Elements |
|---|---|---|
| Base content | 0 | Cards, media items |
| Sticky sidebar | 10 | Sidebar on desktop |
| Dropdowns | 20 | Select menus, Dropdown Menu |
| Sticky headers | 30 | Filter toolbar on Library page |
| Modals / Dialogs | 50 | Dialog, confirmation modal |
| Sheets (mobile sidebar) | 60 | Sheet component |
| Toasts | 70 | Sonner toast stack |
| Tooltips | 80 | Tooltip component |

---

## 3. Layout Architecture

### 3.1 Global Shell

```
┌──────────────────────────────────────────────────────┐
│  Sidebar (250-280px, sticky)  │  Main content area   │
│                               │  max-w-[1400px]      │
│  [Logo]                       │  overflow-y-auto     │
│  [Nav items]                  │                      │
│                               │  [Page content]      │
│  [Theme toggle]               │                      │
│  [Settings]                   │                      │
└──────────────────────────────────────────────────────┘
```

**HTML structure:**
```html
<div class="flex h-screen overflow-hidden bg-background">
  <aside class="w-[260px] shrink-0 border-r border-border ...">
    <!-- Sidebar -->
  </aside>
  <main class="flex-1 overflow-y-auto">
    <div class="max-w-[1400px] mx-auto px-6 py-8">
      <!-- Page content -->
    </div>
  </main>
</div>
```

**On mobile (`< md`):** Sidebar hidden, replaced by Sheet triggered by hamburger button in top bar.

---

### 3.2 Sidebar

**Fixed width:** 260px desktop, full-screen Sheet on mobile.

**Anatomy (top → bottom):**

```
┌─────────────────────────┐
│ ⬛ Semedia              │  ← Logo + brand (h-16, px-4, border-b)
├─────────────────────────┤
│                         │
│ ⬛ Dashboard        [3] │  ← Active: bg-accent border-l-2 border-primary
│    Search               │  ← Inactive: hover:bg-accent/50
│    Library              │          │
│                         │
│ ·  ·  ·  ·  ·  ·  ·  · │  ← Spacer (mt-auto, push to bottom)
│                         │
│ ☀/🌙 Theme  [GPU: RTX] │  ← Footer section (px-4 py-3, border-t)
└─────────────────────────┘
```

**Key Design:**
- **Simple navigation** = No section labels or dividers
- **Clean layout** = Just nav items with icons
- **Footer section** = Theme toggle + runtime badge
- **Upload badge** = Colored badge with count on Dashboard

**Active nav item style:**
```
bg-accent text-accent-foreground border-l-2 border-primary font-medium
```

**Inactive nav item style:**
```
text-muted-foreground hover:bg-accent hover:text-accent-foreground
transition-colors duration-150
```

**Upload queue badge** (on Dashboard nav item):
```html
<Badge variant="secondary" className="ml-auto text-xs bg-blue-100 text-blue-700">
  {uploadCount}
</Badge>
```

**Complete sidebar component:**
```html
<aside className="w-[260px] shrink-0 border-r border-border bg-card flex flex-col h-screen">
  {/* Logo / Brand */}
  <div className="h-16 flex items-center px-4 border-b border-border">
    <div className="flex items-center gap-2">
      <div className="w-8 h-8 bg-primary rounded-md" />
      <span className="font-semibold text-lg">Semedia</span>
    </div>
  </div>
  
  {/* Navigation */}
  <nav className="flex-1 overflow-y-auto py-4">
    <div className="space-y-1 px-3">
      <NavItem
        to="/"
        icon={<LayoutDashboard size={20} />}
        label="Dashboard"
        badge={uploadCount > 0 ? uploadCount : null}
        active={pathname === '/'}
      />
      <NavItem
        to="/search"
        icon={<Search size={20} />}
        label="Search"
        active={pathname === '/search'}
      />
      <NavItem
        to="/library"
        icon={<Library size={20} />}
        label="Library"
        active={pathname === '/library'}
      />
      <NavItem
        to="/settings"
        icon={<Settings size={20} />}
        label="Settings"
        active={pathname === '/settings'}
      />
    </div>
  </nav>
  
  {/* Footer section */}
  <div className="border-t border-border">
    <div className="p-4 flex items-center justify-between">
      <Button
        variant="ghost"
        size="icon"
        onClick={toggleTheme}
        aria-label="Toggle theme"
      >
        {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
      </Button>
      <RuntimeBadge />
    </div>
  </div>
</aside>
```

**NavItem component:**
```tsx
function NavItem({ to, icon, label, badge, active }) {
  return (
    <Link
      to={to}
      className={cn(
        "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
        active
          ? "bg-accent text-accent-foreground border-l-2 border-primary font-medium"
          : "text-muted-foreground hover:bg-accent/50 hover:text-accent-foreground"
      )}
    >
      {icon}
      <span className="flex-1">{label}</span>
      {badge && (
        <Badge variant="secondary" className="text-xs bg-blue-100 text-blue-700">
          {badge}
        </Badge>
      )}
    </Link>
  )
}
```

**Collapse animation:** `transition-[width] duration-250 ease-[cubic-bezier(0.4,0,0.2,1)]`

---

### 3.3 Main Content Area

- `flex-1 overflow-y-auto` — scrolls independently of sidebar
- `max-w-[1400px] mx-auto` — centered on large screens
- Content padding: `px-6 py-8` (desktop), `px-4 py-6` (tablet), `px-3 py-4` (mobile)

---

### 3.4 Responsive Breakpoints

| Name | Width | Behavior |
|---|---|---|
| `sm` | 640px | Grids: 1 column |
| `md` | 768px | Grids: 2 columns; sidebar collapses |
| `lg` | 1024px | Grids: 4 columns; sidebar visible |
| `xl` | 1280px | Max content width kicks in |

**Tailwind grid pattern used throughout:**
```
grid-cols-1 sm:grid-cols-2 lg:grid-cols-4
```

---

## 4. Page Designs

### 4.1 Dashboard

**URL:** `/`

**Layout (desktop `lg+`):**
```
┌────────────────────────────────────────────────────────────────┐
│ Semedia                                          │
│ Upload and manage your semantic media library                  │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Upload Dropzone (Full Width, Prominent)                 │  │
│  │  [Dashed border, 180px height, centered content]         │  │
│  │  ☁ Drop files here or click to browse                   │  │
│  │  PNG, JPG, WEBP, GIF, BMP · MP4, WebM, MOV              │  │
│  │  [Browse Files]                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Upload Queue (3)                        [Collapse ▼]    │  │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ← Horizontal      │  │
│  │  │🔵 65%  │  │🟠 80%  │  │🟢 100% │     scroll          │  │
│  │  │video   │  │image   │  │photo   │                     │  │
│  │  │[×]     │  │[×]     │  │        │                     │  │
│  │  └────────┘  └────────┘  └────────┘                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Recent Media                    [View All →] [Refresh]  │  │
│  │  ─────────────────────────────────────────────────────── │  │
│  │  [Grid: 4 cols lg, 3 cols md, 2 cols sm, 1 col xs]      │  │
│  │  [Card] [Card] [Card] [Card]                             │  │
│  │  [Card] [Card] [Card] [Card]                             │  │
│  │  [Card] [Card] [Card] [Card]                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

**Layout (mobile/tablet `< lg`):** Single column, stacked vertically. Upload queue collapses to vertical list on mobile.

**Key Design Decisions:**
- **Full-width upload dropzone** = more prominent, easier drag target
- **Horizontal upload queue** = compact, browser-download-style UX
- **Grid layout for media** = better visual scanning than vertical list
- **12 items in 3 rows** = balanced, fills space well

**Hero section:**
```html
<div class="flex items-center justify-between mb-8">
  <div>
    <h1 class="text-3xl font-bold text-foreground">Semedia</h1>
    <p class="text-muted-foreground mt-1">Upload and manage your semantic media library</p>
  </div>
  <RuntimeBadge />
</div>
```

**Content layout:**
```html
<div class="flex flex-col gap-6">
  {/* Full-width upload dropzone */}
  <UploadDropzone className="min-h-[180px]" />
  
  {/* Horizontal upload queue (only when active) */}
  {uploads.length > 0 && (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Upload Queue ({uploads.length})</CardTitle>
        <Button variant="ghost" size="sm" onClick={toggleCollapse}>
          <ChevronDown className={collapsed ? '' : 'rotate-180'} />
        </Button>
      </CardHeader>
      {!collapsed && (
        <CardContent>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {uploads.map(upload => (
              <UploadCard key={upload.id} upload={upload} />
            ))}
          </div>
        </CardContent>
      )}
    </Card>
  )}
  
  {/* Recent media grid */}
  <Card>
    <CardHeader className="flex flex-row items-center justify-between">
      <CardTitle>Recent Media</CardTitle>
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" onClick={refresh}>
          <RefreshCw size={16} />
        </Button>
        <Button variant="link" asChild>
          <Link to="/library">View All →</Link>
        </Button>
      </div>
    </CardHeader>
    <CardContent>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {mediaItems.slice(0, 12).map(item => (
          <MediaCard key={item.id} media={item} />
        ))}
      </div>
    </CardContent>
  </Card>
</div>
```

**Responsive breakpoints:**
- **xl (1280px+)**: 4 columns, full spacing
- **lg (1024px)**: 4 columns, standard spacing
- **md (768px)**: 3 columns, upload height 160px
- **sm (640px)**: 2 columns, upload height 140px
- **xs (<640px)**: 1 column, upload height 120px

---

### 4.2 Search Page

**URL:** `/search`

**Layout:**
```
┌────────────────────────────────────────────────────────────────┐
│ Search Media                                                   │
│ Find images and videos using text or image queries             │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Search                                                   │  │
│  │  ──────────────────────────────────────────────────────  │  │
│  │  [Tabs: Text Search | Image Search]                      │  │
│  │                                                           │  │
│  │  [Text Search Tab Active]                                │  │
│  │  ┌────────────────────────────────────────┐  [Search]   │  │
│  │  │ Search for images and videos...        │             │  │
│  │  └────────────────────────────────────────┘             │  │
│  │  Recent: sunset · cat video · landscape                  │  │
│  │                                                           │  │
│  │  [Image Search Tab - when selected]                      │  │
│  │  [Dashed drop area with preview]  [Choose image]        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Filters & Sort                                          │  │
│  │  Type: [All ▼]  Score: [≥ 0.7 ▼]  Sort: [Relevance ▼]  │  │
│  │  Active: [Type: Image ×] [Score: ≥0.8 ×]               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  12 results for "sunset"                                       │
│  ─────────────────────────────────────────────────────────    │
│  [Card] [Card] [Card] [Card]                                  │
│  [Card] [Card] [Card] [Card]                                  │
│  [Card] [Card] [Card] [Card]                                  │
│                                                                │
│  [Load more] or [Pagination]                                  │
└────────────────────────────────────────────────────────────────┘
```

**Key Design Decisions:**
- **Tabs unify search modes** = cleaner, less overwhelming than separate cards
- **Recent searches inline** = faster access, no dropdown needed
- **Dedicated filter section** = clear separation from search input
- **Active filter chips** = visual feedback of current filters
- **Results with context** = count + query summary before grid

**Search component with tabs:**
```html
<Card>
  <CardHeader>
    <CardTitle>Search</CardTitle>
  </CardHeader>
  <CardContent>
    <Tabs defaultValue="text" className="w-full">
      <TabsList className="grid w-full grid-cols-2 mb-4">
        <TabsTrigger value="text">Text Search</TabsTrigger>
        <TabsTrigger value="image">Image Search</TabsTrigger>
      </TabsList>
      
      <TabsContent value="text" className="space-y-3">
        <div className="flex gap-2">
          <Input
            placeholder="Search for images and videos..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
          <Button onClick={handleSearch}>Search</Button>
        </div>
        {recentSearches.length > 0 && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>Recent:</span>
            {recentSearches.map(term => (
              <Button
                key={term}
                variant="link"
                size="sm"
                onClick={() => setQuery(term)}
              >
                {term}
              </Button>
            ))}
          </div>
        )}
      </TabsContent>
      
      <TabsContent value="image" className="space-y-3">
        <ImageDropzone onImageSelect={handleImageSearch} />
      </TabsContent>
    </Tabs>
  </CardContent>
</Card>
```

**Filter bar:**
```html
<Card>
  <CardContent className="pt-6">
    <div className="flex flex-wrap items-center gap-3 mb-3">
      <Select value={typeFilter} onValueChange={setTypeFilter}>
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="Type" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All</SelectItem>
          <SelectItem value="image">Images</SelectItem>
          <SelectItem value="video">Videos</SelectItem>
        </SelectContent>
      </Select>
      
      <Select value={scoreFilter} onValueChange={setScoreFilter}>
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="Score" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="0.5">≥ 0.5</SelectItem>
          <SelectItem value="0.7">≥ 0.7</SelectItem>
          <SelectItem value="0.9">≥ 0.9</SelectItem>
        </SelectContent>
      </Select>
      
      <Select value={sortBy} onValueChange={setSortBy}>
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="Sort" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="relevance">Relevance</SelectItem>
          <SelectItem value="date">Date</SelectItem>
          <SelectItem value="size">Size</SelectItem>
        </SelectContent>
      </Select>
    </div>
    
    {/* Active filter chips */}
    {activeFilters.length > 0 && (
      <div className="flex flex-wrap gap-2">
        {activeFilters.map(filter => (
          <Badge key={filter.key} variant="secondary" className="gap-1">
            {filter.label}
            <button onClick={() => removeFilter(filter.key)}>
              <X size={12} />
            </button>
          </Badge>
        ))}
      </div>
    )}
  </CardContent>
</Card>
```

**Debounce:** 300ms on text input before triggering search query.

---

### 4.3 Library Page

**URL:** `/library`

**Layout:**
```
┌────────────────────────────────────────────────────────────────┐
│ Media Library                                                  │
│ 156 items                                                      │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  [🔍 Search library...]  [Type ▼] [Status ▼] [Sort ▼]   │  │
│  │  [View: ⊞ Grid] [≡ List]                                │  │
│  │  Active: [Type: Image ×] [Status: Completed ×]          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  [Bulk toolbar: 3 selected] [Delete] [Download] [Cancel]      │
│                                                                │
│  [☐ Card] [☐ Card] [☐ Card] [☐ Card]                         │
│  [☐ Card] [☐ Card] [☐ Card] [☐ Card]                         │
│  [☐ Card] [☐ Card] [☐ Card] [☐ Card]                         │
│  [☐ Card] [☐ Card] [☐ Card] [☐ Card]                         │
│  [☐ Card] [☐ Card] [☐ Card] [☐ Card]                         │
│  [☐ Card] [☐ Card] [☐ Card] [☐ Card]                         │
│                                                                │
│  Showing 1-24 of 156                                          │
│  [← Previous]  Page 1 of 7  [Next →]  [24 per page ▼]        │
└────────────────────────────────────────────────────────────────┘
```

**Key Design Decisions:**
- **Horizontal filter bar** = more space for content, no sidebar
- **Inline search + filters** = unified control panel
- **View toggle prominent** = easy switching between grid/list
- **Active filters as chips** = clear visual state
- **Bulk toolbar slides in** = appears only when items selected
- **Centered pagination** = clear navigation

**Filter toolbar:**
```html
<Card className="mb-6">
  <CardContent className="pt-6">
    <div className="flex flex-col gap-4">
      {/* Top row: Search + Filters + View toggle */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex-1 min-w-[200px]">
          <Input
            placeholder="Search library..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full"
          />
        </div>
        
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-[120px]">
            <SelectValue placeholder="Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="image">Images</SelectItem>
            <SelectItem value="video">Videos</SelectItem>
          </SelectContent>
        </Select>
        
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="processing">Processing</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
          </SelectContent>
        </Select>
        
        <Select value={sortBy} onValueChange={setSortBy}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Sort" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="newest">Newest</SelectItem>
            <SelectItem value="oldest">Oldest</SelectItem>
            <SelectItem value="name">Name A-Z</SelectItem>
            <SelectItem value="size">Size</SelectItem>
          </SelectContent>
        </Select>
        
        <div className="flex items-center gap-1 border rounded-md">
          <Button
            variant={view === 'grid' ? 'secondary' : 'ghost'}
            size="icon"
            onClick={() => setView('grid')}
          >
            <LayoutGrid size={16} />
          </Button>
          <Button
            variant={view === 'list' ? 'secondary' : 'ghost'}
            size="icon"
            onClick={() => setView('list')}
          >
            <List size={16} />
          </Button>
        </div>
      </div>
      
      {/* Bottom row: Active filter chips */}
      {activeFilters.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-muted-foreground">Active:</span>
          {activeFilters.map(filter => (
            <Badge key={filter.key} variant="secondary" className="gap-1">
              {filter.label}
              <button onClick={() => removeFilter(filter.key)}>
                <X size={12} />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  </CardContent>
</Card>
```

**Bulk actions toolbar (appears when items selected):**
```html
{selectedItems.length > 0 && (
  <Card className="mb-4 border-primary">
    <CardContent className="py-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">
          {selectedItems.length} item{selectedItems.length > 1 ? 's' : ''} selected
        </span>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleBulkDownload}>
            <Download size={16} className="mr-1" />
            Download
          </Button>
          <Button variant="destructive" size="sm" onClick={handleBulkDelete}>
            <Trash2 size={16} className="mr-1" />
            Delete
          </Button>
          <Button variant="ghost" size="sm" onClick={clearSelection}>
            Cancel
          </Button>
        </div>
      </div>
    </CardContent>
  </Card>
)}
```

**List view** (toggle): renders as Data Table (see §5.10).

---

### 4.4 Media Detail Page

**URL:** `/media/:id` | `/media/:id?start=:ts`

**Layout for Video Media (desktop - 2 columns):**
```
┌────────────────────────────────────────────────────────────────┐
│ ← Back to Library          Dashboard > Library > Media Detail  │
├──────────────────────────────┬─────────────────────────────────┤
│                              │                                 │
│  filename.mp4                │  Video Scenes (8)               │
│  [Completed] Video · 3:42    │  ───────────────────────────    │
│  [Download] [Share] [Delete] │                                 │
│                              │  ┌───────────────────────────┐  │
│  ┌────────────────────────┐  │  │ [Scene 1 thumbnail]       │  │
│  │                        │  │  │ 0:00 - 0:15               │  │
│  │   Video Player         │  │  │ Caption for scene 1...    │  │
│  │   (16:9 ratio)         │  │  └───────────────────────────┘  │
│  │                        │  │                                 │
│  └────────────────────────┘  │  ┌───────────────────────────┐  │
│                              │  │ [Scene 2 thumbnail]       │  │
│  Caption                     │  │ 0:15 - 0:30               │  │
│  ──────────────────────────  │  │ Caption for scene 2...    │  │
│  A beautiful sunset over     │  └───────────────────────────┘  │
│  the ocean with waves...     │                                 │
│                              │  ┌───────────────────────────┐  │
│                              │  │ [Scene 3 thumbnail]       │  │
│                              │  │ 0:30 - 0:45               │  │
│                              │  │ Caption for scene 3...    │  │
│                              │  └───────────────────────────┘  │
│                              │                                 │
│                              │  (Vertical scroll for more)     │
│                              │                                 │
└──────────────────────────────┴─────────────────────────────────┘
```

**Layout for Image Media (desktop - single column):**
```
┌────────────────────────────────────────────────────────────────┐
│ ← Back to Library          Dashboard > Library > Media Detail  │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  filename.jpg                                                  │
│  [Completed]  Image · 2.1 MB · 1920×1080 · 1 hour ago         │
│  [Download] [Share] [Delete]                                   │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                                                           │  │
│  │              Image Preview (full resolution)             │  │
│  │              [Click to zoom]                             │  │
│  │                                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  Caption                                                       │
│  ──────────────────────────────────────────────────────────   │
│  A beautiful landscape with mountains in the background...     │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Mobile layout:** Single column - all sections stack vertically (header, player, caption, scenes list).

**Key Design Decisions:**
- **2-column layout for videos** = Player + caption on left (60%), scenes list on right (40%)
- **Vertical scrollable scenes** = Better for many scenes, easier scanning than horizontal
- **Single column for images** = No scenes section, full-width preview
- **Metadata in header** = Quick access to actions and info
- **Scene cards** = Larger thumbnails with captions visible

**Component implementation:**

```tsx
function MediaDetailPage() {
  const { mediaId } = useParams()
  const { data: mediaDetail, isLoading } = useQuery(['media', mediaId])
  
  if (isLoading) return <MediaDetailSkeleton />
  
  const isVideo = mediaDetail.media_type === 'video'
  
  return (
    <div className="max-w-7xl mx-auto">
      {/* Breadcrumb */}
      <div className="mb-6">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)}>
          <ArrowLeft size={16} className="mr-1" />
          Back to Library
        </Button>
        <div className="text-sm text-muted-foreground mt-2">
          Dashboard &gt; Library &gt; Media Detail
        </div>
      </div>
      
      {/* 2-column layout for videos, single column for images */}
      <div className={cn(
        "grid gap-6",
        isVideo ? "lg:grid-cols-[1.5fr_1fr]" : "grid-cols-1"
      )}>
        {/* Left column: Media + Caption */}
        <div className="space-y-6">
          {/* Metadata header */}
          <div className="space-y-3">
            <h1 className="text-2xl font-bold text-foreground truncate">
              {mediaDetail.original_filename}
            </h1>
            
            <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
              <Badge variant={getStatusVariant(mediaDetail.status)}>
                {mediaDetail.status}
              </Badge>
              <span>·</span>
              <span>{mediaDetail.media_type}</span>
              <span>·</span>
              <span>{formatFileSize(mediaDetail.file_size)}</span>
              <span>·</span>
              {isVideo ? (
                <span>{formatDuration(mediaDetail.duration)}</span>
              ) : (
                <span>{mediaDetail.width}×{mediaDetail.height}</span>
              )}
              <span>·</span>
              <span>{formatRelativeTime(mediaDetail.uploaded_at)}</span>
            </div>
            
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={handleDownload}>
                <Download size={16} className="mr-1" />
                Download
              </Button>
              <Button variant="outline" size="sm" onClick={handleShare}>
                <Link size={16} className="mr-1" />
                Share
              </Button>
              <Button variant="destructive" size="sm" onClick={handleDelete}>
                <Trash2 size={16} className="mr-1" />
                Delete
              </Button>
            </div>
          </div>
          
          {/* Media preview */}
          <Card>
            <CardContent className="p-0">
              {isVideo ? (
                <div className="relative w-full aspect-video">
                  <video
                    ref={videoRef}
                    src={mediaDetail.file}
                    controls
                    className="w-full h-full object-contain bg-black rounded-lg"
                    onTimeUpdate={handleTimeUpdate}
                  />
                </div>
              ) : (
                <div className="relative w-full">
                  <img
                    src={mediaDetail.file}
                    alt={mediaDetail.original_filename}
                    className="w-full h-auto object-contain rounded-lg cursor-zoom-in"
                    onClick={handleZoom}
                  />
                </div>
              )}
            </CardContent>
          </Card>
          
          {/* Caption */}
          <Card>
            <CardHeader>
              <CardTitle>Caption</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-foreground leading-relaxed">
                {mediaDetail.caption || 'No caption available'}
              </p>
            </CardContent>
          </Card>
        </div>
        
        {/* Right column: Video Scenes (only for videos) */}
        {isVideo && mediaDetail.scenes?.length > 0 && (
          <div>
            <Card className="sticky top-6">
              <CardHeader>
                <CardTitle>Video Scenes ({mediaDetail.scenes.length})</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-[calc(100vh-200px)] overflow-y-auto pr-2">
                  {mediaDetail.scenes.map((scene) => (
                    <button
                      key={scene.id}
                      onClick={() => seekTo(scene.start_time)}
                      className="w-full rounded-lg overflow-hidden border border-border hover:border-primary hover:shadow-md transition-all focus:outline-none focus:ring-2 focus:ring-ring text-left"
                    >
                      <div className="relative aspect-video">
                        <img
                          src={scene.thumbnail_image}
                          alt={`Scene ${scene.scene_index + 1}`}
                          className="w-full h-full object-cover"
                        />
                        <div className="absolute top-2 left-2 bg-black/70 text-white text-xs px-2 py-1 rounded-md font-medium">
                          Scene {scene.scene_index + 1}
                        </div>
                      </div>
                      <div className="p-3 bg-card">
                        <div className="text-xs text-muted-foreground font-medium mb-1">
                          {formatTime(scene.start_time)} – {formatTime(scene.end_time)}
                        </div>
                        <p className="text-sm text-foreground line-clamp-2">
                          {scene.caption}
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
```

**Responsive behavior:**
- **Desktop (lg+)**: 2 columns for videos (60/40 split), single column for images
- **Tablet/Mobile (<lg)**: Single column, scenes list below caption
- **Scenes panel**: Sticky on desktop, scrollable list, max-height with overflow

**Share action:** Copies media URL to clipboard, shows success toast.

**Delete action:** Opens confirmation Dialog before calling `DELETE /api/v1/media/{id}/`.

---

---

## 5. Component Designs

### 5.1 Button

**Variants and styles:**

| Variant | Background | Text | Border | Usage |
|---|---|---|---|---|
| `default` | `bg-primary` | `text-primary-foreground` | none | Primary CTA |
| `secondary` | `bg-secondary` | `text-secondary-foreground` | none | Secondary actions |
| `destructive` | `bg-destructive` | `text-destructive-foreground` | none | Delete, danger |
| `outline` | transparent | `text-foreground` | `border-border` | Tertiary actions |
| `ghost` | transparent | `text-foreground` | none | Inline actions |
| `link` | transparent | `text-primary underline` | none | Text links |

**Sizes:**

| Size | Height | Padding | Font size |
|---|---|---|---|
| `sm` | 36px | `px-3` | `text-sm` |
| `md` (default) | 40px | `px-4` | `text-sm` |
| `lg` | 44px | `px-8` | `text-base` |
| `icon` | 40×40px | `p-2` | — |

**States:**
- Hover: `hover:opacity-90` (default/destructive), `hover:bg-accent` (ghost/outline)
- Focus: `focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2`
- Pressed: `active:scale-[0.98] transition-transform duration-150`
- Disabled: `disabled:opacity-50 disabled:pointer-events-none`
- Loading: spinner replaces leading icon, text unchanged, `disabled`

---

### 5.2 Input

```html
<input class="
  flex h-10 w-full rounded-md border border-input
  bg-background px-3 py-2
  text-sm text-foreground
  placeholder:text-muted-foreground
  focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring
  disabled:cursor-not-allowed disabled:opacity-50
  transition-colors duration-150
" />
```

**With error state:** add `border-destructive focus-visible:ring-destructive`

**With success state:** add `border-green-500 focus-visible:ring-green-500`

**Error message below input:**
```html
<p class="text-xs text-destructive mt-1" role="alert">{errorMessage}</p>
```

---

### 5.3 Card

```html
<div class="rounded-lg border border-border bg-card text-card-foreground shadow-sm">
  <div class="p-6 flex flex-col space-y-1.5">  <!-- CardHeader -->
    <h3 class="text-lg font-semibold leading-none">Title</h3>
    <p class="text-sm text-muted-foreground">Description</p>
  </div>
  <div class="p-6 pt-0">  <!-- CardContent -->
    ...
  </div>
  <div class="p-6 pt-0 flex items-center">  <!-- CardFooter -->
    ...
  </div>
</div>
```

**Hover (for clickable cards):** `hover:shadow-md hover:border-border/80 transition-shadow duration-150`

---

### 5.4 Badge

| Variant | Style | Usage |
|---|---|---|
| `default` | `bg-primary text-primary-foreground` | General labels |
| `secondary` | `bg-secondary text-secondary-foreground` | Neutral tags |
| `destructive` | `bg-destructive text-destructive-foreground` | Error status |
| `outline` | `border border-border text-foreground` | Filter chips |

```html
<span class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ...">
  Label
</span>
```

---

### 5.5 Upload Dropzone

**Visual anatomy:**

```
┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐
  (border-dashed border-2 border-border, min-h-[200px])
│                                                  │
│              ☁  (48px, text-muted-foreground)    │
│        Drop files here or click to browse        │
│    PNG, JPG, WEBP, GIF, BMP · MP4, WebM, MOV    │
│                                                  │
│               [Browse Files]                     │
│                                                  │
└ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘
```

**Drag-over state:** `border-primary bg-primary/5` — blue tint fills the area.

**Validation errors:** `toast.error("File type not supported")` via Sonner.

**Size warning:** `toast.warning("File exceeds 100MB — upload may be slow")`.

---

### 5.6 Upload Queue Panel

**Only rendered when `uploads.length > 0`.**

```
┌─────────────────────────────────────────────┐
│ Upload Queue                     (Card)      │
├─────────────────────────────────────────────┤
│ [🔵 Uploading]  video.mp4  42 MB            │
│ ████████░░░░░░  65%                [Cancel] │
├─────────────────────────────────────────────┤
│ [🟠 Processing] image.jpg  2.1 MB           │
│ ████████████░░  80%                [Cancel] │
├─────────────────────────────────────────────┤
│ [🟢 Completed]  photo.png  1.4 MB           │
│ ████████████████ 100%                       │
├─────────────────────────────────────────────┤
│ [🔴 Failed]     corrupt.mp4  8 MB           │
│ ░░░░░░░░░░░░░░  0%                  [Retry] │
└─────────────────────────────────────────────┘
```

**Item slide-in animation:**
```css
@keyframes slideInFromTop {
  from { transform: translateY(-8px); opacity: 0; }
  to   { transform: translateY(0);    opacity: 1; }
}
.upload-item { animation: slideInFromTop 250ms cubic-bezier(0.4,0,0.2,1); }
```

**Auto-remove completed:** `setTimeout(() => removeItem(id), 5000)` after status = `completed`.

---

### 5.7 Media List Panel

**Used on Dashboard (12 items, vertical list).**

Each item:
```
┌─────────────────────────────────────────────────────┐
│ [120px thumb]  filename.jpg                         │
│                [Completed]  Image · 2.1 MB · 2d ago │
│                Caption text here, truncated...      │
└─────────────────────────────────────────────────────┘
```

- Thumbnail: `w-[120px] h-[80px] object-cover rounded-md`
- Video: gray placeholder with `<Film />` icon + scene count badge
- Hover: `hover:bg-accent/50 hover:shadow-sm transition-all duration-150 cursor-pointer`
- Card header: `"Recent Media"` + `<Button variant="ghost" size="icon"><RefreshCw /></Button>` + `"View All →"` link

---

### 5.8 Search Result Card

```
┌──────────────────────────────┐
│ [score: 94%]    [0:12–0:31]  │  ← chips overlaid on thumbnail
│                              │
│   16:10 aspect ratio image   │
│                              │
├──────────────────────────────┤
│ filename.mp4                 │
│ [Scene]  Caption excerpt...  │
└──────────────────────────────┘
```

- Aspect ratio: `aspect-[16/10]` on thumbnail container
- Score chip: `absolute top-2 left-2 bg-black/60 text-white text-xs px-2 py-0.5 rounded-full`
- Time chip: `absolute top-2 right-2 bg-black/60 text-white text-xs px-2 py-0.5 rounded-full`
- Hover: `hover:scale-[1.02] hover:shadow-md transition-all duration-150`
- Click: navigate to `/media/:media_id`

---

### 5.9 Runtime Badge

Displays in Dashboard hero and Sidebar bottom.

```
[🟢 GPU: RTX 4090]   or   [🟡 CPU]   or   [Connecting...]
```

```html
<Badge variant="outline" class="gap-1.5 text-xs">
  <span class="h-2 w-2 rounded-full bg-green-500" />
  GPU: RTX 4090
</Badge>
```

Refetch interval: 30 seconds via `useQuery(['runtime'], { refetchInterval: 30000 })`.

---

### 5.10 Data Table

**Used in Library page (list view).**

| Column | Width | Sortable |
|---|---|---|
| ☐ (checkbox) | 40px | — |
| Thumbnail | 80px | No |
| Filename | flex-1 | Yes |
| Type | 80px | Yes |
| Size | 90px | Yes |
| Status | 110px | Yes |
| Date | 120px | Yes |
| Actions | 80px | No |

**Column header (sortable):**
```html
<button class="flex items-center gap-1 hover:text-foreground transition-colors">
  Filename <ArrowUpDown size={14} />
</button>
```

**Mobile behavior:** Collapse `Type`, `Size`, `Date` columns at `< md`. Show only Thumbnail, Filename, Status, Actions.

---

### 5.11 Skeleton Screens

**Skeleton component base:**
```html
<div class="animate-pulse rounded-md bg-muted" />
```

**Media list item skeleton:**
```html
<div class="flex gap-3 p-3">
  <Skeleton class="h-[80px] w-[120px] rounded-md" />
  <div class="flex-1 space-y-2">
    <Skeleton class="h-4 w-3/4" />
    <Skeleton class="h-3 w-1/2" />
    <Skeleton class="h-3 w-full" />
  </div>
</div>
```

**Search result card skeleton:** Full card with `aspect-[16/10]` skeleton for thumbnail + 3 lines below.

**Minimum display time:** 200ms — use `setTimeout` to ensure skeleton doesn't flash on fast responses.

---

### 5.12 Empty States

**Standard empty state pattern:**
```html
<div class="flex flex-col items-center justify-center py-16 text-center">
  <div class="rounded-full bg-muted p-4 mb-4">
    <ImageOff class="text-muted-foreground" size={32} />
  </div>
  <h3 class="text-lg font-semibold text-foreground mb-1">No media yet</h3>
  <p class="text-sm text-muted-foreground mb-4 max-w-sm">
    Upload your first image or video to get started.
  </p>
  <Button onClick={openUpload}>Upload media</Button>
</div>
```

**Context-specific icons and copy:**

| Context | Icon | Title | CTA |
|---|---|---|---|
| Empty library | `ImageOff` | "No media yet" | "Upload media" |
| No search results | `SearchX` | "No results found" | "Try different terms" |
| No scenes | `Film` | "No scenes detected" | (none) |

---

### 5.13 Error States

**Inline error (page-level):**
```html
<div class="flex flex-col items-center justify-center py-16 text-center">
  <AlertCircle class="text-destructive mb-4" size={40} />
  <h3 class="text-lg font-semibold">Something went wrong</h3>
  <p class="text-sm text-muted-foreground mt-1 mb-4">
    Failed to load media. Please try again.
  </p>
  <Button variant="outline" onClick={retry}>Try again</Button>
</div>
```

**Error banner (search failure):**
```html
<Alert variant="destructive">
  <AlertCircle size={16} />
  <AlertTitle>Search failed</AlertTitle>
  <AlertDescription>
    Unable to connect to search service.
    <Button variant="link" size="sm">Try again</Button>
  </AlertDescription>
</Alert>
```

**Rules:** Never show stack traces. Always provide a recovery action.

---

### 5.14 Toast / Notifications

**Library:** Sonner (`<Toaster />` mounted in `App.tsx` root).

| Event | Type | Duration | Action |
|---|---|---|---|
| Upload complete | success | 5s | — |
| Upload failed | error | 10s | Retry |
| Delete complete | success | 5s | Undo |
| API error | error | 10s | — |

**Usage:**
```ts
toast.success("Upload complete")
toast.error("Upload failed", { action: { label: "Retry", onClick: retry } })
toast.success("Deleted", { action: { label: "Undo", onClick: undo } })
```

**Behavior:** Stacks vertically (bottom-right), pauses on hover, has close button.

---

### 5.15 Dialog / Modal

**Delete confirmation:**
```
┌──────────────────────────────────────┐
│ Delete media?                        │
│                                      │
│ This action cannot be undone.        │
│ "filename.mp4" will be permanently   │
│ deleted from your library.           │
│                                      │
│            [Cancel]  [Delete]        │
└──────────────────────────────────────┘
```

- Focus trapped inside Dialog when open
- `Escape` closes it
- Destructive button: `variant="destructive"`
- `aria-labelledby` and `aria-describedby` set correctly

---

### 5.16 Error Boundary

**File:** `src/components/ErrorBoundary.tsx` — class component wrapping the entire app in `App.tsx`.

**UI when error is caught:**
```
┌──────────────────────────────────────┐
│                                      │
│    ⚠  (AlertTriangle, destructive)  │
│                                      │
│    Something went wrong              │
│    An unexpected error occurred.     │
│    Please reload the page.           │
│                                      │
│         [Reload page]                │
│                                      │
└──────────────────────────────────────┘
```

- Logs `error` and `errorInfo` to `console.error`
- Never exposes stack trace to users
- Button calls `window.location.reload()`

---

## 6. Interaction Patterns

### 6.1 Hover & Focus

| Element | Hover | Focus |
|---|---|---|
| Nav items | `bg-accent/50` | `ring-2 ring-ring` |
| Buttons | `opacity-90` or `bg-accent` | `ring-2 ring-ring ring-offset-2` |
| Cards (clickable) | `shadow-md scale-[1.02]` | `ring-2 ring-ring` |
| Inputs | `border-border/80` | `ring-2 ring-ring` |
| Scene thumbnails | `border-primary` | `ring-2 ring-ring` |

All hover transitions: `transition-all duration-150`.

**Focus indicators must always be visible** — `focus:outline-none focus-visible:ring-2 focus-visible:ring-ring` on every interactive element.

---

### 6.2 Micro-Animations

| Trigger | Animation | Duration |
|---|---|---|
| Button click | `scale-[0.98]` | 150ms |
| Card hover | `scale-[1.02] shadow-md` | 150ms |
| Content appears | `fade-in` (opacity 0→1) | 150ms |
| Upload item added | slide in from top | 250ms |
| Search results load | staggered fade-in | 150ms each, 30ms delay per item |
| Sidebar collapse | `width` transition | 250ms |
| Theme switch | all color variables | 300ms |

**Staggered fade-in for search results:**
```tsx
results.map((result, i) => (
  <SearchResultCard
    key={result.media_id}
    style={{ animationDelay: `${i * 30}ms` }}
    className="animate-fadeIn"
  />
))
```

---

### 6.3 Keyboard Shortcuts

| Key | Action | Condition |
|---|---|---|
| `/` | Focus search input | Not in input/textarea |
| `u` | Open upload dialog | Not in input/textarea |
| `?` | Open shortcuts help dialog | Always |
| `Escape` | Close modal / dialog / sheet | Always |
| `↑` `↓` | Navigate search results | Not in input, results visible |
| `Enter` | Open focused result | Not in input, item focused |

**Implementation guard:**
```ts
window.addEventListener('keydown', (e) => {
  const tag = document.activeElement?.tagName.toLowerCase()
  const isEditable = ['input', 'textarea', 'select'].includes(tag) ||
                     document.activeElement?.getAttribute('contenteditable')
  if (isEditable && e.key !== 'Escape') return
  // handle shortcut
})
```

**Shortcut hints:** Display in `<Tooltip>` on primary action buttons (e.g., Upload button shows `u`).

---

### 6.4 Dark Mode Toggle

**Toggle button** in sidebar bottom:
```tsx
<Button variant="ghost" size="icon" onClick={toggleTheme} aria-label="Toggle theme">
  {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
</Button>
```

**Theme initialization** (in `main.tsx` before render):
```ts
const stored = localStorage.getItem('semedia_theme')
const system = window.matchMedia('(prefers-color-scheme: dark)').matches
const isDark = stored === 'dark' || (!stored && system)
document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light')
```

**On switch:** Update `data-theme` attribute on `<html>` — CSS variables update instantly, `300ms` color transition handles visual smoothness.

**meta theme-color update:**
```ts
document.querySelector('meta[name="theme-color"]')
  ?.setAttribute('content', isDark ? '#09090b' : '#ffffff')
```

---

## 7. Accessibility Design

### WCAG AA Requirements

| Requirement | Implementation |
|---|---|
| Contrast 4.5:1 (normal text) | Verified via HSL token pairings (`--foreground` on `--background`) |
| Contrast 3:1 (large text) | All headings h1–h3 meet this with primary colors |
| Keyboard navigation | Radix UI primitives handle Tab, Arrow, Enter, Space, Escape |
| Visible focus | `focus-visible:ring-2 ring-ring` on every interactive element |
| ARIA labels | `aria-label` on icon-only buttons, `aria-expanded` on collapsibles |
| Screen reader support | `aria-live="polite"` on search results count, upload status |
| Semantic HTML | `<nav>`, `<main>`, `<aside>`, `<article>`, `<section>` used throughout |
| Skip link | `<a href="#main-content">` as first child of `<body>` |
| Form labels | `<label htmlFor={id}>` for every input |
| Alt text | `alt={filename}` on all media thumbnails |
| Reduced motion | All animations wrapped in `@media (prefers-reduced-motion: no-preference)` |

**`aria-live` regions:**
```html
<div aria-live="polite" aria-atomic="true" class="sr-only">
  {searchStatus} <!-- e.g. "12 results found" -->
</div>
```

---

## 8. Icon System

**Library:** `lucide-react`

**Default size:** 20px (`size={20}`), color inherits via `currentColor`.

**Semantic icon mapping:**

| Action / Concept | Icon | Usage |
|---|---|---|
| Upload | `CloudUpload` | Dropzone, sidebar badge |
| Search | `Search` | Search page, nav |
| Delete | `Trash2` | Media detail, bulk actions |
| Library | `Library` | Nav item |
| Dashboard | `LayoutDashboard` | Nav item |
| Settings | `Settings` | Nav item / sidebar bottom |
| Theme (light) | `Sun` | Theme toggle |
| Theme (dark) | `Moon` | Theme toggle |
| Refresh | `RefreshCw` | Media list panel header |
| Download | `Download` | Media detail |
| Share / Copy | `Link` | Media detail |
| Back | `ArrowLeft` | Media detail breadcrumb |
| View All | `ChevronRight` | Panel headers |
| Close | `X` | Filter chips, toast, modal |
| Sort | `ArrowUpDown` | Table column headers |
| Error | `AlertCircle` | Error states |
| Warning | `AlertTriangle` | Error boundary |
| Empty (images) | `ImageOff` | Empty state |
| Empty (search) | `SearchX` | No results state |
| Video | `Film` | Video placeholder |
| Runtime | `Cpu` | Runtime badge |
| Hamburger | `Menu` | Mobile sidebar trigger |
| Keyboard help | `Keyboard` | Shortcuts dialog trigger |

**Decorative icons** (not announced by screen readers):
```html
<span aria-hidden="true"><CloudUpload size={48} /></span>
```

**Interactive icons** (with accessible label):
```html
<Button variant="ghost" size="icon" aria-label="Delete media">
  <Trash2 size={20} />
</Button>
```

---

## 9. index.css — Complete Token File

The complete `index.css` after redesign (replaces all custom styles):

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background:             0 0% 100%;
    --foreground:             222.2 84% 4.9%;
    --card:                   0 0% 100%;
    --card-foreground:        222.2 84% 4.9%;
    --popover:                0 0% 100%;
    --popover-foreground:     222.2 84% 4.9%;
    --primary:                222.2 47.4% 11.2%;
    --primary-foreground:     210 40% 98%;
    --secondary:              210 40% 96.1%;
    --secondary-foreground:   222.2 47.4% 11.2%;
    --muted:                  210 40% 96.1%;
    --muted-foreground:       215.4 16.3% 46.9%;
    --accent:                 210 40% 96.1%;
    --accent-foreground:      222.2 47.4% 11.2%;
    --destructive:            0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border:                 214.3 31.8% 91.4%;
    --input:                  214.3 31.8% 91.4%;
    --ring:                   222.2 84% 4.9%;
    --radius:                 0.5rem;

    --shadow-sm:  0 1px 2px 0 rgb(0 0 0 / 0.05);
    --shadow-md:  0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    --shadow-lg:  0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
    --shadow-xl:  0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);

    --transition-fast:   150ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-normal: 250ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-slow:   350ms cubic-bezier(0.4, 0, 0.2, 1);
    --transition-theme:  300ms cubic-bezier(0.4, 0, 0.2, 1);
  }

  [data-theme='dark'] {
    --background:             222.2 84% 4.9%;
    --foreground:             210 40% 98%;
    --card:                   222.2 84% 4.9%;
    --card-foreground:        210 40% 98%;
    --popover:                222.2 84% 4.9%;
    --popover-foreground:     210 40% 98%;
    --primary:                210 40% 98%;
    --primary-foreground:     222.2 47.4% 11.2%;
    --secondary:              217.2 32.6% 17.5%;
    --secondary-foreground:   210 40% 98%;
    --muted:                  217.2 32.6% 17.5%;
    --muted-foreground:       215 20.2% 65.1%;
    --accent:                 217.2 32.6% 17.5%;
    --accent-foreground:      210 40% 98%;
    --destructive:            0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border:                 217.2 32.6% 17.5%;
    --input:                  217.2 32.6% 17.5%;
    --ring:                   212.7 26.8% 83.9%;
  }

  * {
    @apply border-border;
    box-sizing: border-box;
  }

  html {
    color-scheme: light;
    transition: color var(--transition-theme),
                background-color var(--transition-theme);
  }

  [data-theme='dark'] html {
    color-scheme: dark;
  }

  body {
    @apply bg-background text-foreground;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
    font-size: 1rem;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  /* Smooth theme color transition */
  *, *::before, *::after {
    transition: background-color var(--transition-theme),
                border-color var(--transition-theme),
                color var(--transition-theme);
  }

  /* Skip navigation link */
  .skip-nav {
    @apply sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4
           focus:z-[100] focus:px-4 focus:py-2 focus:bg-background
           focus:border focus:border-border focus:rounded-md focus:text-foreground;
  }
}

@layer utilities {
  /* Reduced motion: disable all animations */
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
    }
  }

  /* Upload item slide-in */
  @keyframes slideInFromTop {
    from { transform: translateY(-8px); opacity: 0; }
    to   { transform: translateY(0);    opacity: 1; }
  }

  @media (prefers-reduced-motion: no-preference) {
    .animate-slideIn {
      animation: slideInFromTop 250ms cubic-bezier(0.4, 0, 0.2, 1);
    }
    .animate-fadeIn {
      animation: fadeIn 150ms cubic-bezier(0.4, 0, 0.2, 1) both;
    }
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
  }
}
```

---

