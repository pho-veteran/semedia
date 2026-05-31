import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { cwd } from 'node:process'

import { Button } from '../ui/Button'
import { Badge } from '../ui/Badge'

// Task 7.6: Test layout.
// Validates: Requirements 6.1, 6.3, 10.2, 11.1
//  - App_Layout là nơi duy nhất giới hạn chiều rộng nội dung (`max-w-[1440px]`)
//    (R6.1).
//  - SearchPage/MediaDetailPage KHÔNG còn ràng buộc `max-w-7xl` cấp trang (R6.3).
//  - Phần tử tương tác hiển thị chỉ báo focus bằng token `ring`
//    (`focus-visible:ring-ring`) (R10.2).
//  - Khi `data-theme='dark'`, token ngữ nghĩa đại diện vẫn được áp dụng cho
//    UI_Primitive (R11.1).
//
// Vitest chạy với cwd tại thư mục `frontend`, nên giải nguồn theo gốc dự án
// (cùng quy ước với `lib/tokenCompleteness.test.ts`). Kiểu cho node built-in
// (`readFileSync`/`resolve`/`cwd`) được khai báo trong `src/node-builtins.d.ts`.
// jsdom KHÔNG tính toán Tailwind CSS, nên các khẳng định dark mode dựa trên tên
// lớp token + thuộc tính `data-theme` thay vì màu đã tính.

const appLayoutSource = readFileSync(
  resolve(cwd(), 'src/components/layout/AppLayout.tsx'),
  'utf-8',
)
const searchPageSource = readFileSync(
  resolve(cwd(), 'src/pages/SearchPage.tsx'),
  'utf-8',
)
const mediaDetailPageSource = readFileSync(
  resolve(cwd(), 'src/pages/MediaDetailPage.tsx'),
  'utf-8',
)

describe('App_Layout owns the max-width container (Requirement 6.1)', () => {
  it('khai báo `max-w-[1440px]` + `mx-auto` trên container nội dung chính', () => {
    expect(appLayoutSource).toContain('max-w-[1440px]')
    expect(appLayoutSource).toContain('mx-auto')
  })
})

describe('Pages bỏ ràng buộc width/padding cấp trang (Requirement 6.3)', () => {
  it('SearchPage không còn dùng `max-w-7xl`', () => {
    expect(searchPageSource).not.toContain('max-w-7xl')
  })

  it('MediaDetailPage không còn dùng `max-w-7xl` ở bất kỳ nhánh nào', () => {
    expect(mediaDetailPageSource).not.toContain('max-w-7xl')
  })
})

describe('Chỉ báo focus dùng token `ring` (Requirement 10.2)', () => {
  it('UI_Primitive Button render lớp `focus-visible:ring-ring`', () => {
    render(<Button>Focusable</Button>)

    const button = screen.getByRole('button', { name: 'Focusable' })
    expect(button).toHaveClass('focus-visible:ring-ring')
  })
})

describe('Dark mode áp dụng token ngữ nghĩa đại diện (Requirement 11.1)', () => {
  afterEach(() => {
    // Thuộc tính `data-theme` là trạng thái global trên documentElement; dọn để
    // không rò rỉ sang test khác.
    document.documentElement.removeAttribute('data-theme')
  })

  it('UI_Primitive đại diện vẫn mang lớp token khi `data-theme=\'dark\'`', () => {
    document.documentElement.setAttribute('data-theme', 'dark')

    render(<Badge variant="completed">completed</Badge>)

    // `data-theme='dark'` được áp dụng ở phạm vi áp token (R11.1).
    expect(document.documentElement).toHaveAttribute('data-theme', 'dark')

    // Token ngữ nghĩa đại diện (`bg-success`/`text-success-foreground`) hiện diện
    // bất kể theme — giá trị màu do CSS var theo `data-theme` quyết định.
    const badge = screen.getByText('completed')
    expect(badge).toHaveClass('bg-success')
    expect(badge).toHaveClass('text-success-foreground')
  })
})
