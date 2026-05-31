import { describe, it, expect } from 'vitest'
import { readFileSync, readdirSync, existsSync, statSync } from 'node:fs'
import { resolve } from 'node:path'
import { cwd } from 'node:process'

// Task 8.3: Static guard test cho legacy & palette hardcode.
// Validates: Requirements 1.3, 2.1, 2.4, 2.5, 3.2, 11.4, 13.2
//  - File nguồn live KHÔNG còn `import './App.css'` (và mọi tham chiếu App.css).
//  - File nguồn live KHÔNG còn literal palette bị cấm (bg-blue-500, emerald-500...).
//  - File nguồn live KHÔNG còn class legacy (app-shell, nav-item, status-pill...).
//  - Dead_Component & Legacy_Stylesheet đã bị xóa khỏi đĩa.
//
// `tsconfig.app.json` cố tình giới hạn `"types": ["vite/client"]` (không kèm
// "node"), nên @types/node KHÔNG được nạp khi `tsc -b` kiểm tra `src`. Kiểu cho
// các module Node dùng ở đây được khai báo cục bộ trong `src/node-builtins.d.ts`.
// Vitest chạy với cwd tại thư mục `frontend`, nên giải nguồn theo gốc dự án.

const srcRoot = resolve(cwd(), 'src')

/**
 * Thu thập đệ quy mọi file nguồn LIVE dưới `src` với đuôi `.ts`/`.tsx`,
 * LOẠI TRỪ:
 *  - file test (`*.test.ts`, `*.test.tsx`) — để guard không tự bắt chính danh
 *    sách literal bị cấm liệt kê bên trong các file test này,
 *  - file khai báo kiểu (`*.d.ts`).
 */
function collectLiveSourceFiles(dir: string, acc: string[] = []): string[] {
  for (const entry of readdirSync(dir)) {
    const fullPath = resolve(dir, entry)
    if (statSync(fullPath).isDirectory()) {
      collectLiveSourceFiles(fullPath, acc)
      continue
    }
    const isTest = /\.test\.tsx?$/.test(entry)
    const isDecl = /\.d\.ts$/.test(entry)
    const isSource = /\.tsx?$/.test(entry)
    if (isSource && !isTest && !isDecl) {
      acc.push(fullPath)
    }
  }
  return acc
}

const liveFiles = collectLiveSourceFiles(srcRoot)
// Đọc trước nội dung mỗi file một lần để các assertion dùng lại.
const liveSources = liveFiles.map((path) => ({
  path,
  content: readFileSync(path, 'utf-8'),
}))

// Đường dẫn tương đối (gọn) cho thông điệp lỗi dễ đọc.
function rel(path: string): string {
  return path.slice(srcRoot.length + 1).replace(/\\/g, '/')
}

describe('legacy guard: live source files được thu thập', () => {
  it('có ít nhất một file nguồn live (.ts/.tsx, loại test & d.ts)', () => {
    expect(liveSources.length).toBeGreaterThan(0)
  })
})

describe('legacy guard: không còn tham chiếu App.css (R2.1, R2.4)', () => {
  it.each(liveSources)('$path không chứa "App.css"', ({ path, content }) => {
    expect(
      content.includes('App.css'),
      `${rel(path)} vẫn tham chiếu App.css (legacy stylesheet đã bị gỡ)`,
    ).toBe(false)
  })
})

// Literal palette bị cấm theo design.md "No hardcoded palette" (R1.3, R3.2,
// R11.4, R13.2). Mỗi literal được kiểm riêng để thông điệp lỗi nêu rõ literal vi phạm.
const FORBIDDEN_PALETTE_LITERALS = [
  'bg-blue-500',
  'bg-amber-500',
  'bg-emerald-500',
  'bg-orange-100',
  'bg-green-100',
  'bg-green-700',
  'text-green-700',
  'bg-green-500/5',
  'border-green-500/20',
  'bg-black/60',
  'bg-red-500',
  'emerald-500',
  'amber-500',
] as const

describe('legacy guard: không còn literal palette hardcode (R1.3, R3.2, R11.4, R13.2)', () => {
  for (const literal of FORBIDDEN_PALETTE_LITERALS) {
    it(`không file live nào chứa "${literal}"`, () => {
      const offenders = liveSources
        .filter(({ content }) => content.includes(literal))
        .map(({ path }) => rel(path))
      expect(
        offenders,
        `Literal palette bị cấm "${literal}" xuất hiện trong: ${offenders.join(', ')}`,
      ).toEqual([])
    })
  }
})

// Class legacy từ App.css (design.md "No legacy references"). Chỉ dùng các tên
// có dấu gạch nối để tránh false-positive với token Tailwind hay tên biến/component
// live (vd `panel`, `sidebar`, `dropzone` trùng UploadQueuePanel/Sidebar layout/UploadDropzone).
const FORBIDDEN_LEGACY_CLASSES = [
  'app-shell',
  'nav-item',
  'status-pill',
  'hero-card',
  'result-card',
  'queue-item',
  'search-bar',
] as const

describe('legacy guard: không còn class legacy (R2.4)', () => {
  for (const cls of FORBIDDEN_LEGACY_CLASSES) {
    it(`không file live nào chứa class legacy "${cls}"`, () => {
      const offenders = liveSources
        .filter(({ content }) => content.includes(cls))
        .map(({ path }) => rel(path))
      expect(
        offenders,
        `Class legacy "${cls}" xuất hiện trong: ${offenders.join(', ')}`,
      ).toEqual([])
    })
  }
})

describe('legacy guard: dead code & legacy stylesheet đã bị xóa (R2.3, R2.5)', () => {
  const deletedFiles = [
    'src/App.css',
    'src/components/MediaListPanel.tsx',
    'src/components/Sidebar.tsx',
  ]

  it.each(deletedFiles)('%s KHÔNG còn tồn tại trên đĩa', (relativePath) => {
    const fullPath = resolve(cwd(), relativePath)
    expect(
      existsSync(fullPath),
      `${relativePath} vẫn tồn tại — Legacy_Stylesheet/Dead_Component chưa được gỡ`,
    ).toBe(false)
  })
})
