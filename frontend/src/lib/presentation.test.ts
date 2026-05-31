import { describe, it, expect } from 'vitest'
import fc from 'fast-check'
import {
  statusToBadgeVariant,
  statusBadgeClasses,
  statusProgressBarClass,
  shouldShowBoostBadge,
  resolveMediaPreviewSource,
  resolveUploadPreviewSource,
  type StatusBadgeVariant,
} from './presentation'
import type { MediaType, UploadQueueStatus } from '../types/api'

/**
 * Property-based tests cho lớp hàm thuần trình bày `lib/presentation.ts`.
 * Mỗi property cài đặt bằng MỘT property-based test (fast-check, ≥100 iterations).
 */
describe('presentation: status presentation mapping', () => {
  // Tập trạng thái hợp lệ và bảng ánh xạ ngữ nghĩa cố định kỳ vọng (nguồn chân lý).
  const ALL_STATUSES: readonly UploadQueueStatus[] = [
    'uploading',
    'pending',
    'processing',
    'completed',
    'failed',
  ]

  const EXPECTED_VARIANT: Record<UploadQueueStatus, StatusBadgeVariant> = {
    uploading: 'info',
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'destructive',
  }

  const statusArb = fc.constantFrom<UploadQueueStatus>(...ALL_STATUSES)

  // Feature: ui-ux-modernization, Property 1: Ánh xạ trình bày trạng thái là cố định, toàn phần và phân biệt
  it('Property 1: status mapping is fixed, total, and distinguishing', () => {
    fc.assert(
      fc.property(statusArb, fc.anything(), (status, override) => {
        // Cố định + toàn phần: mỗi trạng thái hợp lệ ánh xạ tới đúng variant cố định.
        const variant = statusToBadgeVariant(status)
        expect(variant).toBe(EXPECTED_VARIANT[status])

        // Bỏ qua mọi override: chữ ký chỉ nhận `status`, nên truyền thêm đối số
        // tùy ý không làm thay đổi kết quả (ánh xạ thuần theo trạng thái).
        const variantWithOverride = (
          statusToBadgeVariant as (
            s: UploadQueueStatus,
            ...rest: unknown[]
          ) => StatusBadgeVariant
        )(status, override)
        expect(variantWithOverride).toBe(variant)

        // Thanh tiến trình suy ra từ CÙNG ánh xạ ngữ nghĩa với badge.
        expect(statusProgressBarClass(status)).toBe(`bg-${variant}`)

        // Lớp badge cũng nhất quán với cùng variant (nền + foreground theo token).
        expect(statusBadgeClasses(status)).toBe(
          `bg-${variant} text-${variant}-foreground`,
        )
      }),
      { numRuns: 100 },
    )
  })

  it('Property 1 (distinctness): processing/completed/failed yield 3 distinct variants', () => {
    const variants = new Set([
      statusToBadgeVariant('processing'),
      statusToBadgeVariant('completed'),
      statusToBadgeVariant('failed'),
    ])
    expect(variants.size).toBe(3)
  })
})

describe('presentation: Boost badge visibility', () => {
  // Feature: ui-ux-modernization, Property 2: Hiển thị badge Boost chỉ phụ thuộc dấu của rerank_boost
  it('Property 2: Boost badge shows iff rerank_boost > 0, invariant to UI density/collapsed state', () => {
    // `uiDensityCollapsed` mô hình hóa mật độ UI / trạng thái collapsed: kết quả
    // phải BẤT BIẾN với cờ này vì `shouldShowBoostBadge` chỉ nhận `rerankBoost`.
    fc.assert(
      fc.property(
        fc.double({ noNaN: true }),
        fc.boolean(),
        (rerankBoost, uiDensityCollapsed) => {
          const shown = shouldShowBoostBadge(rerankBoost)

          // Badge hiện KHI VÀ CHỈ KHI rerank_boost > 0 (strictly positive).
          expect(shown).toBe(rerankBoost > 0)

          // Bất biến với mật độ UI / collapsed: cờ phụ không đổi kết quả.
          void uiDensityCollapsed
          expect(shouldShowBoostBadge(rerankBoost)).toBe(shown)
        },
      ),
      { numRuns: 100 },
    )
  })

  it('Property 2 (boundary): 0 is false; smallest positive is true; negatives are false', () => {
    expect(shouldShowBoostBadge(0)).toBe(false)
    expect(shouldShowBoostBadge(-0)).toBe(false)
    expect(shouldShowBoostBadge(Number.MIN_VALUE)).toBe(true)
    expect(shouldShowBoostBadge(-Number.MIN_VALUE)).toBe(false)
    expect(shouldShowBoostBadge(Number.MAX_VALUE)).toBe(true)
    expect(shouldShowBoostBadge(-Number.MAX_VALUE)).toBe(false)
  })
})

describe('presentation: media preview source resolution', () => {
  // Một chuỗi "có giá trị" khi khác null/rỗng (đồng bộ với quy ước của hàm thuần).
  const isNonEmpty = (value: string | null): value is string =>
    typeof value === 'string' && value.length > 0

  // thumbnail ∈ {chuỗi không rỗng, '', null}; '' được coi như VẮNG MẶT.
  const thumbnailArb = fc.oneof(
    fc.string({ minLength: 1 }),
    fc.constant(''),
    fc.constant(null),
  ) as fc.Arbitrary<string | null>

  // file ∈ {chuỗi (có thể rỗng)}; media_type ∈ {'image','video'}.
  const fileArb = fc.oneof(fc.string({ minLength: 1 }), fc.constant(''))
  const mediaTypeArb = fc.constantFrom<MediaType>('image', 'video')

  // Feature: ui-ux-modernization, Property 3: Phân giải nguồn ảnh xem trước cho media
  it('Property 3: resolves preview source by thumbnail/file/media_type rules; total and never empty image url', () => {
    fc.assert(
      fc.property(thumbnailArb, fileArb, mediaTypeArb, (thumbnail, file, media_type) => {
        const result = resolveMediaPreviewSource({ thumbnail, file, media_type })

        if (isNonEmpty(thumbnail)) {
          // thumbnail có giá trị -> ảnh dùng thumbnail.
          expect(result).toEqual({ kind: 'image', url: thumbnail })
        } else if (media_type === 'image' && isNonEmpty(file)) {
          // thumbnail vắng mặt & là image & có file -> ảnh dùng file.
          expect(result).toEqual({ kind: 'image', url: file })
        } else {
          // còn lại -> fallback theo media_type.
          expect(result).toEqual({ kind: 'fallback', mediaType: media_type })
        }

        // Toàn phần: luôn trả về một PreviewSource hợp lệ ('image' | 'fallback').
        expect(['image', 'fallback']).toContain(result.kind)

        // Nhánh ảnh không bao giờ trả về URL rỗng.
        if (result.kind === 'image') {
          expect(result.url.length).toBeGreaterThan(0)
        } else {
          expect(['image', 'video']).toContain(result.mediaType)
        }
      }),
      { numRuns: 100 },
    )
  })
})

describe('presentation: upload item preview source resolution', () => {
  // Một chuỗi "có giá trị" khi khác undefined/rỗng (đồng bộ với quy ước của hàm thuần).
  const isNonEmpty = (value: string | undefined): value is string =>
    typeof value === 'string' && value.length > 0

  // previewUrl ∈ {chuỗi không rỗng, '', undefined}; '' và undefined được coi như VẮNG MẶT.
  const previewUrlArb = fc.oneof(
    fc.string({ minLength: 1 }),
    fc.constant(''),
    fc.constant(undefined),
  ) as fc.Arbitrary<string | undefined>

  // mediaType ∈ {'image','video', undefined}; undefined dùng mặc định an toàn 'image'.
  const mediaTypeArb = fc.constantFrom<'image' | 'video' | undefined>(
    'image',
    'video',
    undefined,
  )

  // Feature: ui-ux-modernization, Property 4: Phân giải nguồn ảnh xem trước cho mục tải lên
  it('Property 4: resolves upload preview source by previewUrl/mediaType rules; total and never empty image url', () => {
    fc.assert(
      fc.property(previewUrlArb, mediaTypeArb, (previewUrl, mediaType) => {
        const result = resolveUploadPreviewSource({ previewUrl, mediaType })

        if (isNonEmpty(previewUrl)) {
          // previewUrl có giá trị -> ảnh dùng previewUrl.
          expect(result).toEqual({ kind: 'image', url: previewUrl })
        } else {
          // previewUrl vắng mặt ('' hoặc undefined) -> fallback theo mediaType,
          // với mặc định an toàn 'image' khi mediaType undefined.
          expect(result).toEqual({ kind: 'fallback', mediaType: mediaType ?? 'image' })
        }

        // Toàn phần: luôn trả về một PreviewSource hợp lệ ('image' | 'fallback').
        expect(['image', 'fallback']).toContain(result.kind)

        // Nhánh ảnh không bao giờ trả về URL rỗng.
        if (result.kind === 'image') {
          expect(result.url.length).toBeGreaterThan(0)
        } else {
          expect(['image', 'video']).toContain(result.mediaType)
        }
      }),
      { numRuns: 100 },
    )
  })
})
