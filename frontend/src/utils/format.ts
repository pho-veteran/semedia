import { API_BASE_URL } from '../config'
import type { ProcessingStatus, UploadQueueStatus } from '../types/api'

export function getErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message
  }

  return 'Something went wrong while talking to the backend.'
}

export function isTerminalStatus(status: UploadQueueStatus | ProcessingStatus): boolean {
  return status === 'completed' || status === 'failed'
}

export function formatStatusLabel(status: UploadQueueStatus): string {
  switch (status) {
    case 'uploading':
      return 'Uploading'
    case 'pending':
      return 'Pending'
    case 'processing':
      return 'Processing'
    case 'completed':
      return 'Completed'
    case 'failed':
      return 'Failed'
    default:
      return status
  }
}

export function formatFileSize(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) {
    return '0 B'
  }

  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex += 1
  }

  return `${size.toFixed(size >= 10 || unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`
}

export function formatDateTime(value: string | null): string {
  if (!value) {
    return 'N/A'
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

export function formatRelativeTime(value: string | null): string {
  if (!value) {
    return 'N/A'
  }

  const date = new Date(value)
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)

  if (diffInSeconds < 60) {
    return 'Just now'
  }

  const diffInMinutes = Math.floor(diffInSeconds / 60)
  if (diffInMinutes < 60) {
    return `${diffInMinutes}m ago`
  }

  const diffInHours = Math.floor(diffInMinutes / 60)
  if (diffInHours < 24) {
    return `${diffInHours}h ago`
  }

  const diffInDays = Math.floor(diffInHours / 24)
  if (diffInDays < 7) {
    return `${diffInDays}d ago`
  }

  const diffInWeeks = Math.floor(diffInDays / 7)
  if (diffInWeeks < 4) {
    return `${diffInWeeks}w ago`
  }

  const diffInMonths = Math.floor(diffInDays / 30)
  if (diffInMonths < 12) {
    return `${diffInMonths}mo ago`
  }

  const diffInYears = Math.floor(diffInDays / 365)
  return `${diffInYears}y ago`
}

export function formatSeconds(value: number | null): string {
  if (value === null || !Number.isFinite(value)) {
    return '0:00'
  }

  const minutes = Math.floor(value / 60)
  const seconds = Math.floor(value % 60)
  return `${minutes}:${String(seconds).padStart(2, '0')}`
}

export function formatTimeRange(start: number | null, end: number | null): string {
  if (start === null) {
    return 'Image'
  }

  return `${formatSeconds(start)} - ${formatSeconds(end)}`
}

export function formatScore(score: number): string {
  if (!Number.isFinite(score)) {
    return '0%'
  }

  return `${Math.round(score)}%`
}

export function toAbsoluteUrl(value: string | null | undefined): string {
  if (!value) {
    return ''
  }

  if (/^https?:\/\//i.test(value)) {
    return value
  }

  return `${API_BASE_URL}${value.startsWith('/') ? value : `/${value}`}`
}
