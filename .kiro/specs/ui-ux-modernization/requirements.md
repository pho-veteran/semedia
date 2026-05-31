# Requirements Document

## Introduction

Tài liệu này mô tả yêu cầu cho việc tái cấu trúc (refactor) toàn bộ phần trình bày UI/UX của frontend ứng dụng "Semedia" (semantic media search app). Mục tiêu là củng cố và hoàn thiện một hệ thống thiết kế (design system) duy nhất, nhất quán, hiện đại và chuẩn theo các design system uy tín năm 2026 (Material Design 3, Apple HIG, Vercel Geist, shadcn/ui, Radix, Tailwind), bao gồm: layout, typography, color, spacing, radius, shadow/elevation và motion.

Hiện trạng: hệ thống Design_Token đã được triển khai phần lớn trong `frontend/src/index.css` (token màu, surface/brand, token ngữ nghĩa success/warning/info/destructive, shadow, motion, radius, font Inter, dark mode, reduced-motion, scrollbar và các utility glass/gradient-text/focus-ring) và `frontend/tailwind.config.js` (color, borderRadius, boxShadow, easing motion, zIndex, keyframes/animations). Do đó, phần lớn yêu cầu liên quan tới token được phát biểu theo hướng "bảo đảm và hợp nhất" (ensure/consolidate) quanh nguồn chân lý duy nhất, thay vì "tạo mới từ đầu". Phần chưa hoàn tất gồm: gỡ bỏ stylesheet legacy `App.css` (vẫn còn import trong `App.tsx`), xóa component chết, và hợp nhất ràng buộc layout về App_Layout.

Phạm vi thay đổi **chỉ giới hạn ở lớp trình bày của frontend** (React 19 + Vite + TypeScript + Tailwind CSS 3.4 + Radix UI). Việc refactor **không được** thay đổi logic backend, hợp đồng API (API contract), luồng dữ liệu (data flow), logic định tuyến (routing logic), hay hành vi chức năng hiện có. Đây là một ràng buộc bắt buộc xuyên suốt mọi requirement.

Tài liệu cũng yêu cầu loại bỏ hệ thống CSS legacy chồng chéo (App.css) và các component chết (dead code), chuẩn hóa token màu/typography/spacing, bảo đảm khả năng tiếp cận (accessibility WCAG AA) cùng đồng bộ dark mode, và nâng cấp các điểm trình bày trọng yếu: badge điểm số/giải thích kết quả tìm kiếm, ảnh xem trước media, điều hướng/breadcrumb và thẻ hàng đợi tải lên.

## Glossary

- **Frontend**: Ứng dụng web Semedia chạy trên trình duyệt, gồm React 19, Vite, TypeScript, Tailwind CSS 3.4, Radix UI và các component shadcn-style trong `frontend/src/components/ui`.
- **Design_System**: Tập hợp duy nhất các design token (color, typography, spacing, radius, shadow/elevation, motion) và component nền tảng dùng chung cho toàn bộ Frontend, đã được triển khai qua `frontend/src/index.css` và `frontend/tailwind.config.js`.
- **Design_Token**: Một biến thiết kế có tên ngữ nghĩa (semantic) được khai báo trong Design_System, ví dụ token màu `--primary`, `--surface`, `--brand`, token spacing, token radius, token shadow, token motion.
- **Semantic_Color_Token**: Token màu được đặt tên theo mục đích sử dụng thay vì giá trị màu cụ thể, gồm các nhóm: `primary`, `secondary`, `brand`, `success`, `warning`, `info`, `destructive` và `surface`.
- **Type_Scale**: Thang bậc typography thống nhất (kích thước, độ đậm, line-height, letter-spacing) áp dụng cho tiêu đề và nội dung trên mọi trang.
- **Spacing_Scale**: Thang bậc khoảng cách (padding, margin, gap) thống nhất dùng cho layout và component.
- **Legacy_Stylesheet**: Tệp CSS cũ theo class `frontend/src/App.css` với bộ token riêng (`--bg-primary`, `--accent-primary`, `--accent-secondary`...) không thuộc Design_System; hiện vẫn còn được import trong `frontend/src/App.tsx`.
- **Dead_Component**: Component không còn được import hoặc render ở bất kỳ nơi nào trong Frontend, gồm `frontend/src/components/MediaListPanel.tsx` và `frontend/src/components/Sidebar.tsx` (bản cũ ở thư mục gốc components; bản đang dùng là `frontend/src/components/layout/Sidebar.tsx`).
- **UI_Primitive**: Component nền tảng trong `frontend/src/components/ui` (Button, Badge, Card, Dialog, EmptyState, ErrorState, Input, Select, Sheet, Skeleton, Tabs).
- **Page**: Một trong các trang chính của Frontend: DashboardPage, SearchPage, LibraryPage, MediaDetailPage.
- **App_Layout**: Component bố cục khung chính `frontend/src/components/layout/AppLayout.tsx` là nơi duy nhất giới hạn chiều rộng tối đa của nội dung (`max-w-[1440px]`) và đặt padding responsive cho vùng nội dung chính.
- **Processing_Status**: Enum trạng thái xử lý media của backend, gồm đúng bốn giá trị `pending`, `processing`, `completed`, `failed`. Trạng thái `uploading` là trạng thái tổng hợp (synthetic) chỉ tồn tại phía Frontend trong `UploadQueueItem`, không thuộc hợp đồng API.
- **Status_Badge**: Badge biểu thị trạng thái xử lý media (uploading/pending, processing, completed, failed) dựng trên UI_Primitive Badge.
- **Search_Explanation_Badge**: Nhóm badge hiển thị tín hiệu điểm số và giải thích của một kết quả tìm kiếm trong SearchResultCard và SearchResultGroup, gồm điểm Semantic (`vector_score`), điểm Caption (`keyword_score`), Boost (`rerank_boost`), và các nhãn từ đối tượng `explanation` (`match_type` ∈ visual|caption|hybrid, `exact_phrase_match`, `rich_caption`).
- **Media_Thumbnail**: Trường `thumbnail` (kiểu `string | null`) của `MediaSummary`/`MediaDetail` dùng làm ảnh xem trước media (đặc biệt cho video), có sẵn trong hợp đồng API hiện tại.
- **Upload_Queue_Card**: Thẻ trình bày một mục tải lên trong `UploadQueuePanel`, gồm ảnh xem trước, Status_Badge, thanh tiến trình và các nút thao tác (hủy, thử lại, mở media).
- **Theme_Mode**: Chế độ hiển thị sáng hoặc tối, điều khiển qua thuộc tính `data-theme` và ThemeContext.
- **WCAG_AA**: Tiêu chuẩn tiếp cận Web Content Accessibility Guidelines mức AA, gồm yêu cầu tỉ lệ tương phản văn bản tối thiểu 4.5:1 (3:1 cho văn bản lớn), focus hiển thị rõ, điều hướng bàn phím và tôn trọng `prefers-reduced-motion`.
- **API_Contract**: Tập hợp endpoint, phương thức, tham số, cấu trúc request và response giữa Frontend và backend, được dùng qua `frontend/src/api/client.ts`.
- **Component_Behavior**: Hành vi chức năng của component gồm props công khai, sự kiện, luồng dữ liệu, gọi API và logic định tuyến.

## Requirements

### Requirement 1: Hệ thống thiết kế token-based duy nhất

**User Story:** Là một nhà phát triển frontend, tôi muốn toàn bộ Frontend dùng chung một design system token-based duy nhất đã được hợp nhất, để giao diện nhất quán và dễ bảo trì.

#### Acceptance Criteria

1. THE Design_System SHALL duy trì toàn bộ Design_Token trong `frontend/src/index.css` và `frontend/tailwind.config.js` như nguồn chân lý (single source of truth) duy nhất.
2. THE Frontend SHALL áp dụng style cho mọi Page và mọi UI_Primitive thông qua Design_Token của Design_System.
3. WHERE một component cần giá trị màu, spacing, radius, shadow hoặc typography, THE Frontend SHALL tham chiếu Design_Token tương ứng và SHALL không dùng giá trị hardcode ở mọi thời điểm, kể cả trong giai đoạn phát triển hoặc di trú.
4. THE Design_System SHALL bảo đảm đầy đủ sáu nhóm token: color, typography, spacing, radius, shadow/elevation và motion.
5. WHERE phát hiện token trùng lặp hoặc không dùng tới trong Design_System, THE Frontend SHALL hợp nhất hoặc loại bỏ token đó để giữ nguồn chân lý duy nhất.

### Requirement 2: Loại bỏ stylesheet legacy và mã chết

**User Story:** Là một nhà phát triển frontend, tôi muốn loại bỏ CSS legacy và component chết, để tránh trùng lặp token và giảm rủi ro xung đột style.

#### Acceptance Criteria

1. THE Frontend SHALL loại bỏ việc import Legacy_Stylesheet (`frontend/src/App.css`) khỏi `frontend/src/App.tsx`.
2. WHEN mọi giao diện đã chuyển sang Design_Token (migration hoàn tất), THE Frontend SHALL xóa Legacy_Stylesheet khỏi mã nguồn như một bước dọn dẹp thủ công sau di trú.
3. THE Frontend SHALL xóa Dead_Component `frontend/src/components/MediaListPanel.tsx` và `frontend/src/components/Sidebar.tsx` (bản cũ ở thư mục gốc components).
4. IF một class CSS của Legacy_Stylesheet vẫn còn được tham chiếu trong mã nguồn, THEN THE Frontend SHALL thay thế class đó bằng style dựa trên Design_Token trước khi xóa Legacy_Stylesheet.
5. WHEN quá trình refactor hoàn tất, THE Frontend SHALL build thành công và SHALL không còn bất kỳ tham chiếu nào tới Legacy_Stylesheet hoặc Dead_Component (số tham chiếu legacy bằng không).

### Requirement 3: Chuẩn hóa token màu ngữ nghĩa

**User Story:** Là một nhà thiết kế hệ thống, tôi muốn mọi màu sắc dùng Semantic_Color_Token, để màu nhất quán và dễ điều chỉnh giữa các chế độ giao diện.

#### Acceptance Criteria

1. THE Design_System SHALL định nghĩa các Semantic_Color_Token cho các nhóm `primary`, `secondary`, `brand`, `success`, `warning`, `info`, `destructive` và `surface`, mỗi nhóm gồm màu nền và màu foreground tương ứng.
2. THE Frontend SHALL thay thế mọi màu hardcode dạng Tailwind palette trực tiếp (ví dụ `bg-blue-500`, `bg-amber-500`, `bg-emerald-500`, `text-green-700`, `bg-orange-100`, `bg-green-100`, `bg-green-500/5`, `bg-black/60`) trong UploadQueuePanel, DataTable, SearchResultCard, SearchResultGroup, RuntimeBadge và Badge bằng Semantic_Color_Token tương ứng.
3. THE Status_Badge SHALL hiển thị mỗi trạng thái (uploading/pending, processing, completed, failed) theo cùng một quy ước thị giác nhất quán về kiểu nền và độ tương phản.
4. WHERE một trạng thái cần phân biệt với trạng thái khác, THE Status_Badge SHALL luôn dùng Semantic_Color_Token theo ánh xạ cố định một cách nghiêm ngặt (`info` cho uploading/pending, `warning` cho processing, `success` cho completed, `destructive` cho failed) thay vì màu palette hardcode.
5. THE Status_Badge SHALL gán cho mỗi trạng thái một Semantic_Color_Token khác nhau để bảo đảm phân biệt thị giác giữa các trạng thái.
6. WHILE một media đang ở trạng thái processing, THE Status_Badge SHALL hiển thị bằng token `warning` cố định.
7. THE Frontend SHALL chỉ ánh xạ trạng thái synthetic `uploading` cho hàng đợi tải lên (UploadQueueItem) và SHALL ánh xạ bốn trạng thái Processing_Status (`pending`, `processing`, `completed`, `failed`) cho dữ liệu media từ backend mà không thay đổi tập giá trị trạng thái của API_Contract.
8. IF một nơi gọi cố gắng override Semantic_Color_Token của một trạng thái sang token khác (ví dụ `primary`), THEN THE Status_Badge SHALL bỏ qua override đó và SHALL vẫn áp dụng ánh xạ cố định theo trạng thái.

### Requirement 4: Thang bậc typography thống nhất

**User Story:** Là một người dùng, tôi muốn tiêu đề và văn bản nhất quán giữa các trang, để giao diện trông chuyên nghiệp và dễ đọc.

#### Acceptance Criteria

1. THE Design_System SHALL định nghĩa một Type_Scale thống nhất gồm các cấp tiêu đề và văn bản với kích thước, độ đậm, line-height và letter-spacing xác định.
2. THE Frontend SHALL áp dụng cùng một cấp Type_Scale cho tiêu đề cấp một (h1) trên DashboardPage, SearchPage, LibraryPage và MediaDetailPage.
3. THE Frontend SHALL áp dụng Type_Scale cho mọi cấp tiêu đề và văn bản trên mọi Page.
4. THE Frontend SHALL dùng font Inter với cấu hình `font-feature-settings` đã định nghĩa trong Design_System cho toàn bộ văn bản.

### Requirement 5: Thang bậc spacing, radius, shadow và motion thống nhất

**User Story:** Là một nhà thiết kế hệ thống, tôi muốn spacing, bo góc, đổ bóng và chuyển động theo thang bậc thống nhất, để nhịp điệu thị giác đồng đều trên toàn ứng dụng.

#### Acceptance Criteria

1. THE Design_System SHALL định nghĩa Spacing_Scale thống nhất cho padding, margin và gap.
2. THE Design_System SHALL định nghĩa thang bậc radius và thang bậc shadow/elevation thống nhất.
3. THE Frontend SHALL áp dụng Spacing_Scale, thang radius và thang shadow của Design_System cho mọi Page và UI_Primitive.
4. THE Design_System SHALL định nghĩa thang bậc motion (thời lượng và đường cong easing) thống nhất cho các hiệu ứng chuyển tiếp và animation.
5. WHERE một component dùng animation hoặc transition, THE Frontend SHALL dùng token motion của Design_System ngay lập tức cho mọi component có animation, không miễn trừ cho animation legacy hoặc chuyên biệt trong giai đoạn di trú.

### Requirement 6: Layout và container nhất quán trên mọi trang

**User Story:** Là một người dùng, tôi muốn các trang có chiều rộng nội dung và khoảng đệm nhất quán, để bố cục cân đối và không bị lệch giữa các trang.

#### Acceptance Criteria

1. THE App_Layout SHALL là nơi duy nhất giới hạn chiều rộng tối đa của nội dung (`max-w-[1440px]`) và đặt padding responsive cho vùng nội dung chính.
2. WHEN refactor layout, THE Frontend SHALL bảo đảm App_Layout cung cấp các điều khiển max-width và padding responsive TRƯỚC khi loại bỏ ràng buộc chiều rộng và padding cấp trang.
3. THE Frontend SHALL loại bỏ ràng buộc chiều rộng và padding cấp trang trùng lặp gây xung đột với App_Layout, gồm `max-w-7xl mx-auto px-6 py-8` trong SearchPage và các ràng buộc `max-w-7xl mx-auto` (cùng `max-w-7xl mx-auto px-3 py-4 md:px-6 md:py-8`) trong MediaDetailPage.
4. THE Frontend SHALL trình bày DashboardPage, SearchPage, LibraryPage và MediaDetailPage theo cùng một quy ước container và padding của App_Layout, đạt sự nhất quán bằng cách tuân theo quy ước của App_Layout.
5. THE Frontend SHALL dùng quy ước grid và gap nhất quán cho các lưới media và lưới kết quả trên mọi Page.

### Requirement 7: Bố cục responsive chuẩn

**User Story:** Là một người dùng trên nhiều kích thước màn hình, tôi muốn giao diện hiển thị hợp lý trên mobile, tablet và desktop, để sử dụng được trên mọi thiết bị.

#### Acceptance Criteria

1. WHILE khung nhìn ở kích thước mobile, THE Frontend SHALL trình bày nội dung dạng một cột bất kể cấu hình lưới khác, ưu tiên một cột trên mobile cao hơn mọi cấu hình lưới đa cột, và giữ mọi điều khiển ở trạng thái thao tác được.
2. WHILE khung nhìn ở kích thước tablet hoặc desktop, THE Frontend SHALL trình bày lưới media và lưới kết quả theo số cột tăng dần phù hợp với điểm ngắt (breakpoint) đã định nghĩa.
3. THE Frontend SHALL dùng cùng một tập breakpoint responsive cho mọi Page, trong đó tablet và desktop ĐƯỢC PHÉP dùng chung một giá trị breakpoint miễn là mọi Page dùng cùng một tập breakpoint nhất quán.
4. WHILE khung nhìn ở kích thước mobile, THE Sidebar SHALL hiển thị ở dạng menu mở được (Sheet) thay vì cột cố định.

### Requirement 8: Nhất quán component nền tảng

**User Story:** Là một người dùng, tôi muốn các thành phần như nút, thẻ, badge và trạng thái rỗng/lỗi/đang tải trông nhất quán, để trải nghiệm liền mạch giữa các trang.

#### Acceptance Criteria

1. THE Frontend SHALL dùng UI_Primitive dùng chung cho nút (Button), thẻ (Card), badge (Badge), trạng thái rỗng (EmptyState), trạng thái lỗi (ErrorState) và trạng thái đang tải (Skeleton) trên mọi Page.
2. THE Frontend SHALL trình bày trạng thái đang tải bằng Skeleton dùng chung với cùng một quy ước thị giác trên DashboardPage, SearchPage, LibraryPage và MediaDetailPage.
3. THE Frontend SHALL trình bày trạng thái rỗng bằng EmptyState dùng chung và trạng thái lỗi bằng ErrorState dùng chung.
4. THE Status_Badge SHALL dùng chung một UI_Primitive Badge với tập variant trạng thái xác định cho mọi nơi hiển thị trạng thái media.
5. THE Frontend SHALL áp dụng cùng quy ước trình bày của UI_Primitive cho các component trình bày kết quả tìm kiếm SearchResultCard và SearchResultGroup.

### Requirement 9: Bảo toàn hành vi chức năng và hợp đồng backend

**User Story:** Là chủ sản phẩm, tôi muốn việc refactor UI/UX không thay đổi hành vi chức năng hay backend, để tránh phát sinh lỗi và rủi ro hồi quy.

#### Acceptance Criteria

1. THE Frontend SHALL giữ nguyên API_Contract đang dùng trong `frontend/src/api/client.ts`, gồm các endpoint `GET /api/v1/runtime/`, `GET /api/v1/media/`, `GET /api/v1/media/{id}/`, `POST /api/v1/media/upload/`, `DELETE /api/v1/media/{id}/`, `POST /api/v1/search/`, `POST /api/v1/search/by-image/`, cùng phương thức, tham số và cấu trúc request/response tương ứng.
2. THE Frontend SHALL giữ nguyên Component_Behavior gồm props công khai, sự kiện, luồng dữ liệu và logic định tuyến của mọi component và Page.
3. WHERE một thay đổi chỉ thuộc lớp trình bày, THE Frontend SHALL giới hạn chỉnh sửa trong class style, markup trình bày và Design_Token mà không thay đổi logic xử lý dữ liệu.
4. IF một thao tác refactor đòi hỏi thay đổi logic backend, hợp đồng API hoặc luồng dữ liệu, THEN THE Frontend SHALL không thực hiện thay đổi đó.
5. WHEN quá trình refactor hoàn tất, THE Frontend SHALL vượt qua toàn bộ bộ kiểm thử hiện có (`SearchResultCard.test.tsx`, `SearchResultGroup.test.tsx`, `SearchPage.test.tsx`, `searchResults.test.ts`) mà không cần sửa kỳ vọng hành vi của các kiểm thử đó; các kiểm thử ĐƯỢC PHÉP thất bại tạm thời trong quá trình refactor miễn là tất cả đều đạt khi refactor hoàn tất.

### Requirement 10: Khả năng tiếp cận theo WCAG AA

**User Story:** Là một người dùng cần hỗ trợ tiếp cận, tôi muốn giao diện đáp ứng WCAG AA, để tôi có thể đọc, điều hướng và thao tác hiệu quả.

#### Acceptance Criteria

1. THE Frontend SHALL bảo đảm tỉ lệ tương phản giữa văn bản và nền đạt tối thiểu 4.5:1 cho văn bản thường và 3:1 cho văn bản lớn ở cả Theme_Mode sáng và tối.
2. WHEN một phần tử tương tác nhận focus bàn phím, THE Frontend SHALL hiển thị chỉ báo focus rõ ràng dùng token `ring` của Design_System.
3. THE Frontend SHALL cho phép điều hướng và kích hoạt mọi điều khiển tương tác bằng bàn phím.
4. WHILE người dùng bật tùy chọn `prefers-reduced-motion`, THE Frontend SHALL giảm thiểu hoặc loại bỏ mọi animation và transition, bao gồm cả các hiệu ứng thiết yếu như spinner đang tải và chỉ báo tiến trình.
5. THE Frontend SHALL giữ nguyên các thuộc tính tiếp cận hiện có gồm liên kết bỏ qua điều hướng (skip-nav) và nhãn aria.

### Requirement 11: Đồng bộ dark mode

**User Story:** Là một người dùng, tôi muốn dark mode hiển thị đồng bộ và đầy đủ trên mọi giao diện, để trải nghiệm nhất quán khi đổi chế độ.

#### Acceptance Criteria

1. WHEN Theme_Mode chuyển sang chế độ tối, THE Frontend SHALL áp dụng tập Design_Token chế độ tối cho mọi Page và UI_Primitive.
2. WHEN Theme_Mode chuyển sang chế độ sáng, THE Frontend SHALL áp dụng tập Design_Token chế độ sáng cho mọi Page và UI_Primitive.
3. THE Frontend SHALL bảo đảm mọi Semantic_Color_Token có giá trị xác định cho cả Theme_Mode sáng và tối.
4. WHILE đang ở Theme_Mode tối, THE Frontend SHALL không hiển thị màu hardcode vốn chỉ phù hợp với chế độ sáng.
5. IF một Semantic_Color_Token chưa được định nghĩa đầy đủ trong giai đoạn phát triển, THEN THE Frontend SHALL vẫn cho phép chuyển Theme_Mode và SHALL dùng màu mặc định (default) làm giá trị dự phòng cho token đó.

### Requirement 12: Tham chiếu chuẩn design system 2026

**User Story:** Là một nhà thiết kế hệ thống, tôi muốn các quyết định thị giác bám theo các design system uy tín năm 2026, để giao diện chuyên nghiệp và hiện đại.

#### Acceptance Criteria

1. THE Design_System SHALL định nghĩa các quy ước về typography, color, spacing, radius, shadow/elevation và motion bám theo nguyên tắc của các nguồn tham chiếu (Material Design 3, Apple HIG, Vercel Geist, shadcn/ui, Radix, Tailwind).
2. THE Frontend SHALL trình bày các trạng thái tương tác (hover, focus, active, disabled) của UI_Primitive theo quy ước nhất quán do Design_System định nghĩa.
3. IF việc trình bày thị giác của một trạng thái tương tác (ví dụ hover) thất bại, THEN THE Frontend SHALL dự phòng về trạng thái thị giác mặc định (default).
4. THE Frontend SHALL áp dụng hệ phân cấp thị giác (visual hierarchy) nhất quán giữa surface nền, surface nâng cao và lớp nội dung dựa trên token `surface` và shadow/elevation.

### Requirement 13: Nhất quán trình bày badge điểm số và giải thích kết quả tìm kiếm

**User Story:** Là một người dùng tìm kiếm, tôi muốn các badge điểm số và giải thích kết quả hiển thị nhất quán và dễ hiểu, để đánh giá nhanh độ liên quan của từng kết quả.

#### Acceptance Criteria

1. THE Frontend SHALL trình bày Search_Explanation_Badge trong SearchResultCard và SearchResultGroup gồm điểm Semantic (theo `vector_score`), điểm Caption (theo `keyword_score`), Boost (theo `rerank_boost`) và các nhãn giải thích từ `explanation` (`match_type`, `exact_phrase_match`, `rich_caption`).
2. THE Frontend SHALL tô màu cho Search_Explanation_Badge bằng Semantic_Color_Token và SHALL không dùng màu palette hardcode (ví dụ `bg-green-500/5`, `border-green-500/20`, `bg-black/60`).
3. THE Frontend SHALL áp dụng Type_Scale của Design_System cho nhãn và nội dung của Search_Explanation_Badge.
4. WHERE một kết quả có `rerank_boost` lớn hơn 0, THE Frontend SHALL hiển thị badge Boost của Search_Explanation_Badge bằng Semantic_Color_Token thay vì màu palette hardcode, và SHALL chỉ hiển thị badge Boost khi `rerank_boost` lớn hơn 0 (strictly positive).
5. WHILE `rerank_boost` lớn hơn 0, THE Frontend SHALL luôn hiển thị badge Boost bất kể mật độ UI hoặc trạng thái thu gọn (collapsed) và SHALL không ẩn badge Boost khi giao diện chật.
6. THE Search_Explanation_Badge SHALL tuân theo cùng quy ước thị giác (kiểu nền, độ tương phản, bo góc, kích thước) như Status_Badge.
7. THE Frontend SHALL trình bày chú giải (legend) hướng dẫn cách đọc các badge kết quả bằng Design_Token và Type_Scale, đồng thời giữ nguyên nội dung và hành vi hiện có.
8. WHEN refactor trình bày badge và chú giải kết quả tìm kiếm, THE Frontend SHALL giữ nguyên kỳ vọng hành vi của `SearchResultCard.test.tsx`, `SearchResultGroup.test.tsx` và `SearchPage.test.tsx`.

### Requirement 14: Ảnh xem trước media dùng trường thumbnail

**User Story:** Là một người dùng, tôi muốn xem ảnh thu nhỏ (thumbnail) cho media kể cả video, để nhận diện nội dung nhanh trong danh sách và lưới.

#### Acceptance Criteria

1. WHERE một MediaSummary có Media_Thumbnail khác null, THE Frontend SHALL dùng Media_Thumbnail làm ảnh xem trước trong MediaCard, DataTable và lưới media của DashboardPage và LibraryPage.
2. IF Media_Thumbnail bằng null, THEN THE Frontend SHALL hiển thị ảnh fallback phù hợp cho mọi giá trị `media_type` khi không có ảnh xem trước (biểu tượng video cho video, biểu tượng hình ảnh hoặc trường `file` cho hình ảnh).
3. IF việc tải Media_Thumbnail thất bại, THEN THE Frontend SHALL hiển thị fallback thay vì hiển thị ảnh hỏng.
4. THE Frontend SHALL trình bày mọi ảnh xem trước, BAO GỒM cả biểu tượng fallback, với cùng tỉ lệ khung hình và quy ước bo góc do Design_System định nghĩa tại mọi nơi hiển thị.
5. WHERE thay đổi chỉ là dùng Media_Thumbnail cho lớp trình bày, THE Frontend SHALL không thay đổi API_Contract của MediaSummary.

### Requirement 15: Điều hướng, sidebar và breadcrumb nhất quán với design system

**User Story:** Là một người dùng, tôi muốn sidebar và breadcrumb/nút quay lại ở trang chi tiết hiển thị trạng thái nhất quán, để định hướng dễ dàng trong ứng dụng.

#### Acceptance Criteria

1. THE Frontend SHALL trình bày trạng thái active, hover và disabled của các mục điều hướng trong Sidebar bằng Design_Token (ví dụ token `brand`, `muted`, `ring`) thay vì màu palette hardcode.
2. WHERE đang ở MediaDetailPage, THE Frontend SHALL trình bày breadcrumb và nút quay lại (back) bằng Design_Token và Type_Scale nhất quán với Design_System; yêu cầu về breadcrumb và nút quay lại này CHỈ áp dụng cho MediaDetailPage, không áp dụng phổ quát cho mọi Page.
3. WHEN một mục điều hướng tương ứng với Page hiện tại, THE Sidebar SHALL đánh dấu mục đó ở trạng thái active bằng Design_Token và đặt thuộc tính `aria-current`.
4. WHEN một phần tử điều hướng hoặc nút quay lại nhận focus bàn phím, THE Frontend SHALL hiển thị chỉ báo focus dùng token `ring`.
5. THE Frontend SHALL giữ nguyên logic định tuyến và Component_Behavior khi tinh chỉnh trình bày của Sidebar và breadcrumb.

### Requirement 16: Trình bày thẻ hàng đợi tải lên nhất quán

**User Story:** Là một người dùng đang tải media lên, tôi muốn thẻ hàng đợi tải lên hiển thị nhất quán với phần còn lại của hệ thống, để theo dõi tiến trình rõ ràng.

#### Acceptance Criteria

1. THE Frontend SHALL trình bày Upload_Queue_Card (trong UploadQueuePanel) gồm ảnh xem trước, Status_Badge, thanh tiến trình và các nút thao tác bằng Design_Token.
2. THE Frontend SHALL tô màu thanh tiến trình theo trạng thái bằng Semantic_Color_Token và SHALL không dùng màu palette hardcode (ví dụ `bg-blue-500`, `bg-amber-500`, `bg-emerald-500`).
3. THE Upload_Queue_Card SHALL dùng Status_Badge với ánh xạ trạng thái nhất quán (`info` cho uploading/pending, `warning` cho processing, `success` cho completed, `destructive` cho failed).
4. WHERE một mục tải lên không có ảnh xem trước, THE Upload_Queue_Card SHALL hiển thị fallback phù hợp cho mọi giá trị `media_type` khi không có ảnh xem trước.
5. WHILE một mục đang ở trạng thái uploading hoặc processing, THE Upload_Queue_Card SHALL hiển thị hiệu ứng tiến trình dùng token motion của Design_System.
