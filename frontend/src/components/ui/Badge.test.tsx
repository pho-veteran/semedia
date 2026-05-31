import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Badge } from './Badge'

// Task 4.2: Unit test cho Badge token.
// Validates: Requirements 3.2, 3.3
//  - Bốn variant trạng thái (uploading/processing/completed/failed) phải dùng
//    lớp Semantic_Color_Token (bg-info/bg-warning/bg-success/bg-destructive)
//    thay vì màu Tailwind palette hardcode (bg-blue-500/bg-orange-500/
//    bg-green-100/bg-red-500).

// Ánh xạ cố định trạng thái -> token nền + token foreground (Requirement 3.4).
const STATUS_VARIANTS = [
  { variant: 'uploading', bg: 'bg-info', fg: 'text-info-foreground' },
  { variant: 'processing', bg: 'bg-warning', fg: 'text-warning-foreground' },
  { variant: 'completed', bg: 'bg-success', fg: 'text-success-foreground' },
  { variant: 'failed', bg: 'bg-destructive', fg: 'text-destructive-foreground' },
] as const

// Màu palette hardcode bị cấm trên các Status_Badge (Requirement 3.2).
const FORBIDDEN_PALETTE_CLASSES = [
  'bg-blue-500',
  'bg-orange-500',
  'bg-green-100',
  'bg-red-500',
]

describe('Badge status variants use semantic color tokens', () => {
  it.each(STATUS_VARIANTS)(
    'variant "$variant" dùng $bg / $fg thay vì palette hardcode',
    ({ variant, bg, fg }) => {
      render(<Badge variant={variant}>{variant}</Badge>)

      const badge = screen.getByText(variant)

      // Dùng lớp token ngữ nghĩa.
      expect(badge).toHaveClass(bg)
      expect(badge).toHaveClass(fg)

      // Không dùng bất kỳ lớp palette bị cấm nào.
      for (const palette of FORBIDDEN_PALETTE_CLASSES) {
        expect(badge).not.toHaveClass(palette)
      }
    },
  )

  it('gán mỗi trạng thái một token nền khác nhau (phân biệt thị giác)', () => {
    const backgroundTokens = STATUS_VARIANTS.map((status) => status.bg)
    const uniqueTokens = new Set(backgroundTokens)

    expect(uniqueTokens.size).toBe(STATUS_VARIANTS.length)
  })
})
