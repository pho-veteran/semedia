// Ambient typings cho một số Node built-in dùng trong test (vd:
// `tokenCompleteness.test.ts`). `tsconfig.app.json` đặt `"types": ["vite/client"]`
// (không gồm "node") nên @types/node không được nạp khi `tsc -b` kiểm tra `src`.
//
// File này KHÔNG có top-level import/export => là "script" (global), nhờ vậy các
// khối `declare module` bên dưới là ambient module declarations thực sự, chứ
// không phải module augmentation (vốn yêu cầu module gốc đã tồn tại và sẽ lỗi
// TS2664). Chỉ khai báo đúng API được dùng, KHÔNG kéo theo global của Node
// (vd setTimeout -> NodeJS.Timeout) để tránh xung đột với kiểu DOM trong app.

declare module 'node:fs' {
  export function readFileSync(path: string, encoding: BufferEncoding): string
  export function readdirSync(path: string): string[]
  export function existsSync(path: string): boolean
  export function statSync(path: string): {
    isDirectory(): boolean
    isFile(): boolean
  }
}

declare module 'node:path' {
  export function resolve(...paths: string[]): string
}

declare module 'node:process' {
  export function cwd(): string
}

type BufferEncoding =
  | 'ascii'
  | 'utf8'
  | 'utf-8'
  | 'utf16le'
  | 'ucs2'
  | 'ucs-2'
  | 'base64'
  | 'base64url'
  | 'latin1'
  | 'binary'
  | 'hex'
