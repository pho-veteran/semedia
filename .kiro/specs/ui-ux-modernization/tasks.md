# Implementation Plan: UI/UX Modernization

## Overview

Kế hoạch triển khai refactor lớp trình bày của frontend "Semedia" theo `requirements.md` và `design.md`. Cách tiếp cận theo chiến lược di trú an toàn của design: mở rộng token trước, thêm lớp hàm thuần trình bày, refactor token màu trong component, hợp nhất layout, rồi gỡ legacy/dead code; mỗi nhóm thay đổi đều được kiểm chứng bằng `npm run test` và `npm run build`.

Ngôn ngữ triển khai: **TypeScript + React** (theo codebase và design hiện có). Test framework: **Vitest 4**; property-based testing dùng **fast-check** cho lớp hàm thuần `lib/presentation.ts`.

Ràng buộc xuyên suốt (Requirement 9): chỉ thay đổi lớp trình bày — không thay đổi API contract, luồng dữ liệu, logic định tuyến hay props/hành vi công khai của component. Bộ test hiện có phải đạt nguyên trạng khi refactor hoàn tất.

## Tasks

- [x] 1. Mở rộng & hợp nhất token layer (nguồn chân lý duy nhất)
  - [x] 1.1 Bổ sung và xác nhận Semantic_Color_Token trong `frontend/src/index.css`
    - Bảo đảm mỗi nhóm token (`primary`, `secondary`, `brand`, `success`, `warning`, `info`, `destructive`, `surface`) có cặp nền + foreground và có giá trị xác định trong cả khối `:root` và `[data-theme='dark']`
    - Xác nhận đầy đủ sáu nhóm token (color, typography, spacing, radius, shadow/elevation, motion) và Type_Scale/Spacing_Scale/radius/shadow/motion hiện diện
    - Dùng cú pháp `var(--token, <default>)` ở nơi rủi ro để theme vẫn chuyển được và rơi về giá trị mặc định an toàn
    - _Requirements: 1.1, 1.4, 3.1, 4.1, 5.1, 5.2, 5.4, 11.3, 11.5_

  - [x] 1.2 Map `success`/`warning`/`info` thành color key dùng được dạng utility trong `frontend/tailwind.config.js`
    - Đăng ký `success`/`success-foreground`, `warning`/`warning-foreground`, `info`/`info-foreground` vào `theme.extend.colors` để component dùng được `bg-success text-success-foreground`...
    - Giữ nguyên ánh xạ borderRadius/boxShadow/easing/zIndex/keyframes hiện có
    - _Requirements: 1.1, 1.2, 3.1, 5.2, 5.4_

  - [x] 1.3 Viết static guard test cho tính đầy đủ token
    - Đọc `index.css` xác nhận mỗi semantic token (+ `*-foreground`) xuất hiện trong cả `:root` và `[data-theme='dark']`
    - Xác nhận `tailwind.config.js` map `success`/`warning`/`info` thành color key
    - _Requirements: 1.4, 3.1, 11.3_

- [x] 2. Tạo lớp hàm thuần trình bày `frontend/src/lib/presentation.ts`
  - [x] 2.1 Triển khai các hàm thuần ánh xạ trình bày
    - `statusToBadgeVariant`, `statusBadgeClasses`, `statusProgressBarClass` theo bảng ánh xạ cố định (`uploading`/`pending`→`info`, `processing`→`warning`, `completed`→`success`, `failed`→`destructive`), bỏ qua mọi override
    - `shouldShowBoostBadge(rerankBoost)` trả về true khi và chỉ khi `rerankBoost > 0`
    - `resolveMediaPreviewSource` và `resolveUploadPreviewSource` trả về `{ kind: 'image', url }` hoặc `{ kind: 'fallback', mediaType }` theo quy tắc trong design
    - Định nghĩa kiểu trình bày nội bộ `StatusBadgeVariant` và `PreviewSource` (không thuộc API contract)
    - _Requirements: 3.4, 3.7, 3.8, 13.4, 14.1, 14.2, 16.2, 16.3, 16.4_

  - [x] 2.2 Viết property test cho ánh xạ trình bày trạng thái (fast-check, ≥100 iterations)
    - **Property 1: Ánh xạ trình bày trạng thái là cố định, toàn phần và phân biệt**
    - **Validates: Requirements 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 8.4, 16.2, 16.3**

  - [x] 2.3 Viết property test cho hiển thị badge Boost (fast-check, ≥100 iterations)
    - **Property 2: Hiển thị badge Boost chỉ phụ thuộc dấu của rerank_boost**
    - **Validates: Requirements 13.4, 13.5**

  - [x] 2.4 Viết property test cho phân giải nguồn ảnh xem trước media (fast-check, ≥100 iterations)
    - **Property 3: Phân giải nguồn ảnh xem trước cho media**
    - **Validates: Requirements 14.1, 14.2**

  - [x] 2.5 Viết property test cho phân giải nguồn ảnh xem trước mục tải lên (fast-check, ≥100 iterations)
    - **Property 4: Phân giải nguồn ảnh xem trước cho mục tải lên**
    - **Validates: Requirements 16.4**

- [x] 3. Checkpoint - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Refactor UI_Primitive Badge sang token ngữ nghĩa
  - [x] 4.1 Cập nhật `frontend/src/components/ui/Badge.tsx`
    - Thay 4 variant trạng thái palette-hardcode bằng token: `uploading: bg-info text-info-foreground`, `processing: bg-warning text-warning-foreground`, `completed: bg-success text-success-foreground`, `failed: bg-destructive text-destructive-foreground`
    - Giữ nguyên tên variant và các variant token-based hiện có (`default`, `secondary`, `destructive`, `outline`) để không phá vỡ nơi gọi
    - _Requirements: 3.2, 3.3, 8.4, 13.6_

  - [x] 4.2 Viết unit test cho Badge token
    - Render 4 variant trạng thái, xác nhận dùng lớp token (`bg-info`, `bg-warning`, `bg-success`, `bg-destructive`) thay vì palette
    - _Requirements: 3.2, 3.3_

- [x] 5. Refactor token màu trong feature components
  - [x] 5.1 Cập nhật `frontend/src/components/RuntimeBadge.tsx`
    - Thay `emerald-*`/`amber-*` bằng token `success` (GPU) / `warning` (CPU); giữ nguyên cấu trúc và nhãn
    - _Requirements: 3.2, 11.4_

  - [x] 5.2 Cập nhật `frontend/src/components/DataTable.tsx`
    - Thay `getStatusColor` bằng `statusBadgeClasses`/`statusToBadgeVariant`; thumbnail cột dùng `resolveMediaPreviewSource` với fallback theo `media_type` và `onError`
    - _Requirements: 3.2, 14.1, 14.2, 14.3, 14.4_

  - [x] 5.3 Cập nhật `frontend/src/components/MediaCard.tsx`
    - Chuẩn hóa nguồn ảnh xem trước qua `resolveMediaPreviewSource`, giữ tỉ lệ khung hình và bo góc nhất quán, giữ `onError` fallback
    - _Requirements: 14.1, 14.2, 14.3, 14.4_

  - [x] 5.4 Cập nhật `frontend/src/components/UploadQueuePanel.tsx`
    - `statusBarColor` → `statusProgressBarClass`; status badge dùng `statusToBadgeVariant`; ảnh xem trước/fallback qua `resolveUploadPreviewSource`; hiệu ứng tiến trình dùng animation token (`animate-shimmer`) cho uploading/processing; giữ nguyên `VideoPreviewFrame`
    - _Requirements: 3.2, 16.1, 16.2, 16.3, 16.4, 16.5_

  - [x] 5.5 Cập nhật `frontend/src/components/SearchResultCard.tsx`
    - Thay `bg-black/60` (chip điểm), `bg-green-500/5 border-green-500/20` (Boost), `bg-primary/5 border-primary/20` (context badge) bằng token ngữ nghĩa; badge Boost chỉ render khi `shouldShowBoostBadge(item.explanation.rerank_boost)`; áp Type_Scale cho nhãn; giữ nguyên text/nhãn/cấu trúc DOM/`aria-label`/thứ tự badge
    - _Requirements: 3.2, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.8_

  - [x] 5.6 Cập nhật `frontend/src/components/SearchResultGroup.tsx`
    - Thay chip `bg-black/60` bằng token overlay; giữ nguyên hành vi expand/collapse và `aria-label`
    - _Requirements: 3.2, 8.5, 13.2, 13.6, 13.8_

  - [x] 5.7 Viết unit test token cho feature components
    - Render đại diện UploadQueuePanel/DataTable/MediaCard/RuntimeBadge, xác nhận dùng lớp token và fallback thumbnail; không trùng với bộ test hiện có của SearchResult*
    - _Requirements: 3.2, 14.1, 14.2, 16.2_

- [x] 6. Checkpoint - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Hợp nhất layout và điều hướng
  - [x] 7.1 Xác nhận `frontend/src/components/layout/AppLayout.tsx`
    - Bảo đảm AppLayout là nơi duy nhất đặt `max-w-[1440px] mx-auto` + padding responsive trước khi gỡ ràng buộc cấp trang
    - _Requirements: 6.1, 6.2_

  - [x] 7.2 Gỡ ràng buộc width/padding trong `frontend/src/pages/SearchPage.tsx`
    - Bỏ wrapper `max-w-7xl mx-auto px-6 py-8`, thay bằng container trung tính; giữ grid kết quả `grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4`
    - _Requirements: 6.3, 6.4, 6.5, 7.1, 7.2, 7.3_

  - [x] 7.3 Gỡ ràng buộc width/padding & chuẩn hóa breadcrumb trong `frontend/src/pages/MediaDetailPage.tsx`
    - Bỏ `max-w-7xl mx-auto ...` ở mọi nhánh (loading/error/empty/main); breadcrumb + nút Back dùng token & Type_Scale, focus ring `focus-visible:ring-ring`
    - _Requirements: 6.3, 6.4, 15.2, 15.4_

  - [x] 7.4 Chuẩn hóa grid container trong `frontend/src/pages/DashboardPage.tsx` và `frontend/src/pages/LibraryPage.tsx`
    - Bảo đảm dùng cùng quy ước grid/gap (`grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4`) và theo container của AppLayout
    - _Requirements: 6.4, 6.5, 7.2, 7.3_

  - [x] 7.5 Xác nhận token cho `frontend/src/components/layout/Sidebar.tsx`
    - Bảo đảm trạng thái active/hover/disabled dùng token (`brand`, `muted`, `ring`); giữ `aria-current='page'`, logic `onNavigate`, và dạng `Sheet` trên mobile
    - _Requirements: 7.4, 15.1, 15.3, 15.4, 15.5_

  - [x] 7.6 Viết test layout
    - Xác nhận AppLayout chứa `max-w-[1440px]`; SearchPage/MediaDetailPage không còn `max-w-7xl`; focus ring dùng `focus-visible:ring-ring`; `data-theme='dark'` áp dụng token đại diện
    - _Requirements: 6.1, 6.3, 10.2, 11.1_

- [x] 8. Gỡ legacy stylesheet & dead code
  - [x] 8.1 Gỡ `import './App.css'` khỏi `frontend/src/App.tsx`
    - _Requirements: 2.1_

  - [x] 8.2 Xóa Legacy_Stylesheet và Dead_Component
    - Xóa `frontend/src/App.css`, `frontend/src/components/MediaListPanel.tsx`, `frontend/src/components/Sidebar.tsx` (bản gốc) sau khi xác nhận không còn tham chiếu class legacy ngoài dead components
    - _Requirements: 2.2, 2.3, 2.4_

  - [x] 8.3 Viết static guard test cho legacy & palette hardcode
    - Grep nội dung file nguồn live: không còn `import './App.css'`, không còn class legacy, không còn literal palette bị cấm (`bg-blue-500`, `bg-amber-500`, `bg-emerald-500`, `bg-orange-100`, `bg-green-100`, `text-green-700`, `bg-green-500/5`, `border-green-500/20`, `bg-black/60`, `bg-red-500`, `emerald-500`, `amber-500`...)
    - _Requirements: 1.3, 2.1, 2.4, 2.5, 3.2, 11.4, 13.2_

- [x] 9. Final checkpoint - Ensure all tests pass (`npm run test`) và build thành công (`npm run build`), ask the user if questions arise.

## Notes

- Các sub-task đánh dấu `*` là optional (test) và có thể bỏ qua cho MVP nhanh; sub-task không có `*` là core và phải triển khai.
- Mỗi task tham chiếu các sub-requirement cụ thể để truy vết.
- Property test chỉ áp dụng cho lớp hàm thuần `lib/presentation.ts` (4 property); phần còn lại của feature là lớp trình bày, được kiểm chứng bằng example/snapshot test, static guard (grep/lint), build/smoke và bộ test hiện có.
- Property test dùng `fast-check` với tối thiểu 100 iterations mỗi property; mỗi property cài đặt bằng một property-based test và gắn comment tham chiếu `// Feature: ui-ux-modernization, Property N: ...`.
- Bộ test hiện có (`SearchResultCard.test.tsx`, `SearchResultGroup.test.tsx`, `SearchPage.test.tsx`, `searchResults.test.ts`) phải đạt nguyên trạng, không sửa kỳ vọng hành vi.
- Các lệnh dài (dev server/watch) không chạy tự động; dùng `npm run test` (đã có cờ `--run`) và `npm run build` để kiểm chứng một lần; dọn sạch tệp tạm sau kiểm chứng.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "1.2", "2.1", "7.1"] },
    { "id": 1, "tasks": ["1.3", "2.2", "4.1", "5.1", "5.6", "7.5"] },
    { "id": 2, "tasks": ["2.3", "4.2", "5.2", "5.3", "5.4", "5.5", "7.2", "7.3", "7.4"] },
    { "id": 3, "tasks": ["2.4", "5.7", "7.6"] },
    { "id": 4, "tasks": ["2.5", "8.1"] },
    { "id": 5, "tasks": ["8.2"] },
    { "id": 6, "tasks": ["8.3"] }
  ]
}
```
