import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { DataTable } from './DataTable'
import type { MediaSummary } from '../types/api'

// Task 5.7: Unit test token cho feature component DataTable.
// Validates: Requirements 3.2, 14.1, 14.2
//  - Item có thumbnail -> render <img> dùng đúng thumbnail.
//  - Video không có thumbnail -> fallback icon (không có <img> trong ô thumbnail).
//  - Status badge dùng token (statusBadgeClasses: bg-success cho completed).

function makeMedia(overrides: Partial<MediaSummary> = {}): MediaSummary {
  return {
    id: 1,
    file: '/media/photo.jpg',
    thumbnail: null,
    original_filename: 'photo.jpg',
    media_type: 'image',
    mime_type: 'image/jpeg',
    file_size: 2048,
    status: 'completed',
    duration: null,
    caption: '',
    index_key: 'idx-1',
    uploaded_at: '2026-05-01T12:00:00Z',
    updated_at: '2026-05-01T12:00:00Z',
    enqueued_at: null,
    processed_at: null,
    scene_count: 0,
    ...overrides,
  }
}

const noop = () => {}

describe('DataTable thumbnails and status tokens', () => {
  it('renders an <img> when a row has a thumbnail', () => {
    const data = [
      makeMedia({
        id: 1,
        thumbnail: '/media/thumbs/a.jpg',
        original_filename: 'a.jpg',
      }),
    ]

    render(<DataTable data={data} selectedIds={[]} onSelectionChange={noop} />)

    const img = screen.getByRole('img', { name: 'a.jpg' })
    expect(img.getAttribute('src')).toBe('/media/thumbs/a.jpg')
  })

  it('renders a fallback icon (no <img>) for a video row without thumbnail', () => {
    const data = [
      makeMedia({
        id: 2,
        media_type: 'video',
        thumbnail: null,
        file: '/media/clip.mp4',
        original_filename: 'clip.mp4',
      }),
    ]

    render(<DataTable data={data} selectedIds={[]} onSelectionChange={noop} />)

    expect(screen.queryByRole('img')).not.toBeInTheDocument()
  })

  it('status badge uses semantic token classes for completed', () => {
    const data = [makeMedia({ id: 3, status: 'completed', thumbnail: '/media/t.jpg' })]

    const { container } = render(
      <DataTable data={data} selectedIds={[]} onSelectionChange={noop} />,
    )

    expect(container.querySelector('.bg-success')).not.toBeNull()
    expect(container.querySelector('.text-success-foreground')).not.toBeNull()
    // No hardcoded palette classes from the old getStatusColor implementation.
    expect(container.querySelector('.bg-green-100')).toBeNull()
    expect(container.querySelector('.text-green-700')).toBeNull()
  })

  it('status badge uses warning token for processing', () => {
    const data = [makeMedia({ id: 4, status: 'processing', thumbnail: '/media/t.jpg' })]

    const { container } = render(
      <DataTable data={data} selectedIds={[]} onSelectionChange={noop} />,
    )

    expect(container.querySelector('.bg-warning')).not.toBeNull()
  })
})
