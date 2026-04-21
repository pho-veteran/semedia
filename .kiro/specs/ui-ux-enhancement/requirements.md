# Requirements Document: Semedia UI/UX Redesign

## Introduction

This document specifies the requirements for redesigning the Semedia frontend application using shadcn/ui design principles. The redesign transforms the existing interface into a minimalist, professional, and accessible application with a consistent design system, improved user experience, and WCAG AA compliance.

## Glossary

- **UI_System**: The complete Semedia frontend user interface application
- **Design_System**: The collection of design tokens, color variables, typography, spacing, and styling rules
- **Theme_Manager**: The component responsible for managing light/dark theme switching
- **Sidebar**: The fixed navigation panel on the left side of the application
- **Upload_Dropzone**: The drag-and-drop file upload interface component
- **Upload_Queue**: The panel displaying active file uploads with progress indicators
- **Media_Card**: A card component displaying media item information and thumbnail
- **Search_Interface**: The search page with text and image search capabilities
- **Library_View**: The media library page with filtering, sorting, and bulk operations
- **Detail_Page**: The media detail page showing full media information and scenes
- **Filter_Bar**: The toolbar containing search, filter, and sort controls
- **Data_Table**: The list view component for displaying media in tabular format
- **Toast_System**: The notification system for displaying temporary messages
- **Dialog_Component**: Modal dialogs for confirmations and user interactions
- **Skeleton_Screen**: Loading placeholder components displayed during data fetching
- **Error_Boundary**: The top-level error handling component
- **Accessibility_System**: The collection of WCAG AA compliance features

## Requirements

### Requirement 1: Design System Implementation

**User Story:** As a developer, I want a consistent design system with CSS variables and tokens, so that the UI maintains visual consistency across all components.

#### Acceptance Criteria

1. THE Design_System SHALL define all color tokens as HSL channel values in CSS variables
2. THE Design_System SHALL provide separate color palettes for light and dark themes
3. THE Design_System SHALL define typography scale with 6 heading levels and 4 body text sizes
4. THE Design_System SHALL define spacing tokens using Tailwind's spacing scale
5. THE Design_System SHALL define shadow tokens for 4 elevation levels (sm, md, lg, xl)
6. THE Design_System SHALL define border radius tokens for 4 sizes (sm, md, lg, xl)
7. THE Design_System SHALL define motion timing tokens for 4 durations (fast, normal, slow, theme)
8. THE Design_System SHALL define z-index hierarchy for 8 UI layers

### Requirement 2: Theme Management

**User Story:** As a user, I want to switch between light and dark themes, so that I can use the application comfortably in different lighting conditions.

#### Acceptance Criteria

1. WHEN the application initializes, THE Theme_Manager SHALL check localStorage for saved theme preference
2. IF no saved preference exists, THEN THE Theme_Manager SHALL use system color scheme preference
3. WHEN the user clicks the theme toggle button, THE Theme_Manager SHALL switch between light and dark themes
4. WHEN the theme changes, THE Theme_Manager SHALL update the data-theme attribute on the HTML element
5. WHEN the theme changes, THE Theme_Manager SHALL save the preference to localStorage
6. WHEN the theme changes, THE Theme_Manager SHALL update the meta theme-color tag
7. THE Theme_Manager SHALL apply 300ms transition duration to all color changes

### Requirement 3: Global Layout Structure

**User Story:** As a user, I want a consistent layout with navigation sidebar and main content area, so that I can easily navigate the application.

#### Acceptance Criteria

1. THE UI_System SHALL display a fixed-width sidebar (260px) on desktop viewports
2. THE UI_System SHALL display the sidebar as a full-screen sheet on mobile viewports (< 768px)
3. THE UI_System SHALL display main content area with maximum width of 1400px centered on screen
4. THE UI_System SHALL make the main content area independently scrollable from the sidebar
5. THE UI_System SHALL apply responsive padding to content (12px mobile, 16px tablet, 24px desktop)

### Requirement 4: Sidebar Navigation

**User Story:** As a user, I want a sidebar with navigation links and theme controls, so that I can access different sections of the application.

#### Acceptance Criteria

1. THE Sidebar SHALL display the application logo and brand name in the header section
2. THE Sidebar SHALL display navigation items for Dashboard, Search, Library, and Settings
3. WHEN a navigation item is active, THE Sidebar SHALL highlight it with accent background and primary border
4. WHEN the user hovers over an inactive navigation item, THE Sidebar SHALL display hover state with accent background
5. THE Sidebar SHALL display upload queue count badge on Dashboard nav item when uploads are active
6. THE Sidebar SHALL display theme toggle button in the footer section
7. THE Sidebar SHALL display runtime badge in the footer section
8. THE Sidebar SHALL apply 150ms transition to all hover and focus states

### Requirement 5: Dashboard Page Layout

**User Story:** As a user, I want a dashboard with upload interface and recent media, so that I can quickly upload files and see my recent content.

#### Acceptance Criteria

1. THE UI_System SHALL display full-width upload dropzone at the top of the dashboard
2. WHEN uploads are active, THE UI_System SHALL display horizontal upload queue panel below the dropzone
3. THE UI_System SHALL display recent media section with grid layout below the upload area
4. THE UI_System SHALL display 12 most recent media items in the recent media section
5. THE UI_System SHALL use responsive grid (1 column mobile, 2 columns sm, 3 columns md, 4 columns lg)
6. THE UI_System SHALL display refresh button and "View All" link in recent media header

### Requirement 6: Upload Dropzone Functionality

**User Story:** As a user, I want to upload files by dragging or clicking, so that I can add media to my library.

#### Acceptance Criteria

1. THE Upload_Dropzone SHALL display dashed border with 200px minimum height
2. THE Upload_Dropzone SHALL display cloud icon, instruction text, and supported formats
3. WHEN the user drags files over the dropzone, THE Upload_Dropzone SHALL change border to primary color and add blue tint background
4. WHEN the user drops files, THE Upload_Dropzone SHALL initiate upload for all valid files
5. WHEN the user clicks the dropzone, THE Upload_Dropzone SHALL open file browser dialog
6. IF a file type is not supported, THEN THE Upload_Dropzone SHALL display error toast notification
7. IF a file exceeds 100MB, THEN THE Upload_Dropzone SHALL display warning toast notification

### Requirement 7: Upload Queue Display

**User Story:** As a user, I want to see upload progress for my files, so that I can monitor the upload status.

#### Acceptance Criteria

1. WHEN uploads are active, THE Upload_Queue SHALL display as a card with collapsible content
2. THE Upload_Queue SHALL display upload count in the header
3. THE Upload_Queue SHALL display each upload item horizontally with thumbnail, filename, size, and progress bar
4. THE Upload_Queue SHALL display status badge with appropriate color (blue for uploading, orange for processing, green for completed, red for failed)
5. THE Upload_Queue SHALL display cancel button for uploading and processing items
6. THE Upload_Queue SHALL display retry button for failed items
7. WHEN an upload item is added, THE Upload_Queue SHALL animate it with slide-in from top (250ms duration)
8. WHEN an upload completes, THE Upload_Queue SHALL automatically remove the item after 5 seconds

### Requirement 8: Search Page Interface

**User Story:** As a user, I want to search for media using text or images, so that I can find specific content in my library.

#### Acceptance Criteria

1. THE Search_Interface SHALL display tabs for text search and image search modes
2. WHEN text search tab is active, THE Search_Interface SHALL display text input field and search button
3. WHEN image search tab is active, THE Search_Interface SHALL display image dropzone for query image
4. THE Search_Interface SHALL display recent search terms below the text input
5. WHEN the user presses Enter in the search input, THE Search_Interface SHALL trigger search
6. THE Search_Interface SHALL debounce text input changes by 300ms before triggering search
7. THE Search_Interface SHALL display filter controls for type, score threshold, and sort order
8. THE Search_Interface SHALL display active filter chips with remove buttons
9. THE Search_Interface SHALL display search results count and query summary
10. THE Search_Interface SHALL display search results in responsive grid layout

### Requirement 9: Library Page Functionality

**User Story:** As a user, I want to browse, filter, and manage my media library, so that I can organize my content.

#### Acceptance Criteria

1. THE Library_View SHALL display total item count in the page header
2. THE Library_View SHALL display filter toolbar with search input, type filter, status filter, and sort selector
3. THE Library_View SHALL display view toggle buttons for grid and list views
4. THE Library_View SHALL display active filter chips below the filter controls
5. WHEN items are selected, THE Library_View SHALL display bulk actions toolbar
6. THE Library_View SHALL display bulk download and bulk delete buttons in the toolbar
7. THE Library_View SHALL display media items in responsive grid layout (grid view) or data table (list view)
8. THE Library_View SHALL display pagination controls with page numbers and items per page selector
9. WHEN the user selects items, THE Library_View SHALL display selection count in bulk toolbar

### Requirement 10: Media Detail Page Layout

**User Story:** As a user, I want to view detailed information about a media item, so that I can see full content and metadata.

#### Acceptance Criteria

1. THE Detail_Page SHALL display back button and breadcrumb navigation in the header
2. THE Detail_Page SHALL display filename, status badge, and metadata (type, size, duration/dimensions, upload time)
3. THE Detail_Page SHALL display action buttons for download, share, and delete
4. WHEN media type is video, THE Detail_Page SHALL use 2-column layout on desktop (60/40 split)
5. WHEN media type is image, THE Detail_Page SHALL use single-column layout
6. THE Detail_Page SHALL display media preview (video player or image) in a card
7. THE Detail_Page SHALL display caption in a separate card below the preview
8. WHEN media type is video AND scenes exist, THE Detail_Page SHALL display scenes panel in right column
9. THE Detail_Page SHALL make scenes panel sticky on desktop with scrollable content
10. WHEN the user clicks a scene thumbnail, THE Detail_Page SHALL seek video to that scene's start time

### Requirement 11: Button Component Variants

**User Story:** As a developer, I want button components with consistent variants and states, so that I can maintain visual hierarchy.

#### Acceptance Criteria

1. THE UI_System SHALL provide 6 button variants (default, secondary, destructive, outline, ghost, link)
2. THE UI_System SHALL provide 4 button sizes (sm: 36px, md: 40px, lg: 44px, icon: 40x40px)
3. WHEN the user hovers over a button, THE UI_System SHALL apply hover state (opacity or background change)
4. WHEN a button receives focus, THE UI_System SHALL display 2px ring with ring color
5. WHEN the user presses a button, THE UI_System SHALL apply scale transform (0.98) for 150ms
6. WHEN a button is disabled, THE UI_System SHALL apply 50% opacity and disable pointer events
7. WHEN a button is in loading state, THE UI_System SHALL display spinner and disable interaction

### Requirement 12: Input Component States

**User Story:** As a user, I want form inputs with clear visual feedback, so that I can understand input state and validation.

#### Acceptance Criteria

1. THE UI_System SHALL display inputs with 10px height, rounded corners, and border
2. WHEN an input receives focus, THE UI_System SHALL display 2px ring with ring color
3. WHEN an input has an error, THE UI_System SHALL display destructive border and ring color
4. WHEN an input has an error, THE UI_System SHALL display error message below the input
5. WHEN an input is disabled, THE UI_System SHALL display disabled cursor and 50% opacity
6. THE UI_System SHALL apply 150ms transition to all input state changes

### Requirement 13: Card Component Structure

**User Story:** As a developer, I want card components with consistent structure, so that I can display grouped content.

#### Acceptance Criteria

1. THE UI_System SHALL provide card component with rounded corners, border, and shadow
2. THE UI_System SHALL provide card header section with title and description
3. THE UI_System SHALL provide card content section with padding
4. THE UI_System SHALL provide card footer section for actions
5. WHEN a card is clickable, THE UI_System SHALL apply hover state with increased shadow and scale (1.02)
6. THE UI_System SHALL apply 150ms transition to card hover effects

### Requirement 14: Badge Component Variants

**User Story:** As a developer, I want badge components for status and labels, so that I can display categorical information.

#### Acceptance Criteria

1. THE UI_System SHALL provide 4 badge variants (default, secondary, destructive, outline)
2. THE UI_System SHALL display badges with rounded-full shape, small padding, and xs font size
3. THE UI_System SHALL use semantic colors for upload status badges (blue: uploading, orange: processing, green: completed, red: failed)

### Requirement 15: Media Card Display

**User Story:** As a user, I want media cards with thumbnails and metadata, so that I can identify content at a glance.

#### Acceptance Criteria

1. THE Media_Card SHALL display thumbnail with 16:10 aspect ratio
2. WHEN media type is video, THE Media_Card SHALL display film icon placeholder if thumbnail is unavailable
3. THE Media_Card SHALL display filename, status badge, type, size, and relative time
4. THE Media_Card SHALL display caption excerpt truncated to 2 lines
5. WHEN the user hovers over a media card, THE Media_Card SHALL apply scale transform (1.02) and increased shadow
6. WHEN the user clicks a media card, THE Media_Card SHALL navigate to the detail page

### Requirement 16: Search Result Card Display

**User Story:** As a user, I want search result cards with relevance scores, so that I can evaluate search quality.

#### Acceptance Criteria

1. THE UI_System SHALL display search result cards with 16:10 aspect ratio thumbnails
2. THE UI_System SHALL display relevance score chip overlaid on top-left of thumbnail
3. WHEN result is a video scene, THE UI_System SHALL display time range chip overlaid on top-right of thumbnail
4. THE UI_System SHALL display filename and caption excerpt below the thumbnail
5. WHEN result is a scene, THE UI_System SHALL display scene badge
6. WHEN the user hovers over a result card, THE UI_System SHALL apply scale transform (1.02) and increased shadow
7. WHEN the user clicks a result card, THE UI_System SHALL navigate to the media detail page

### Requirement 17: Runtime Badge Display

**User Story:** As a user, I want to see the current runtime environment, so that I know which hardware is being used.

#### Acceptance Criteria

1. THE UI_System SHALL display runtime badge in sidebar footer and dashboard header
2. THE UI_System SHALL display green indicator dot for GPU runtime
3. THE UI_System SHALL display yellow indicator dot for CPU runtime
4. THE UI_System SHALL display runtime type and device name (e.g., "GPU: RTX 4090")
5. THE UI_System SHALL refetch runtime information every 30 seconds
6. WHEN runtime information is loading, THE UI_System SHALL display "Connecting..." text

### Requirement 18: Data Table Implementation

**User Story:** As a user, I want to view media in a table format, so that I can see detailed information in a compact layout.

#### Acceptance Criteria

1. THE Data_Table SHALL display 8 columns (checkbox, thumbnail, filename, type, size, status, date, actions)
2. THE Data_Table SHALL make filename, type, size, status, and date columns sortable
3. WHEN the user clicks a sortable column header, THE Data_Table SHALL sort by that column
4. THE Data_Table SHALL display sort indicator icon on the active sort column
5. WHEN viewport is mobile (< 768px), THE Data_Table SHALL hide type, size, and date columns
6. THE Data_Table SHALL display checkboxes for bulk selection
7. THE Data_Table SHALL display action buttons (download, delete) in the actions column

### Requirement 19: Skeleton Loading States

**User Story:** As a user, I want to see loading placeholders, so that I understand content is being fetched.

#### Acceptance Criteria

1. WHEN data is loading, THE UI_System SHALL display skeleton screens matching the content structure
2. THE UI_System SHALL animate skeleton components with pulse effect
3. THE UI_System SHALL display skeleton for minimum 200ms to prevent flashing
4. THE UI_System SHALL provide skeleton variants for media cards, list items, and search results

### Requirement 20: Empty State Display

**User Story:** As a user, I want to see helpful empty states, so that I understand when no content is available.

#### Acceptance Criteria

1. WHEN no media exists in library, THE UI_System SHALL display empty state with ImageOff icon and "Upload media" button
2. WHEN no search results are found, THE UI_System SHALL display empty state with SearchX icon and "Try different terms" message
3. WHEN no scenes are detected in a video, THE UI_System SHALL display empty state with Film icon
4. THE UI_System SHALL center empty states vertically and horizontally with 16px vertical padding
5. THE UI_System SHALL display icon in muted background circle, title, description, and optional action button

### Requirement 21: Error State Handling

**User Story:** As a user, I want to see clear error messages with recovery options, so that I can resolve issues.

#### Acceptance Criteria

1. WHEN a page-level error occurs, THE UI_System SHALL display error state with AlertCircle icon and error message
2. THE UI_System SHALL display "Try again" button for recoverable errors
3. WHEN a search fails, THE UI_System SHALL display error banner with destructive variant
4. THE UI_System SHALL never display stack traces to users
5. THE UI_System SHALL always provide a recovery action for errors

### Requirement 22: Toast Notification System

**User Story:** As a user, I want to receive temporary notifications for actions, so that I get feedback on operations.

#### Acceptance Criteria

1. WHEN an upload completes, THE Toast_System SHALL display success toast for 5 seconds
2. WHEN an upload fails, THE Toast_System SHALL display error toast for 10 seconds with retry action
3. WHEN a media item is deleted, THE Toast_System SHALL display success toast for 5 seconds with undo action
4. WHEN an API error occurs, THE Toast_System SHALL display error toast for 10 seconds
5. THE Toast_System SHALL stack toasts vertically in bottom-right corner
6. WHEN the user hovers over a toast, THE Toast_System SHALL pause auto-dismiss timer
7. THE Toast_System SHALL display close button on all toasts

### Requirement 23: Dialog Modal Functionality

**User Story:** As a user, I want confirmation dialogs for destructive actions, so that I can prevent accidental data loss.

#### Acceptance Criteria

1. WHEN the user clicks delete button, THE Dialog_Component SHALL display confirmation dialog
2. THE Dialog_Component SHALL trap focus inside the dialog when open
3. WHEN the user presses Escape key, THE Dialog_Component SHALL close the dialog
4. THE Dialog_Component SHALL display dialog title, description, and action buttons
5. THE Dialog_Component SHALL use destructive variant for delete button
6. THE Dialog_Component SHALL set aria-labelledby and aria-describedby attributes correctly

### Requirement 24: Error Boundary Implementation

**User Story:** As a user, I want the application to handle unexpected errors gracefully, so that I can recover from crashes.

#### Acceptance Criteria

1. WHEN an unhandled error occurs, THE Error_Boundary SHALL catch the error and display fallback UI
2. THE Error_Boundary SHALL display AlertTriangle icon, error title, and description
3. THE Error_Boundary SHALL display "Reload page" button
4. WHEN the user clicks reload button, THE Error_Boundary SHALL reload the page
5. THE Error_Boundary SHALL log error and errorInfo to console
6. THE Error_Boundary SHALL never expose stack traces to users

### Requirement 25: Hover and Focus States

**User Story:** As a user, I want clear visual feedback on interactive elements, so that I understand what is clickable.

#### Acceptance Criteria

1. WHEN the user hovers over a navigation item, THE UI_System SHALL apply accent background with 50% opacity
2. WHEN the user hovers over a button, THE UI_System SHALL apply opacity change or accent background
3. WHEN the user hovers over a clickable card, THE UI_System SHALL apply increased shadow and scale transform
4. WHEN an element receives keyboard focus, THE UI_System SHALL display 2px ring with ring color
5. THE UI_System SHALL apply 150ms transition to all hover and focus state changes
6. THE UI_System SHALL ensure focus indicators are always visible

### Requirement 26: Micro-Animations

**User Story:** As a user, I want subtle animations that communicate state changes, so that the interface feels responsive.

#### Acceptance Criteria

1. WHEN the user clicks a button, THE UI_System SHALL apply scale transform (0.98) for 150ms
2. WHEN a card is hovered, THE UI_System SHALL apply scale transform (1.02) for 150ms
3. WHEN content appears, THE UI_System SHALL apply fade-in animation (150ms)
4. WHEN an upload item is added, THE UI_System SHALL apply slide-in from top animation (250ms)
5. WHEN search results load, THE UI_System SHALL apply staggered fade-in with 30ms delay per item
6. WHEN the sidebar collapses, THE UI_System SHALL apply width transition (250ms)
7. WHEN the theme switches, THE UI_System SHALL apply color transition to all variables (300ms)

### Requirement 27: Keyboard Shortcuts

**User Story:** As a user, I want keyboard shortcuts for common actions, so that I can navigate efficiently.

#### Acceptance Criteria

1. WHEN the user presses "/" key, THE UI_System SHALL focus the search input (if not in input field)
2. WHEN the user presses "u" key, THE UI_System SHALL open upload dialog (if not in input field)
3. WHEN the user presses "?" key, THE UI_System SHALL open shortcuts help dialog
4. WHEN the user presses Escape key, THE UI_System SHALL close any open modal, dialog, or sheet
5. WHEN the user presses up/down arrow keys, THE UI_System SHALL navigate search results (if not in input field)
6. WHEN the user presses Enter key, THE UI_System SHALL open focused result (if not in input field)
7. THE UI_System SHALL not trigger shortcuts when user is typing in input, textarea, or contenteditable element

### Requirement 28: Responsive Breakpoints

**User Story:** As a user, I want the interface to adapt to different screen sizes, so that I can use it on any device.

#### Acceptance Criteria

1. WHEN viewport width is less than 640px, THE UI_System SHALL use 1-column grid layout
2. WHEN viewport width is 640px or greater, THE UI_System SHALL use 2-column grid layout
3. WHEN viewport width is 768px or greater, THE UI_System SHALL display sidebar and use 3-column grid layout
4. WHEN viewport width is 1024px or greater, THE UI_System SHALL use 4-column grid layout
5. WHEN viewport width is less than 768px, THE UI_System SHALL hide sidebar and display hamburger menu button
6. WHEN viewport width is less than 768px, THE UI_System SHALL collapse data table columns (hide type, size, date)

### Requirement 29: Accessibility Compliance

**User Story:** As a user with disabilities, I want an accessible interface, so that I can use the application with assistive technologies.

#### Acceptance Criteria

1. THE Accessibility_System SHALL ensure 4.5:1 contrast ratio for normal text
2. THE Accessibility_System SHALL ensure 3:1 contrast ratio for large text (headings)
3. THE Accessibility_System SHALL support keyboard navigation for all interactive elements
4. THE Accessibility_System SHALL display visible focus indicators on all interactive elements
5. THE Accessibility_System SHALL provide aria-label attributes on icon-only buttons
6. THE Accessibility_System SHALL provide aria-live regions for dynamic content (search results count, upload status)
7. THE Accessibility_System SHALL use semantic HTML elements (nav, main, aside, article, section)
8. THE Accessibility_System SHALL provide skip navigation link as first focusable element
9. THE Accessibility_System SHALL provide label elements for all form inputs
10. THE Accessibility_System SHALL provide alt text for all media thumbnails
11. WHEN user prefers reduced motion, THE Accessibility_System SHALL disable all animations

### Requirement 30: Icon System

**User Story:** As a developer, I want a consistent icon system, so that I can use semantic icons throughout the application.

#### Acceptance Criteria

1. THE UI_System SHALL use lucide-react icon library for all icons
2. THE UI_System SHALL use 20px default size for icons
3. THE UI_System SHALL use currentColor for icon color inheritance
4. THE UI_System SHALL provide semantic icon mapping for all actions (upload, search, delete, etc.)
5. WHEN an icon is decorative, THE UI_System SHALL set aria-hidden="true" attribute
6. WHEN an icon is interactive, THE UI_System SHALL provide accessible label via aria-label

### Requirement 31: Dark Mode Color Palette

**User Story:** As a user, I want a dark mode with appropriate colors, so that I can use the application in low-light environments.

#### Acceptance Criteria

1. WHEN dark mode is active, THE Design_System SHALL use dark background (222.2 84% 4.9%)
2. WHEN dark mode is active, THE Design_System SHALL use light foreground (210 40% 98%)
3. WHEN dark mode is active, THE Design_System SHALL invert primary and primary-foreground colors
4. WHEN dark mode is active, THE Design_System SHALL use darker secondary, muted, and accent colors
5. WHEN dark mode is active, THE Design_System SHALL use darker destructive color (0 62.8% 30.6%)
6. WHEN dark mode is active, THE Design_System SHALL use lighter ring color for focus indicators

### Requirement 32: Filter and Sort Controls

**User Story:** As a user, I want to filter and sort my media library, so that I can find specific content.

#### Acceptance Criteria

1. THE Filter_Bar SHALL provide type filter with options (all, images, videos)
2. THE Filter_Bar SHALL provide status filter with options (all, completed, processing, failed)
3. THE Filter_Bar SHALL provide sort selector with options (newest, oldest, name, size)
4. THE Filter_Bar SHALL provide score threshold filter on search page (≥0.5, ≥0.7, ≥0.9)
5. WHEN the user selects a filter, THE Filter_Bar SHALL display active filter chip
6. WHEN the user clicks remove button on filter chip, THE Filter_Bar SHALL remove that filter
7. THE Filter_Bar SHALL apply filters immediately without requiring submit button

### Requirement 33: Bulk Operations

**User Story:** As a user, I want to perform bulk operations on multiple media items, so that I can manage content efficiently.

#### Acceptance Criteria

1. WHEN the user selects one or more items, THE Library_View SHALL display bulk actions toolbar
2. THE Library_View SHALL display selection count in the bulk toolbar
3. THE Library_View SHALL provide bulk download button
4. THE Library_View SHALL provide bulk delete button with destructive variant
5. THE Library_View SHALL provide cancel button to clear selection
6. WHEN the user clicks bulk delete, THE Library_View SHALL display confirmation dialog
7. WHEN the user confirms bulk delete, THE Library_View SHALL delete all selected items

### Requirement 34: Video Scene Navigation

**User Story:** As a user, I want to navigate video scenes, so that I can jump to specific parts of a video.

#### Acceptance Criteria

1. WHEN media type is video AND scenes exist, THE Detail_Page SHALL display scenes panel
2. THE Detail_Page SHALL display scene thumbnail, time range, and caption for each scene
3. THE Detail_Page SHALL display scene index badge on each thumbnail
4. WHEN the user clicks a scene thumbnail, THE Detail_Page SHALL seek video player to that scene's start time
5. THE Detail_Page SHALL make scenes panel scrollable with max-height constraint
6. THE Detail_Page SHALL make scenes panel sticky on desktop viewports

### Requirement 35: Share Functionality

**User Story:** As a user, I want to share media items, so that I can provide access to others.

#### Acceptance Criteria

1. WHEN the user clicks share button on detail page, THE UI_System SHALL copy media URL to clipboard
2. WHEN the URL is copied, THE UI_System SHALL display success toast notification
3. THE UI_System SHALL use the Link icon for share button

### Requirement 36: Reduced Motion Support

**User Story:** As a user who prefers reduced motion, I want animations to be disabled, so that I can use the application comfortably.

#### Acceptance Criteria

1. WHEN user prefers reduced motion, THE UI_System SHALL set all animation durations to 0.01ms
2. WHEN user prefers reduced motion, THE UI_System SHALL set all transition durations to 0.01ms
3. WHEN user prefers reduced motion, THE UI_System SHALL set animation iteration count to 1
4. THE UI_System SHALL wrap all animations in prefers-reduced-motion: no-preference media query

### Requirement 37: Mobile Sidebar Sheet

**User Story:** As a mobile user, I want to access navigation via a slide-out menu, so that I can navigate on small screens.

#### Acceptance Criteria

1. WHEN viewport width is less than 768px, THE UI_System SHALL hide the sidebar
2. WHEN viewport width is less than 768px, THE UI_System SHALL display hamburger menu button
3. WHEN the user clicks hamburger button, THE UI_System SHALL open sidebar as full-screen sheet
4. WHEN the sheet is open, THE UI_System SHALL trap focus inside the sheet
5. WHEN the user presses Escape or clicks outside, THE UI_System SHALL close the sheet
6. THE UI_System SHALL apply slide-in animation when opening the sheet (250ms)

### Requirement 38: Pagination Controls

**User Story:** As a user, I want to navigate through pages of media, so that I can browse large libraries.

#### Acceptance Criteria

1. THE Library_View SHALL display pagination controls at the bottom of the page
2. THE Library_View SHALL display current page number and total pages
3. THE Library_View SHALL display previous and next buttons
4. THE Library_View SHALL display items per page selector (24, 48, 96 options)
5. WHEN the user clicks previous button, THE Library_View SHALL navigate to previous page
6. WHEN the user clicks next button, THE Library_View SHALL navigate to next page
7. WHEN the user changes items per page, THE Library_View SHALL reset to page 1

### Requirement 39: Touch Target Sizing

**User Story:** As a mobile user, I want adequately sized touch targets, so that I can interact with the interface easily.

#### Acceptance Criteria

1. THE UI_System SHALL ensure all interactive elements have minimum 44px height on mobile
2. THE UI_System SHALL ensure all interactive elements have minimum 44px width on mobile
3. THE UI_System SHALL apply appropriate padding to maintain touch target size

### Requirement 40: Content Padding Responsiveness

**User Story:** As a user, I want appropriate content spacing on different devices, so that content is readable and not cramped.

#### Acceptance Criteria

1. WHEN viewport width is less than 640px, THE UI_System SHALL apply 12px horizontal padding to content
2. WHEN viewport width is 768px or greater, THE UI_System SHALL apply 16px horizontal padding to content
3. WHEN viewport width is 1024px or greater, THE UI_System SHALL apply 24px horizontal padding to content
4. THE UI_System SHALL apply responsive vertical spacing (16px mobile, 24px desktop) between sections
