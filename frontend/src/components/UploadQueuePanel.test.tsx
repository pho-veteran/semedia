import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UploadQueuePanel } from './UploadQueuePanel'
import type { UploadQueueItem } from '../types/api'

// Task 5.7: Unit test token cho feature component UploadQueuePanel.
// Validates: Requirements 3.2, 16.2
//  - Thanh tiến trình dùng token theo trạng thái (statusProgressBarClass):
//    uploading/pending -> bg-info, processing -> bg-warning, failed -> bg-destructive.
//  - Không dùng palette hardcode (bg-blue-500/bg-amber-500/bg-emerald-500).
//  - Item completed bị lọc bỏ (chỉ render item chưa hoàn tất).

const noop = () => {}

function makeItem(overrides: Partial<UploadQueueItem> = {}): UploadQueueItem {
  return {
    id: 'item-1',
    name: 'clip.mp4',
    mediaId: null,
    status: 'processing',
    updatedAt: '2026-05-01T12:00:00Z',
    message: '',
    ...overrides,
  }
}

// Palette hardcode bị cấm trên thanh tiến trình (Requirement 3.2, 16.2).
const FORBIDDEN_PALETTE = ['bg-blue-500', 'bg-amber-500', 'bg-emerald-500']

function assertNoForbiddenPalette(html: string) {
  for (const palette of FORBIDDEN_PALETTE) {
    expect(html).not.toContain(palette)
  }
}

describe('UploadQueuePanel progress bar uses semantic tokens', () => {
  it('processing item uses warning token for the progress bar', () => {
    const { container } = render(
      <UploadQueuePanel items={[makeItem({ status: 'processing' })]} onOpenMedia={noop} />,
    )

    expect(container.querySelector('.bg-warning')).not.toBeNull()
    expect(screen.getByText('Processing')).toBeInTheDocument()
    assertNoForbiddenPalette(container.innerHTML)
  })

  it('uploading item uses info token for the progress bar', () => {
    const { container } = render(
      <UploadQueuePanel items={[makeItem({ status: 'uploading' })]} onOpenMedia={noop} />,
    )

    expect(container.querySelector('.bg-info')).not.toBeNull()
    expect(screen.getByText('Uploading')).toBeInTheDocument()
    assertNoForbiddenPalette(container.innerHTML)
  })

  it('failed item uses destructive token for the progress bar', () => {
    const { container } = render(
      <UploadQueuePanel items={[makeItem({ status: 'failed' })]} onOpenMedia={noop} />,
    )

    expect(container.querySelector('.bg-destructive')).not.toBeNull()
    expect(screen.getByText('Failed')).toBeInTheDocument()
    assertNoForbiddenPalette(container.innerHTML)
  })

  it('renders fallback icon (no <img>) when an item has no preview', () => {
    render(
      <UploadQueuePanel
        items={[makeItem({ status: 'uploading', mediaType: 'image', previewUrl: undefined })]}
        onOpenMedia={noop}
      />,
    )

    expect(screen.queryByRole('img')).not.toBeInTheDocument()
  })

  it('filters out completed items (renders nothing when all completed)', () => {
    const { container } = render(
      <UploadQueuePanel items={[makeItem({ status: 'completed' })]} onOpenMedia={noop} />,
    )

    expect(container.firstChild).toBeNull()
  })
})
