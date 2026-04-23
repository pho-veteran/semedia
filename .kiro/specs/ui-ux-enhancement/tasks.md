# Implementation Plan: Semedia UI/UX Redesign

## Overview

This implementation plan transforms the Semedia frontend into a modern, accessible application using shadcn/ui design principles. The redesign includes a complete design system with CSS variables, dark mode support, responsive layouts, and WCAG AA accessibility compliance. Implementation follows a bottom-up approach: design tokens → base components → composite components → pages → interactions.

## Tasks

- [x] 1. Set up design system foundation and CSS tokens
  - Install required dependencies (shadcn/ui, Radix UI primitives, lucide-react, sonner, class-variance-authority, clsx, tailwind-merge)
  - Create complete `frontend/src/index.css` with HSL color tokens for light and dark themes
  - Define typography scale, spacing tokens, shadow tokens, border radius tokens, motion timing tokens, and z-index hierarchy
  - Configure Tailwind with custom theme extensions for design tokens
  - Add reduced motion support with media queries
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 36.1, 36.2, 36.3, 36.4_

- [x] 2. Implement theme management system
  - [x] 2.1 Create theme context and provider component
    - Implement theme initialization from localStorage and system preference
    - Create theme toggle function that updates data-theme attribute on HTML element
    - Implement localStorage persistence for theme preference
    - Add meta theme-color tag update on theme change
    - Apply 300ms transition duration to color changes
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_
  
  - [x] 2.2 Create theme toggle button component
    - Implement button with Sun/Moon icon based on current theme
    - Add aria-label for accessibility
    - Wire up onClick handler to theme toggle function
    - _Requirements: 2.3, 31.1, 31.2, 31.3, 31.4, 31.5, 31.6_

- [x] 3. Build base UI component library
  - [x] 3.1 Create Button component with all variants
    - Implement 6 variants (default, secondary, destructive, outline, ghost, link)
    - Implement 4 sizes (sm, md, lg, icon)
    - Add hover, focus, pressed, disabled, and loading states
    - Apply 150ms transitions and scale transform on press
    - Add focus-visible ring with 2px width
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_
  
  - [x] 3.2 Create Input component with states
    - Implement base input with border, padding, and rounded corners
    - Add focus state with 2px ring
    - Add error state with destructive border and ring
    - Add disabled state with 50% opacity
    - Apply 150ms transition to state changes
    - Create error message component for below input
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_
  
  - [x] 3.3 Create Card component structure
    - Implement Card container with rounded corners, border, and shadow
    - Create CardHeader with title and description sections
    - Create CardContent with padding
    - Create CardFooter for actions
    - Add hover state for clickable cards (increased shadow and scale)
    - Apply 150ms transition to hover effects
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6_
  
  - [x] 3.4 Create Badge component with variants
    - Implement 4 variants (default, secondary, destructive, outline)
    - Use rounded-full shape with small padding and xs font size
    - Add semantic colors for upload status badges (blue, orange, green, red)
    - _Requirements: 14.1, 14.2, 14.3_
  
  - [x] 3.5 Create Dialog/Modal component
    - Implement dialog with focus trap using Radix UI Dialog primitive
    - Add Escape key handler to close dialog
    - Create dialog title, description, and action button sections
    - Set aria-labelledby and aria-describedby attributes
    - Add overlay with backdrop blur
    - _Requirements: 23.1, 23.2, 23.3, 23.4, 23.5, 23.6_
  
  - [x] 3.6 Create Skeleton component for loading states
    - Implement base skeleton with animate-pulse and bg-muted
    - Create skeleton variants for media cards, list items, and search results
    - Add minimum 200ms display time to prevent flashing
    - _Requirements: 19.1, 19.2, 19.3, 19.4_
  
  - [x] 3.7 Create Empty State component
    - Implement centered layout with icon, title, description, and optional CTA
    - Create variants for empty library, no search results, and no scenes
    - Use context-specific icons (ImageOff, SearchX, Film)
    - Apply 16px vertical padding and center alignment
    - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5_
  
  - [x] 3.8 Create Error State component
    - Implement page-level error state with AlertCircle icon
    - Add "Try again" button for recoverable errors
    - Create error banner variant for inline errors
    - Ensure no stack traces are exposed to users
    - Always provide recovery action
    - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5_

- [x] 4. Checkpoint - Verify base components
  - Ensure all base components render correctly in both light and dark themes
  - Test all component variants and states
  - Verify accessibility attributes are present
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement global layout structure
  - [x] 5.1 Create Sidebar component
    - Implement fixed-width sidebar (260px) with logo, navigation, and footer sections
    - Create navigation items for Dashboard, Search, Library.
    - Add active state highlighting with accent background and primary border
    - Add hover state with accent background (50% opacity)
    - Display upload queue count badge on Dashboard nav item
    - Add theme toggle button and runtime badge in footer
    - Apply 150ms transition to hover and focus states
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_
  
  - [x] 5.2 Create mobile sidebar Sheet component
    - Implement full-screen sheet for mobile viewports (< 768px)
    - Add hamburger menu button to trigger sheet
    - Implement focus trap inside sheet when open
    - Add Escape key and outside click handlers to close sheet
    - Apply slide-in animation (250ms) when opening
    - _Requirements: 37.1, 37.2, 37.3, 37.4, 37.5, 37.6_
  
  - [x] 5.3 Create main layout shell
    - Implement flex layout with sidebar and main content area
    - Make main content area independently scrollable
    - Set max-width of 1400px for content, centered on screen
    - Apply responsive padding (12px mobile, 16px tablet, 24px desktop)
    - Hide sidebar and show hamburger on mobile (< 768px)
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 28.1, 28.2, 28.3, 28.4, 28.5, 28.6_

- [x] 6. Build specialized components
  - [x] 6.1 Create UploadDropzone component
    - Implement dashed border with 200px minimum height
    - Display cloud icon, instruction text, and supported formats
    - Add drag-over state with primary border and blue tint background
    - Implement file drop handler to initiate uploads
    - Add click handler to open file browser dialog
    - Display error toast for unsupported file types
    - Display warning toast for files exceeding 100MB
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_
  
  - [x] 6.2 Create UploadQueuePanel component
    - Implement collapsible card that displays when uploads are active
    - Display upload count in header
    - Show each upload item horizontally with thumbnail, filename, size, and progress bar
    - Display status badge with semantic colors (blue, orange, green, red)
    - Add cancel button for uploading/processing items
    - Add retry button for failed items
    - Implement slide-in animation (250ms) for new items
    - Auto-remove completed items after 5 seconds
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8_
  
  - [x] 6.3 Create MediaCard component
    - Implement card with 16:10 aspect ratio thumbnail
    - Display film icon placeholder for videos without thumbnails
    - Show filename, status badge, type, size, and relative time
    - Display caption excerpt truncated to 2 lines
    - Add hover state with scale transform (1.02) and increased shadow
    - Add click handler to navigate to detail page
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6_
  
  - [x] 6.4 Create SearchResultCard component
    - Implement card with 16:10 aspect ratio thumbnail
    - Display relevance score chip overlaid on top-left of thumbnail
    - Display time range chip on top-right for video scenes
    - Show filename and caption excerpt below thumbnail
    - Display scene badge for scene results
    - Add hover state with scale transform (1.02) and increased shadow
    - Add click handler to navigate to media detail page
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7_
  
  - [x] 6.5 Create RuntimeBadge component
    - Display runtime type and device name (e.g., "GPU: RTX 4090")
    - Show green indicator dot for GPU, yellow for CPU
    - Display "Connecting..." text when loading
    - Implement 30-second refetch interval for runtime information
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6_
  
  - [x] 6.6 Create DataTable component
    - Implement table with 8 columns (checkbox, thumbnail, filename, type, size, status, date, actions)
    - Make filename, type, size, status, and date columns sortable
    - Display sort indicator icon on active sort column
    - Add click handler to sort by column
    - Hide type, size, and date columns on mobile (< 768px)
    - Add checkboxes for bulk selection
    - Display action buttons (download, delete) in actions column
    - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7_

- [x] 7. Checkpoint - Verify specialized components
  - Test all specialized components with mock data
  - Verify responsive behavior at different breakpoints
  - Test interactions (hover, click, drag-and-drop)
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement Dashboard page
  - [x] 8.1 Create DashboardPage layout
    - Implement hero section with title, description, and runtime badge
    - Add full-width upload dropzone at top
    - Display horizontal upload queue panel when uploads are active
    - Create recent media section with grid layout (4 cols lg, 3 cols md, 2 cols sm, 1 col xs)
    - Display 12 most recent media items
    - Add refresh button and "View All" link in header
    - Apply responsive padding and spacing
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_
  
  - [x] 8.2 Wire up upload functionality
    - Connect UploadDropzone to upload API endpoint
    - Implement upload progress tracking
    - Update UploadQueuePanel with real-time upload status
    - Handle upload errors and display appropriate toasts
    - _Requirements: 6.4, 6.5, 6.6, 6.7, 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8_
  
  - [x] 8.3 Fetch and display recent media
    - Query API for 12 most recent media items
    - Display loading skeletons while fetching
    - Render MediaCard components in grid layout
    - Handle empty state when no media exists
    - Implement refresh functionality
    - _Requirements: 5.4, 5.5, 19.1, 19.2, 19.3, 20.1_

- [x] 9. Implement Search page
  - [x] 9.1 Create SearchPage layout
    - Implement tabs for text search and image search modes
    - Create text search tab with input field and search button
    - Create image search tab with image dropzone
    - Display recent search terms below text input
    - Add Enter key handler to trigger search
    - Implement 300ms debounce on text input changes
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_
  
  - [x] 9.2 Create filter and sort controls
    - Implement filter controls for type, score threshold, and sort order
    - Display active filter chips with remove buttons
    - Apply filters immediately without submit button
    - _Requirements: 8.7, 8.8, 32.1, 32.2, 32.3, 32.4, 32.5, 32.6, 32.7_
  
  - [x] 9.3 Display search results
    - Show search results count and query summary
    - Render SearchResultCard components in responsive grid layout
    - Implement staggered fade-in animation (150ms each, 30ms delay per item)
    - Display loading skeletons while searching
    - Handle empty state when no results found
    - Handle error state for search failures
    - _Requirements: 8.9, 8.10, 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7, 19.1, 19.2, 19.3, 20.2, 21.3_

- [x] 10. Implement Library page
  - [x] 10.1 Create LibraryPage layout
    - Display total item count in page header
    - Create filter toolbar with search input, type filter, status filter, and sort selector
    - Add view toggle buttons for grid and list views
    - Display active filter chips below filter controls
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  
  - [x] 10.2 Implement bulk operations
    - Display bulk actions toolbar when items are selected
    - Show selection count in toolbar
    - Add bulk download and bulk delete buttons
    - Add cancel button to clear selection
    - Display confirmation dialog for bulk delete
    - _Requirements: 9.5, 9.6, 9.7, 9.9, 33.1, 33.2, 33.3, 33.4, 33.5, 33.6, 33.7_
  
  - [x] 10.3 Display media items in grid or list view
    - Render MediaCard components in responsive grid layout for grid view
    - Render DataTable component for list view
    - Apply filters and sorting to displayed items
    - Display loading skeletons while fetching
    - Handle empty state when no media exists
    - _Requirements: 9.7, 18.1, 18.2, 18.3, 18.4, 18.5, 18.6, 18.7, 19.1, 19.2, 19.3, 20.1_
  
  - [x] 10.4 Implement pagination controls
    - Display current page number and total pages
    - Add previous and next buttons
    - Add items per page selector (24, 48, 96 options)
    - Reset to page 1 when items per page changes
    - _Requirements: 9.8, 38.1, 38.2, 38.3, 38.4, 38.5, 38.6, 38.7_

- [x] 11. Checkpoint - Verify page implementations
  - Test all pages with real API data
  - Verify responsive layouts at all breakpoints
  - Test filtering, sorting, and pagination
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Implement Media Detail page
  - [x] 12.1 Create MediaDetailPage layout
    - Display back button and breadcrumb navigation in header
    - Show filename, status badge, and metadata (type, size, duration/dimensions, upload time)
    - Add action buttons for download, share, and delete
    - Use 2-column layout for videos (60/40 split), single-column for images
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_
  
  - [x] 12.2 Implement media preview
    - Display video player for video media with controls
    - Display image preview for image media with zoom capability
    - Display caption in separate card below preview
    - _Requirements: 10.6, 10.7_
  
  - [x] 12.3 Implement video scenes panel
    - Display scenes panel in right column for videos with scenes
    - Make scenes panel sticky on desktop with scrollable content
    - Show scene thumbnail, time range, and caption for each scene
    - Display scene index badge on thumbnails
    - Add click handler to seek video to scene start time
    - Handle empty state when no scenes detected
    - _Requirements: 10.8, 10.9, 10.10, 34.1, 34.2, 34.3, 34.4, 34.5, 34.6, 20.3_
  
  - [x] 12.4 Implement media actions
    - Wire up download button to download media file
    - Implement share functionality to copy media URL to clipboard
    - Display success toast when URL is copied
    - Add delete confirmation dialog
    - Wire up delete button to API endpoint
    - Navigate back to library after successful delete
    - _Requirements: 35.1, 35.2, 35.3, 23.1, 23.2, 23.3, 23.4, 23.5, 23.6_

- [x] 13. Implement interaction patterns and animations
  - [x] 13.1 Add hover and focus states
    - Apply hover states to navigation items (accent background 50% opacity)
    - Apply hover states to buttons (opacity 90% or accent background)
    - Apply hover states to clickable cards (shadow-md and scale 1.02)
    - Apply hover states to inputs (border-border/80)
    - Apply hover states to scene thumbnails (border-primary)
    - Ensure all interactive elements have visible focus indicators (ring-2 ring-ring)
    - Apply 150ms transition to all hover and focus state changes
    - _Requirements: 25.1, 25.2, 25.3, 25.4, 25.5, 25.6_
  
  - [x] 13.2 Implement micro-animations
    - Add button click animation (scale 0.98 for 150ms)
    - Add card hover animation (scale 1.02 with shadow-md for 150ms)
    - Add content appear animation (fade-in 150ms)
    - Add upload item slide-in animation (250ms from top)
    - Add staggered fade-in for search results (150ms each, 30ms delay)
    - Add sidebar collapse animation (width transition 250ms)
    - Ensure theme switch has 300ms color transition
    - _Requirements: 26.1, 26.2, 26.3, 26.4, 26.5, 26.6, 26.7_

- [x] 14. Implement keyboard shortcuts and accessibility
  - [x] 14.1 Add keyboard shortcuts
    - Implement "/" key to focus search input (when not in input field)
    - Implement "u" key to open upload dialog (when not in input field)
    - Implement "?" key to open shortcuts help dialog
    - Implement Escape key to close modals, dialogs, and sheets
    - Implement up/down arrow keys to navigate search results (when not in input field)
    - Implement Enter key to open focused result (when not in input field)
    - Add guard to prevent shortcuts when user is typing in input/textarea
    - _Requirements: 27.1, 27.2, 27.3, 27.4, 27.5, 27.6, 27.7_
  
  - [x] 14.2 Ensure WCAG AA accessibility compliance
    - Verify 4.5:1 contrast ratio for normal text
    - Verify 3:1 contrast ratio for large text (headings)
    - Ensure keyboard navigation works for all interactive elements
    - Verify visible focus indicators on all interactive elements
    - Add aria-label attributes on icon-only buttons
    - Add aria-live regions for dynamic content (search results count, upload status)
    - Use semantic HTML elements (nav, main, aside, article, section)
    - Add skip navigation link as first focusable element
    - Add label elements for all form inputs
    - Add alt text for all media thumbnails
    - _Requirements: 29.1, 29.2, 29.3, 29.4, 29.5, 29.6, 29.7, 29.8, 29.9, 29.10, 29.11_

- [x] 15. Implement toast notification system
  - Install and configure Sonner toast library
  - Mount Toaster component in App.tsx root
  - Display success toast for upload complete (5s duration)
  - Display error toast for upload failed (10s duration with retry action)
  - Display success toast for delete complete (5s duration with undo action)
  - Display error toast for API errors (10s duration)
  - Configure toasts to stack vertically in bottom-right corner
  - Pause auto-dismiss timer on hover
  - Add close button to all toasts
  - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.5, 22.6, 22.7_

- [x] 16. Implement Error Boundary
  - Create ErrorBoundary class component
  - Wrap entire app in ErrorBoundary in App.tsx
  - Display fallback UI with AlertTriangle icon when error is caught
  - Show "Something went wrong" title and description
  - Add "Reload page" button that calls window.location.reload()
  - Log error and errorInfo to console.error
  - Never expose stack traces to users
  - _Requirements: 24.1, 24.2, 24.3, 24.4, 24.5, 24.6_

- [x] 17. Implement responsive design and touch targets
  - [x] 17.1 Verify responsive breakpoints
    - Test 1-column grid layout on mobile (< 640px)
    - Test 2-column grid layout on small screens (≥ 640px)
    - Test 3-column grid layout on tablets (≥ 768px) with sidebar visible
    - Test 4-column grid layout on desktop (≥ 1024px)
    - Test sidebar collapse on mobile (< 768px) with hamburger menu
    - Test data table column collapse on mobile (hide type, size, date)
    - _Requirements: 28.1, 28.2, 28.3, 28.4, 28.5, 28.6_
  
  - [x] 17.2 Ensure touch target sizing
    - Verify all interactive elements have minimum 44px height on mobile
    - Verify all interactive elements have minimum 44px width on mobile
    - Apply appropriate padding to maintain touch target size
    - _Requirements: 39.1, 39.2, 39.3_
  
  - [x] 17.3 Apply responsive content padding
    - Apply 12px horizontal padding on mobile (< 640px)
    - Apply 16px horizontal padding on tablets (≥ 768px)
    - Apply 24px horizontal padding on desktop (≥ 1024px)
    - Apply responsive vertical spacing (16px mobile, 24px desktop) between sections
    - _Requirements: 40.1, 40.2, 40.3, 40.4_

- [x] 18. Final integration and testing
  - [x] 18.1 Wire up all API endpoints
    - Connect all components to real API endpoints
    - Implement error handling for all API calls
    - Add loading states for all async operations
    - Test all CRUD operations (create, read, update, delete)
    - _Requirements: All requirements_
  
  - [x] 18.2 Test dark mode thoroughly
    - Verify all components render correctly in dark mode
    - Test theme toggle functionality
    - Verify localStorage persistence
    - Test system preference detection
    - Verify meta theme-color updates
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 31.1, 31.2, 31.3, 31.4, 31.5, 31.6_
  
  - [x] 18.3 Perform accessibility audit
    - Run automated accessibility tests (axe, Lighthouse)
    - Test keyboard navigation throughout the application
    - Test with screen reader (NVDA, JAWS, or VoiceOver)
    - Verify all ARIA attributes are correct
    - Test reduced motion preference
    - _Requirements: 29.1, 29.2, 29.3, 29.4, 29.5, 29.6, 29.7, 29.8, 29.9, 29.10, 29.11, 36.1, 36.2, 36.3, 36.4_
  
  - [x] 18.4 Test responsive design on real devices
    - Test on mobile devices (iOS and Android)
    - Test on tablets (iPad, Android tablets)
    - Test on desktop browsers (Chrome, Firefox, Safari, Edge)
    - Verify touch interactions work correctly
    - Test landscape and portrait orientations
    - _Requirements: 28.1, 28.2, 28.3, 28.4, 28.5, 28.6, 39.1, 39.2, 39.3_

- [x] 19. Final checkpoint - Complete redesign verification
  - Verify all 40 requirements are implemented
  - Test all user flows end-to-end
  - Verify performance (Lighthouse score > 90)
  - Ensure no console errors or warnings
  - Verify all animations respect reduced motion preference
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- This is a comprehensive UI/UX redesign that replaces the existing frontend with a modern, accessible design system
- The implementation uses TypeScript, React, Vite, Tailwind CSS, shadcn/ui components, and Radix UI primitives
- All components follow shadcn/ui design principles: owned (not overridden), styled with Tailwind utilities and CSS variables
- The design is minimalist and professional with no glassmorphism or decorative gradients
- All colors are referenced via HSL CSS variables for consistent theming
- Every interactive element is keyboard-navigable and meets WCAG AA contrast requirements
- Animations are functional (150ms for micro-interactions) and respect reduced motion preferences
- The implementation follows a bottom-up approach: design tokens → base components → composite components → pages → interactions
- Each task references specific requirements for traceability
- Testing and verification checkpoints ensure incremental validation
