/**
 * Pure presentation-mapping functions for the UI/UX modernization layer.
 *
 * This module is the single source of truth for translating domain status and
 * media data into presentation primitives (semantic badge variants, token-based
 * Tailwind classes and preview sources). All functions are pure: no side effects,
 * no I/O, no behavior change to callers.
 *
 * NOTE: The types declared here (`StatusBadgeVariant`, `PreviewSource`) are
 * internal presentation types. They are NOT part of the API contract in
 * `types/api.ts` and must not be imported as domain models.
 */

import type {
  MediaSummary,
  UploadQueueItem,
  UploadQueueStatus,
} from '../types/api'

// Variant trạng thái dùng chung cho Badge (ánh xạ tới token ngữ nghĩa cố định).
export type StatusBadgeVariant = 'info' | 'warning' | 'success' | 'destructive'

// Nguồn ảnh xem trước: ảnh thật (có URL) hoặc fallback theo media_type.
export type PreviewSource =
  | { kind: 'image'; url: string }
  | { kind: 'fallback'; mediaType: 'image' | 'video' }

/**
 * Ánh xạ CỐ ĐỊNH trạng thái -> variant ngữ nghĩa (bảng tham chiếu duy nhất).
 *  uploading/pending -> info, processing -> warning, completed -> success, failed -> destructive.
 * Đây là nguồn chân lý cho cả Status_Badge và thanh tiến trình.
 */
const STATUS_VARIANT: Record<UploadQueueStatus, StatusBadgeVariant> = {
  uploading: 'info',
  pending: 'info',
  processing: 'warning',
  completed: 'success',
  failed: 'destructive',
}

// Lớp Tailwind nền/chữ cho từng variant ngữ nghĩa (token, không palette hardcode).
const VARIANT_BADGE_CLASSES: Record<StatusBadgeVariant, string> = {
  info: 'bg-info text-info-foreground',
  warning: 'bg-warning text-warning-foreground',
  success: 'bg-success text-success-foreground',
  destructive: 'bg-destructive text-destructive-foreground',
}

// Lớp token nền cho thanh tiến trình theo từng variant (cùng nguồn ánh xạ với badge).
const VARIANT_PROGRESS_BAR_CLASS: Record<StatusBadgeVariant, string> = {
  info: 'bg-info',
  warning: 'bg-warning',
  success: 'bg-success',
  destructive: 'bg-destructive',
}

/**
 * Trả về variant ngữ nghĩa cố định cho một trạng thái.
 * Ánh xạ là toàn phần trên tập `UploadQueueStatus` và bỏ qua mọi override do nơi
 * gọi cố truyền vào (chữ ký chỉ nhận `status`). (R3.4, R3.5, R16.3)
 */
export function statusToBadgeVariant(status: UploadQueueStatus): StatusBadgeVariant {
  return STATUS_VARIANT[status]
}

/**
 * Lớp Tailwind nền/chữ cho Status_Badge, suy ra từ variant ngữ nghĩa của trạng thái.
 * (R3.2, R3.3)
 */
export function statusBadgeClasses(status: UploadQueueStatus): string {
  return VARIANT_BADGE_CLASSES[statusToBadgeVariant(status)]
}

/**
 * Lớp token nền cho thanh tiến trình theo trạng thái — cùng nguồn ánh xạ với badge.
 * (R16.2)
 */
export function statusProgressBarClass(status: UploadQueueStatus): string {
  return VARIANT_PROGRESS_BAR_CLASS[statusToBadgeVariant(status)]
}

/**
 * Predicate hiển thị badge Boost: chỉ hiện khi `rerankBoost > 0` (strictly positive).
 * Kết quả chỉ phụ thuộc dấu của `rerankBoost`, không phụ thuộc mật độ UI/collapsed.
 * (R13.4, R13.5)
 */
export function shouldShowBoostBadge(rerankBoost: number): boolean {
  return rerankBoost > 0
}

// Một chuỗi được coi là "có giá trị" khi khác null/undefined và không rỗng.
function isNonEmptyString(value: string | null | undefined): value is string {
  return typeof value === 'string' && value.length > 0
}

/**
 * Phân giải nguồn ảnh xem trước cho media (R14.1–14.3, R16.4):
 *  - `thumbnail` khác null/rỗng                              -> ảnh dùng `thumbnail`
 *  - `thumbnail` null & `media_type === 'image'` & có `file` -> ảnh dùng `file`
 *  - còn lại                                                 -> fallback theo `media_type`
 * Hàm là toàn phần và không bao giờ trả về URL rỗng cho nhánh ảnh.
 */
export function resolveMediaPreviewSource(
  media: Pick<MediaSummary, 'thumbnail' | 'file' | 'media_type'>,
): PreviewSource {
  if (isNonEmptyString(media.thumbnail)) {
    return { kind: 'image', url: media.thumbnail }
  }

  if (media.media_type === 'image' && isNonEmptyString(media.file)) {
    return { kind: 'image', url: media.file }
  }

  return { kind: 'fallback', mediaType: media.media_type }
}

/**
 * Phân giải nguồn ảnh xem trước cho mục tải lên (R16.4):
 *  - có `previewUrl`     -> ảnh dùng `previewUrl`
 *  - không có `previewUrl` -> fallback theo `mediaType` (mặc định an toàn `image` khi undefined)
 */
export function resolveUploadPreviewSource(
  item: Pick<UploadQueueItem, 'previewUrl' | 'mediaType'>,
): PreviewSource {
  if (isNonEmptyString(item.previewUrl)) {
    return { kind: 'image', url: item.previewUrl }
  }

  return { kind: 'fallback', mediaType: item.mediaType ?? 'image' }
}
