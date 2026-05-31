# Design Document

## Overview

Tài liệu thiết kế này mô tả cách triển khai việc tái cấu trúc lớp trình bày (presentation-layer) cho frontend "Semedia" theo bộ yêu cầu đã được phê duyệt tại `requirements.md`. Mục tiêu là hợp nhất một design system token-based duy nhất, gỡ bỏ CSS legacy và mã chết, chuẩn hóa token màu ngữ nghĩa, thống nhất typography/spacing/layout, bảo đảm WCAG AA và dark mode parity, đồng thời nâng cấp các bề mặt trình bày trọng yếu (badge điểm số tìm kiếm, ảnh xem trước media, sidebar/breadcrumb, thẻ hàng đợi tải lên).

Ràng buộc xuyên suốt (Requirement 9): **chỉ thay đổi lớp trình bày**. Không thay đổi backend, API contract (`frontend/src/api/client.ts`), luồng dữ liệu, logic định tuyến (hash routing trong `App.tsx`), hay props công khai/hành vi của component. Toàn bộ bộ kiểm thử hiện có phải đạt khi refactor hoàn tất mà không sửa kỳ vọng hành vi.

### Hiện trạng (đã xác minh từ codebase)

- **Design system phần lớn đã có**: `frontend/src/index.css` khai báo token HSL cho color/surface/brand, token ngữ nghĩa (`--success`, `--warning`, `--info`, `--destructive`), shadow, transition/motion, radius, font Inter, dark mode qua `[data-theme='dark']`, `prefers-reduced-motion`, scrollbar, và các utility (`.glass`, `.gradient-text`, `.focus-ring`, `.card-surface`, `.skeleton-shimmer`). `frontend/tailwind.config.js` ánh xạ các biến này vào Tailwind theme (colors, borderRadius, boxShadow, easing, zIndex, keyframes/animations).
- **Legacy còn tồn tại**: `frontend/src/App.css` (bộ token riêng `--bg-primary`, `--accent-primary`, `--accent-secondary`...) vẫn được `import './App.css'` trong `App.tsx`.
- **Mã chết**: `frontend/src/components/MediaListPanel.tsx` và `frontend/src/components/Sidebar.tsx` (bản gốc). Đã xác minh: các class legacy (`sidebar`, `panel`, `brand`, `status-pill`...) **chỉ** được tham chiếu bên trong hai component chết này; `AppLayout` import `./Sidebar` là bản `layout/Sidebar.tsx` đang dùng. Do đó việc gỡ import App.css + xóa hai file này không ảnh hưởng tới giao diện đang chạy.
- **Màu hardcode cần thay**: 
  - `components/ui/Badge.tsx`: variant `uploading: bg-blue-500`, `processing: bg-orange-500`, `completed: bg-green-100 text-green-700`, `failed: bg-red-500`.
  - `UploadQueuePanel.tsx`: `statusBarColor` dùng `bg-blue-500`, `bg-amber-500`, `bg-emerald-500`.
  - `DataTable.tsx`: `getStatusColor` dùng `bg-green-100/text-green-700`, `bg-orange-100`, `bg-red-100`, `bg-gray-100`.
  - `SearchResultCard.tsx`: `bg-black/60`, `bg-green-500/5 border-green-500/20`, `bg-primary/5 border-primary/20`.
  - `SearchResultGroup.tsx`: `bg-black/60`.
  - `RuntimeBadge.tsx`: `bg-emerald-500/*`, `text-emerald-500`, `bg-amber-500/*`, `text-amber-500`.
- **Ràng buộc layout trùng lặp cần gỡ**: `SearchPage.tsx` bọc `max-w-7xl mx-auto px-6 py-8`; `MediaDetailPage.tsx` dùng `max-w-7xl mx-auto ...` ở các nhánh loading/error/empty/main. `AppLayout` đã là nơi đặt `max-w-[1440px] mx-auto px-4 py-6 md:px-6 md:py-8 lg:px-10 lg:py-10`.

### Phạm vi

Thuần frontend: `frontend/src/index.css`, `frontend/tailwind.config.js`, các component trong `components/`, `components/ui/`, `components/layout/`, các `pages/`, và một module helper trình bày mới (thuần hàm) để hỗ trợ test. Không động vào `api/client.ts`, `config.ts`, `contexts/`, `hooks/`, `types/api.ts` (ngoài việc có thể bổ sung kiểu trình bày không phá vỡ).

## Architecture

### Nguyên tắc nguồn chân lý duy nhất (single source of truth)

```mermaid
flowchart TD
    A[index.css :root + data-theme=dark<br/>CSS custom properties HSL] --> B[tailwind.config.js<br/>theme.extend maps var --token]
    B --> C[Tailwind utility classes<br/>bg-*, text-*, rounded-*, shadow-*]
    C --> D[UI Primitives<br/>Button, Badge, Card, Skeleton...]
    C --> E[Feature components<br/>SearchResultCard, UploadQueuePanel...]
    D --> F[Pages<br/>Dashboard, Search, Library, MediaDetail]
    E --> F
    F --> G[AppLayout<br/>max-w-[1440px] + padding responsive]
    H[Presentation helpers thuần hàm<br/>lib/presentation.ts] --> D
    H --> E
    style A fill:#e8eaf6
    style G fill:#e0f2f1
    style H fill:#fff3e0
```

Mọi giá trị thị giác chảy một chiều: CSS variables (index.css) → Tailwind theme (tailwind.config.js) → utility classes → component. Không component nào được phép đặt giá trị màu/spacing/radius/shadow trực tiếp bằng palette Tailwind hoặc literal; tất cả phải tham chiếu token ngữ nghĩa.

### Phân lớp trách nhiệm

| Lớp | Tệp | Trách nhiệm sau refactor |
|-----|-----|--------------------------|
| Token layer | `index.css`, `tailwind.config.js` | Khai báo & ánh xạ toàn bộ Design_Token; loại token trùng/không dùng |
| Presentation helpers | `lib/presentation.ts` (mới) | Hàm thuần ánh xạ trạng thái→token, predicate hiển thị badge, chọn nguồn ảnh xem trước (để tách logic trình bày dễ kiểm thử, không đổi hành vi) |
| UI primitives | `components/ui/*` | Áp token; Badge có tập variant trạng thái ngữ nghĩa cố định |
| Feature components | `components/*` | Thay màu hardcode bằng token; dùng helper trình bày |
| Layout | `components/layout/AppLayout.tsx`, `Sidebar.tsx` | AppLayout là nơi duy nhất khống chế width/padding; Sidebar dùng token cho active/hover/focus |
| Pages | `pages/*` | Gỡ ràng buộc width/padding cấp trang; theo quy ước AppLayout & grid chung |

### Chiến lược di trú an toàn (đảm bảo build luôn xanh)

Thứ tự thực hiện được thiết kế để mỗi bước giữ giao diện và test ở trạng thái hợp lệ (Requirement 2.2, 6.2, 9.5):

1. **Mở rộng token & Tailwind trước** — thêm bất kỳ token còn thiếu (ví dụ alias semantic cho `secondary`/`info` foreground nếu cần) trước khi dùng.
2. **Thêm helper trình bày thuần hàm** — không thay đổi component nào, chỉ tạo nguồn logic để các component gọi và để test tham chiếu.
3. **Refactor token màu trong component** — Badge, UploadQueuePanel, DataTable, SearchResult*, RuntimeBadge.
4. **Hợp nhất layout** — xác nhận AppLayout cung cấp đủ width/padding, rồi mới gỡ `max-w-7xl ...` khỏi SearchPage/MediaDetailPage.
5. **Gỡ import `App.css`** khỏi `App.tsx`, sau đó **xóa `App.css`** và **xóa dead components** (chỉ sau khi xác nhận không còn tham chiếu — đã xác minh hiện chỉ dead components tự dùng).
6. **Chạy `npm run build` + `npm run test`** sau mỗi nhóm thay đổi.

## Components and Interfaces

### 1. Token layer: `index.css` + `tailwind.config.js`

**Mục tiêu (R1, R3, R4, R5, R11, R12):** giữ index.css/tailwind.config.js là nguồn chân lý, bảo đảm sáu nhóm token đầy đủ và mọi semantic token đều có giá trị cho cả hai theme.

- Giữ nguyên cấu trúc HSL hiện có. Bổ sung (nếu thiếu) foreground tương ứng cho mọi nhóm semantic để bảo đảm cặp nền/chữ: `primary`, `secondary`, `brand`, `success`, `warning`, `info`, `destructive`, `surface`. Hiện `success/warning/info/destructive` đã có `*-foreground`; `secondary` đã có; `surface` dùng `card-foreground/foreground` làm chữ.
- Đăng ký các nhóm còn thiếu vào `tailwind.config.js > theme.extend.colors` để dùng được dạng utility (`bg-success text-success-foreground`, `bg-warning`, `bg-info`, ...). Hiện config **chưa** map `success/warning/info` thành color key — đây là bổ sung bắt buộc để component thôi dùng palette hardcode.
- Type_Scale (R4): khai báo thang tiêu đề/văn bản thống nhất. Tận dụng `font-feature-settings` đã có trên `body`/heading. Chuẩn hóa cấp h1 dùng chung một lớp tiện ích (ví dụ `text-3xl md:text-4xl font-bold tracking-tight`) áp dụng nhất quán trên 4 page.
- Spacing/radius/shadow/motion (R5): giữ thang radius (`sm..3xl`), shadow (`sm..xl`, `glow-*`), easing (`spring/smooth/out-expo`), animation keyframes đã có. Mọi animation component phải dùng các animation token này (lớp `animate-*`) hoặc biến `--transition-*`.
- Dọn token trùng/không dùng (R1.5): rà soát và loại token không còn tham chiếu sau khi xóa App.css (App.css mang bộ `--accent-*`, `--bg-*` riêng — sẽ biến mất hoàn toàn cùng file).

### 2. Presentation helpers (mới): `frontend/src/lib/presentation.ts`

Tách phần logic trình bày thuần để (a) loại bỏ trùng lặp ánh xạ trạng thái rải rác trong nhiều component và (b) tạo điểm kiểm thử property rõ ràng. Đây là **hàm thuần, không đổi hành vi quan sát được** của component.

```ts
import type { MediaSummary, UploadQueueStatus, UploadQueueItem } from '@/types/api'

// Variant trạng thái dùng chung cho Badge (ánh xạ tới token ngữ nghĩa cố định)
export type StatusBadgeVariant = 'info' | 'warning' | 'success' | 'destructive'

// Ánh xạ CỐ ĐỊNH trạng thái -> variant ngữ nghĩa (R3.4, R3.5, R16.3)
//  uploading/pending -> info, processing -> warning, completed -> success, failed -> destructive
export function statusToBadgeVariant(status: UploadQueueStatus): StatusBadgeVariant

// Lớp Tailwind nền/chữ cho từng variant, lấy từ token ngữ nghĩa (không palette hardcode)
export function statusBadgeClasses(status: UploadQueueStatus): string

// Lớp token cho thanh tiến trình theo trạng thái (R16.2) — cùng nguồn ánh xạ với badge
export function statusProgressBarClass(status: UploadQueueStatus): string

// Predicate hiển thị badge Boost: chỉ hiện khi rerank_boost > 0 (strictly positive) (R13.4, R13.5)
export function shouldShowBoostBadge(rerankBoost: number): boolean

// Nguồn ảnh xem trước media + fallback theo media_type (R14.1–14.3, R16.4)
export type PreviewSource =
  | { kind: 'image'; url: string }
  | { kind: 'fallback'; mediaType: 'image' | 'video' }
export function resolveMediaPreviewSource(
  media: Pick<MediaSummary, 'thumbnail' | 'file' | 'media_type'>
): PreviewSource
export function resolveUploadPreviewSource(
  item: Pick<UploadQueueItem, 'previewUrl' | 'mediaType'>
): PreviewSource
```

Lưu ý quan trọng về bảo toàn hành vi: `statusToBadgeVariant` phải tạo ra **đúng** kết quả thị giác mà các test hiện có kỳ vọng. Các test không kiểm tra tên class màu cụ thể (chúng kiểm tra text/aria/cấu trúc), nên việc đổi nền badge từ palette sang token là an toàn.

### 3. UI Primitive: `components/ui/Badge.tsx`

**Thay đổi (R3.2, R3.3, R8.4, R13.6):** thay 4 variant trạng thái palette-hardcode bằng token ngữ nghĩa, giữ nguyên tên variant để không phá vỡ nơi gọi (`MediaCard`, `UploadQueuePanel`, `MediaDetailPage` đang dùng `variant="uploading|processing|completed|failed"`).

```ts
// badgeVariants.variants.variant — sau refactor (token-based)
uploading:  "bg-info text-info-foreground",
processing: "bg-warning text-warning-foreground",
completed:  "bg-success text-success-foreground",
failed:     "bg-destructive text-destructive-foreground",
```

- Giữ `default`, `secondary`, `destructive`, `outline` như cũ (đã token-based).
- Tên variant `uploading` được giữ làm nhãn variant trình bày cho cả `uploading` và `pending` (nơi gọi map `pending -> uploading` variant), khớp ánh xạ `info`.
- Status_Badge và Search_Explanation_Badge dùng cùng UI_Primitive Badge này → đồng nhất bo góc/kích thước/độ tương phản (R13.6).

### 4. Feature components

- **`SearchResultCard.tsx`** (R13): 
  - Chip điểm/score overlay: thay `bg-black/60 text-white` bằng token overlay nhất quán (ví dụ một lớp tiện ích `bg-foreground/70 text-background` hoặc token surface tối chuyên cho overlay). Phải đạt tương phản AA trên ảnh.
  - Badge "Boost": thay `bg-green-500/5 border-green-500/20 text-foreground` bằng token `success` (nền/viền/chữ theo token), và **chỉ render khi `shouldShowBoostBadge(item.explanation.rerank_boost)`** (giữ nguyên điều kiện `> 0` hiện có).
  - Badge context (`Exact phrase`, `Rich caption`): thay `bg-primary/5 border-primary/20` bằng token (ví dụ `bg-accent text-accent-foreground` hoặc `border-border` + `text-foreground`).
  - Giữ nguyên text/nhãn/cấu trúc DOM, `aria-label`, thứ tự badge → bảo toàn `SearchResultCard.test.tsx`.
- **`SearchResultGroup.tsx`** (R13.6, R8.5): chip `bg-black/60` → token overlay như trên; giữ nguyên hành vi expand/collapse và `aria-label` → bảo toàn `SearchResultGroup.test.tsx`.
- **`UploadQueuePanel.tsx`** (R16): 
  - `statusBarColor` → `statusProgressBarClass(status)` (token). 
  - Status badge dùng `statusToBadgeVariant`. 
  - Hiệu ứng tiến trình `animate-shimmer` (đã là animation token) cho uploading/processing (R16.5). 
  - Ảnh xem trước/fallback qua `resolveUploadPreviewSource` (R16.4). Giữ nguyên `VideoPreviewFrame` (logic tạo thumbnail từ blob — đây là hành vi, không đổi).
- **`DataTable.tsx`** (R3.2, R14.1): `getStatusColor` → dùng `statusBadgeClasses`/`statusToBadgeVariant`; thumbnail cột dùng `resolveMediaPreviewSource` (ưu tiên `thumbnail`, fallback theo `media_type`).
- **`MediaCard.tsx`** (R14.1–14.4): hiện đã ưu tiên `media.thumbnail ?? (isVideo ? null : media.file)`. Chuẩn hóa qua `resolveMediaPreviewSource` để nhất quán tỉ lệ khung hình (`aspect-[16/10]`) và quy ước bo góc; giữ `onError` fallback (R14.3). Badge trạng thái đã dùng variant — chỉ hưởng lợi từ Badge token mới.
- **`RuntimeBadge.tsx`** (R3.2): thay `emerald-*`/`amber-*` bằng token `success`/`warning` (GPU→success, CPU→warning) giữ nguyên cấu trúc và nhãn.

### 5. Layout: `AppLayout.tsx` + pages

- **`AppLayout.tsx`** (R6.1, R6.2): giữ là nơi duy nhất đặt `max-w-[1440px] mx-auto` + padding responsive. Không thay đổi cấu trúc; xác nhận đủ trước khi gỡ ràng buộc cấp trang.
- **`SearchPage.tsx`** (R6.3): bỏ wrapper `max-w-7xl mx-auto px-6 py-8`, thay bằng container trung tính (`space-y-*`), để AppLayout chịu trách nhiệm width/padding. Grid kết quả giữ `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4` (R6.5, R7).
- **`MediaDetailPage.tsx`** (R6.3, R15.2): bỏ `max-w-7xl mx-auto ...` ở mọi nhánh (loading/error/empty/main). Breadcrumb + nút Back dùng token & Type_Scale (đã gần đạt: `text-muted-foreground hover:text-foreground`, separator `/`). Bảo đảm focus ring token (`focus-visible:ring-ring`). Yêu cầu breadcrumb chỉ áp dụng cho MediaDetailPage.
- **`DashboardPage.tsx`, `LibraryPage.tsx`**: giữ container hiện tại (đã không tự giới hạn max-width), bảo đảm dùng cùng quy ước grid `grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4`.

### 6. Sidebar điều hướng: `components/layout/Sidebar.tsx`

(R15.1, R15.3, R15.4, R7.4) — Sidebar hiện đã token-based phần lớn (`bg-brand/10 text-brand` cho active, `aria-current`, focus ring token, mobile dùng `Sheet`). Việc cần làm:
- Xác nhận trạng thái active/hover/disabled đều dùng token (`brand`, `muted`, `ring`) — đã đạt; chỉ chuẩn hóa nếu còn literal.
- Giữ nguyên `aria-current='page'` và logic `onNavigate` (R15.5).

### 7. Gỡ legacy & dead code

- `App.tsx`: xóa dòng `import './App.css'` (R2.1).
- Xóa `frontend/src/App.css` (R2.2) — sau khi xác nhận không còn tham chiếu class legacy ngoài dead components.
- Xóa `frontend/src/components/MediaListPanel.tsx` và `frontend/src/components/Sidebar.tsx` (R2.3).
- Kết quả: số tham chiếu legacy = 0; `npm run build` thành công (R2.5).

## Data Models

Không thay đổi bất kỳ mô hình dữ liệu API nào (R9.1, R14.5). Tái sử dụng nguyên trạng `frontend/src/types/api.ts`: `MediaSummary`, `MediaDetail`, `SearchResult`, `SearchResultExplanation`, `UploadQueueItem`, `ProcessingStatus`, `UploadQueueStatus`.

Chỉ bổ sung **kiểu trình bày nội bộ** (không phá vỡ, không thuộc API contract) trong `lib/presentation.ts`:

```ts
type StatusBadgeVariant = 'info' | 'warning' | 'success' | 'destructive'

type PreviewSource =
  | { kind: 'image'; url: string }
  | { kind: 'fallback'; mediaType: 'image' | 'video' }
```

Ánh xạ trạng thái cố định (bảng tham chiếu duy nhất, dùng cho cả Status_Badge và thanh tiến trình):

| Trạng thái (`UploadQueueStatus`) | Variant ngữ nghĩa | Token nền/chữ |
|----------------------------------|-------------------|---------------|
| `uploading` | `info` | `bg-info / text-info-foreground` |
| `pending` | `info` | `bg-info / text-info-foreground` |
| `processing` | `warning` | `bg-warning / text-warning-foreground` |
| `completed` | `success` | `bg-success / text-success-foreground` |
| `failed` | `destructive` | `bg-destructive / text-destructive-foreground` |

Quy tắc chọn ảnh xem trước (`resolveMediaPreviewSource`):

| Điều kiện | Kết quả |
|-----------|---------|
| `thumbnail` khác null/rỗng | `{ kind: 'image', url: thumbnail }` |
| `thumbnail` null & `media_type === 'image'` & có `file` | `{ kind: 'image', url: file }` |
| còn lại | `{ kind: 'fallback', mediaType }` |

`SearchResultExplanation` được dùng để suy ra hiển thị Search_Explanation_Badge:
- Semantic ← `vector_score`, Caption ← `keyword_score`, Boost ← `rerank_boost` (chỉ khi `> 0`), nhãn ← `match_type`, `exact_phrase_match`, `rich_caption`. Không đổi cấu trúc dữ liệu.

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

Phần lớn yêu cầu của feature này thuộc lớp trình bày (CSS token, layout, dark mode, accessibility, dọn legacy) và **không** phù hợp với property-based testing — chúng được kiểm chứng bằng snapshot/example test, kiểm tra grep/lint (không còn palette hardcode), build/smoke, bộ test hiện có, và rà soát tiếp cận thủ công (xem Testing Strategy).

Tuy nhiên, thiết kế tách một lớp **hàm thuần** trong `lib/presentation.ts` (ánh xạ trạng thái→token, predicate hiển thị badge Boost, phân giải nguồn ảnh xem trước). Lớp này có không gian đầu vào lớn (mọi trạng thái, mọi giá trị `rerank_boost`, mọi tổ hợp `thumbnail`/`media_type`/`previewUrl`) nên phù hợp PBT. Sau bước reflection để loại trùng lặp, còn lại **bốn** property.

### Property 1: Ánh xạ trình bày trạng thái là cố định, toàn phần và phân biệt

*For any* giá trị `UploadQueueStatus` (`uploading`, `pending`, `processing`, `completed`, `failed`) và *for any* giá trị "override" tùy ý mà nơi gọi cố truyền vào, hàm ánh xạ trình bày trạng thái phải trả về variant ngữ nghĩa cố định theo bảng (`uploading`→`info`, `pending`→`info`, `processing`→`warning`, `completed`→`success`, `failed`→`destructive`), bỏ qua hoàn toàn override; ánh xạ là toàn phần trên tập trạng thái, và lớp token của thanh tiến trình suy ra từ cùng ánh xạ này; ba trạng thái `processing`/`completed`/`failed` cho ra ba variant phân biệt.

**Validates: Requirements 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 8.4, 16.2, 16.3**

### Property 2: Hiển thị badge Boost chỉ phụ thuộc dấu của rerank_boost

*For any* giá trị `rerank_boost` (số thực bất kỳ: âm, 0, dương, rất lớn) và *for any* trạng thái mật độ UI / collapsed, badge Boost được hiển thị **khi và chỉ khi** `rerank_boost > 0` (strictly positive); kết quả không phụ thuộc vào mật độ UI hay trạng thái thu gọn.

**Validates: Requirements 13.4, 13.5**

### Property 3: Phân giải nguồn ảnh xem trước cho media

*For any* `MediaSummary` (với `thumbnail` là chuỗi khác rỗng hoặc null, `file` bất kỳ, `media_type` ∈ {image, video}): nếu `thumbnail` khác null/rỗng thì kết quả là ảnh dùng đúng `thumbnail`; nếu `thumbnail` null và `media_type === 'image'` và có `file` thì kết quả là ảnh dùng `file`; trong mọi trường hợp còn lại kết quả là fallback đúng theo `media_type`. Hàm là toàn phần và không bao giờ trả về URL rỗng cho nhánh ảnh.

**Validates: Requirements 14.1, 14.2**

### Property 4: Phân giải nguồn ảnh xem trước cho mục tải lên

*For any* `UploadQueueItem` (với `previewUrl` có hoặc không, `mediaType` ∈ {image, video, undefined}): nếu có `previewUrl` thì kết quả là ảnh dùng đúng `previewUrl`; nếu không có `previewUrl` thì kết quả là fallback đúng theo `mediaType` (mặc định an toàn khi `mediaType` undefined).

**Validates: Requirements 16.4**

## Error Handling

Vì đây là refactor lớp trình bày, xử lý lỗi tập trung vào suy biến đồ họa (graceful degradation) chứ không phải luồng lỗi nghiệp vụ (giữ nguyên).

- **Ảnh xem trước hỏng (R14.3):** giữ `onError` trên `<img>` để ẩn ảnh hỏng và hiển thị fallback theo `media_type`. `MediaCard` đã có `onError`; `DataTable` đã có; chuẩn hóa để mọi nơi hiển thị thumbnail đều có fallback. `resolveMediaPreviewSource` quyết định nguồn ban đầu, `onError` xử lý lỗi tải runtime.
- **Token chưa định nghĩa khi phát triển (R11.5):** dùng cú pháp CSS `var(--token, <default>)` ở nơi rủi ro để theme vẫn chuyển được và rơi về giá trị mặc định an toàn thay vì vỡ giao diện. Việc chuyển `data-theme` trong `ThemeContext` không phụ thuộc vào sự tồn tại của từng token cụ thể.
- **Trạng thái tương tác lỗi (R12.3):** các variant của UI_Primitive luôn có trạng thái `default`; nếu lớp hover/active không áp dụng được, phần tử vẫn hiển thị ở trạng thái default hợp lệ (không có trạng thái "trống").
- **Trạng thái dữ liệu rỗng/lỗi:** tiếp tục dùng `EmptyState`/`ErrorState` dùng chung (R8.3) — không thay đổi điều kiện kích hoạt, chỉ bảo đảm token.
- **prefers-reduced-motion (R10.4):** media query trong `index.css` rút gọn mọi animation/transition (kể cả spinner, shimmer tiến trình) về ~0ms; không cần xử lý theo từng component.
- **Bảo toàn lỗi nghiệp vụ:** mọi `try/catch`, `toast.error`, thông điệp lỗi upload/delete/search giữ nguyên (R9.2) — chỉ phần trình bày của thông báo dùng token.

## Testing Strategy

### Cách tiếp cận kép

- **Property-based tests**: chỉ cho lớp hàm thuần `lib/presentation.ts` (4 property ở trên).
- **Example/unit & snapshot tests**: cho rendering, layout, trạng thái tương tác, dark mode, accessibility điểm đại diện.
- **Static guards (grep/lint) & build/smoke**: cho các invariant tĩnh (không palette hardcode, không tham chiếu legacy, token đầy đủ ở cả hai theme, build xanh).
- **Bộ test hiện có**: phải đạt nguyên trạng, không sửa kỳ vọng hành vi.

### Property-based testing

- **Thư viện**: dùng `fast-check` cùng Vitest (hệ test hiện tại là Vitest 4). Không tự cài đặt PBT từ đầu. Thêm `fast-check` vào devDependencies.
- **Cấu hình**: tối thiểu **100 iterations** mỗi property (`fc.assert(fc.property(...), { numRuns: 100 })`).
- **Generators**:
  - Trạng thái: `fc.constantFrom('uploading','pending','processing','completed','failed')`.
  - Boost: `fc.double()` (bao gồm âm, 0, dương, lớn) và một nhánh `fc.double({ min: Number.MIN_VALUE })` cho strictly-positive.
  - Override tùy ý cho Property 1: `fc.anything()` mô phỏng nơi gọi cố override token.
  - Media: bản ghi với `thumbnail` ∈ {chuỗi không rỗng, '', null}, `file` ∈ {chuỗi, ''}, `media_type` ∈ {image, video}.
  - Upload item: `previewUrl` ∈ {chuỗi, undefined}, `mediaType` ∈ {image, video, undefined}.
- **Vị trí test**: `frontend/src/lib/presentation.test.ts`.
- **Tag mỗi property test** bằng comment tham chiếu design:
  - `// Feature: ui-ux-modernization, Property 1: Ánh xạ trình bày trạng thái là cố định, toàn phần và phân biệt`
  - `// Feature: ui-ux-modernization, Property 2: Hiển thị badge Boost chỉ phụ thuộc dấu của rerank_boost`
  - `// Feature: ui-ux-modernization, Property 3: Phân giải nguồn ảnh xem trước cho media`
  - `// Feature: ui-ux-modernization, Property 4: Phân giải nguồn ảnh xem trước cho mục tải lên`
- Mỗi property cài đặt bằng **một** property-based test.

### Unit / example / snapshot tests (chọn lọc, tránh dư thừa)

- **Badge token**: render Badge cho 4 variant trạng thái, xác nhận dùng lớp token (`bg-info`, `bg-warning`, `bg-success`, `bg-destructive`) thay vì palette.
- **UploadQueuePanel / DataTable / MediaCard / RuntimeBadge**: render đại diện, xác nhận lớp token và fallback thumbnail.
- **SearchResultCard / SearchResultGroup / SearchPage**: dựa vào **bộ test hiện có** (đã bao trùm text/aria/cấu trúc, điều hướng bàn phím, nhóm video-scene, legend). Không thêm test trùng; chỉ bảo đảm chúng vẫn xanh sau khi đổi token (R13.8, R9.5).
- **Layout**: test AppLayout chứa `max-w-[1440px]`; test SearchPage/MediaDetailPage **không** còn `max-w-7xl` (có thể bằng kiểm tra container/snapshot).
- **Accessibility**: 
  - Xác nhận `skip-nav` và các `aria-*`/`aria-current` được giữ.
  - Xác nhận focus dùng `focus-visible:ring-ring`.
  - Tương phản WCAG AA cho các cặp token ở cả hai theme: rà soát bằng công cụ tính tương phản; ghi chú rằng xác thực đầy đủ cần kiểm thử thủ công với công nghệ hỗ trợ.
- **Dark mode parity**: test đại diện đặt `data-theme='dark'` và xác nhận token áp dụng; kiểm tra completeness của token bằng static guard bên dưới.

### Static guards & build/smoke

- **No hardcoded palette (R1.3, R3.2, R11.4, R13.2)**: bài test/lệnh grep bảo đảm không còn các literal bị cấm trong các tệp đã liệt kê (`bg-blue-500`, `bg-amber-500`, `bg-emerald-500`, `bg-orange-100`, `bg-green-100`, `bg-green-700`, `bg-green-500/5`, `border-green-500/20`, `bg-black/60`, `bg-red-500`, `text-green-700`, `emerald-500`, `amber-500`...). Có thể hiện thực bằng một test Vitest đọc nội dung file nguồn.
- **No legacy references (R2.1, R2.4, R2.5)**: grep bảo đảm không còn `import './App.css'` và không còn class legacy (`app-shell`, `panel`, `sidebar`, `nav-item`, `status-pill`, `hero-card`, `result-card`, `queue-item`, `dropzone`, `search-bar`) trong tệp live.
- **Dead code removed (R2.3)**: xác nhận `MediaListPanel.tsx` và `components/Sidebar.tsx` (bản gốc) không tồn tại và không bị import.
- **Token completeness (R3.1, R11.3, R1.4)**: test đọc `index.css` xác nhận mỗi semantic token (`--primary/secondary/brand/success/warning/info/destructive/surface` + `*-foreground`) xuất hiện trong cả khối `:root` và `[data-theme='dark']`; xác nhận sáu nhóm token hiện diện.
- **Tailwind mapping**: xác nhận `tailwind.config.js` map `success/warning/info` thành color key dùng được dạng utility.
- **Build (R2.5, R9.5)**: `npm run build` (tsc + vite) phải thành công.
- **Toàn bộ suite (R9.5)**: `npm run test` (vitest --run) phải xanh hoàn toàn.

### Ghi chú thực thi

- Các lệnh dài (dev server/watch) không chạy trong quá trình tự động; dùng `npm run test` (đã có cờ `--run`) và `npm run build` cho kiểm chứng một lần.
- Dọn sạch mọi tệp tạm sinh ra trong quá trình kiểm chứng.
