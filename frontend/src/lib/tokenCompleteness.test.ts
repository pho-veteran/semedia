import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { cwd } from 'node:process'

// Task 1.3: Static guard test cho tính đầy đủ token.
// Validates: Requirements 1.4, 3.1, 11.3
//  - Mỗi Semantic_Color_Token (+ *-foreground) phải xuất hiện trong CẢ khối
//    `:root` lẫn `[data-theme='dark']` của index.css.
//  - tailwind.config.js phải map success/warning/info thành color key dùng được
//    dạng utility (bg-success/text-success-foreground ...).

// `tsconfig.app.json` cố tình giới hạn `"types": ["vite/client"]` (không kèm
// "node"), nên @types/node KHÔNG được nạp khi `tsc -b` kiểm tra `src`. Kiểu cho
// các module Node dùng ở đây được khai báo cục bộ trong `src/node-builtins.d.ts`
// (ambient module, KHÔNG kéo theo global Node để tránh xung đột vd setTimeout).
// Vitest chạy với cwd tại thư mục `frontend`, nên giải nguồn theo gốc dự án
// (tránh phụ thuộc import.meta.url vốn không ổn định khi đường dẫn chứa
// ký tự đặc biệt).
const indexCssPath = resolve(cwd(), 'src/index.css')
const tailwindConfigPath = resolve(cwd(), 'tailwind.config.js')

const indexCss = readFileSync(indexCssPath, 'utf-8')
const tailwindConfig = readFileSync(tailwindConfigPath, 'utf-8')

// Tám nhóm Semantic_Color_Token theo Design_System (Requirement 3.1).
const SEMANTIC_TOKENS = [
  'primary',
  'secondary',
  'brand',
  'success',
  'warning',
  'info',
  'destructive',
  'surface',
] as const

/**
 * Trích nội dung của một CSS rule theo selector, lấy từ `{` tới `}` đầu tiên.
 * Các khối token (`:root`, `[data-theme='dark']`) chỉ chứa khai báo phẳng
 * (không lồng `{}`), nên dừng ở `}` đầu tiên là chính xác.
 */
function extractRuleBody(css: string, selectorPattern: RegExp): string {
  const match = css.match(selectorPattern)
  expect(match, `Không tìm thấy khối khớp ${selectorPattern}`).not.toBeNull()
  return match![1]
}

/**
 * Một biến CSS được khai báo khi xuất hiện dạng `--token:` (cho phép khoảng
 * trắng trước dấu hai chấm). Mẫu này phân biệt `--surface:` với
 * `--surface-foreground:` / `--surface-elevated:`.
 */
function declaresVar(ruleBody: string, varName: string): boolean {
  return new RegExp(`--${varName}\\s*:`).test(ruleBody)
}

describe('index.css token completeness', () => {
  // `:root { ... }` — chỉ khớp khi `{` đứng ngay sau selector.
  const rootBody = extractRuleBody(indexCss, /:root\s*\{([^}]*)\}/)
  // `[data-theme='dark'] { ... }` — `\s*\{` bảo đảm KHÔNG khớp nhầm
  // `[data-theme='dark'] body { ... }`.
  const darkBody = extractRuleBody(indexCss, /\[data-theme='dark'\]\s*\{([^}]*)\}/)

  it('xác định được cả khối :root và [data-theme=\'dark\']', () => {
    expect(rootBody.trim().length).toBeGreaterThan(0)
    expect(darkBody.trim().length).toBeGreaterThan(0)
  })

  describe.each(SEMANTIC_TOKENS)('semantic token "%s"', (token) => {
    const foreground = `${token}-foreground`

    it(`khai báo --${token} trong cả :root và [data-theme='dark']`, () => {
      expect(declaresVar(rootBody, token), `--${token} thiếu trong :root`).toBe(true)
      expect(
        declaresVar(darkBody, token),
        `--${token} thiếu trong [data-theme='dark']`,
      ).toBe(true)
    })

    it(`khai báo --${foreground} trong cả :root và [data-theme='dark']`, () => {
      expect(
        declaresVar(rootBody, foreground),
        `--${foreground} thiếu trong :root`,
      ).toBe(true)
      expect(
        declaresVar(darkBody, foreground),
        `--${foreground} thiếu trong [data-theme='dark']`,
      ).toBe(true)
    })
  })
})

describe('tailwind.config.js semantic color mapping', () => {
  it.each(['success', 'warning', 'info'])(
    'map "%s" thành color key với DEFAULT và foreground theo CSS var',
    (token) => {
      // Khối color key, ví dụ:
      //   success: {
      //     DEFAULT: "hsl(var(--success))",
      //     foreground: "hsl(var(--success-foreground))",
      //   },
      const keyBlock = new RegExp(`${token}\\s*:\\s*\\{([^}]*)\\}`)
      const match = tailwindConfig.match(keyBlock)
      expect(match, `Thiếu color key "${token}" trong tailwind.config.js`).not.toBeNull()

      const body = match![1]
      expect(
        new RegExp(`DEFAULT\\s*:\\s*["'\`]hsl\\(var\\(--${token}\\)\\)`).test(body),
        `color key "${token}" thiếu DEFAULT -> var(--${token})`,
      ).toBe(true)
      expect(
        new RegExp(
          `foreground\\s*:\\s*["'\`]hsl\\(var\\(--${token}-foreground\\)\\)`,
        ).test(body),
        `color key "${token}" thiếu foreground -> var(--${token}-foreground)`,
      ).toBe(true)
    },
  )
})
