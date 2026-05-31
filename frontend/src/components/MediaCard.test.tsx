import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { MediaCard } from './MediaCard'
import type { MediaSummary } from '../types/api'

// Task 5.7: Unit test token cho feature component MediaCard.
// Validates: Requirements 14.1, 14.2
//  - Có thumbnail -> render <img> dùng đúng thumbnail.
//  - Video không có thumbnail -> fallback icon (không có <img>).
//  - Status badge dùng UI_Primitive Badge với token (bg-success).

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

describe('MediaCard preview source', () => {
  it('renders an <img> when a thumbnail is present', () => {
    const media = makeMedia({
      media_type: 'video',
      thumbnail: '/media/thumbs/clip.jpg',
      original_filename: 'clip.mp4',
    })

    render(<MediaCard media={media} />)

    const img = screen.getByRole('img', { name: 'clip.mp4' })
    expect(img).toBeInTheDocument()
    expect(img.getAttribute('src')).toContain('/media/thumbs/clip.jpg')
  })

  it('renders fallback icon (no <img>) for a video without thumbnail', () => {
    const media = makeMedia({
      media_type: 'video',
      thumbnail: null,
      file: '/media/clip.mp4',
      original_filename: 'clip.mp4',
    })

    const { container } = render(<MediaCard media={media} />)

    expect(screen.queryByRole('img')).not.toBeInTheDocument()
    // Fallback rendered on a muted surface using design tokens.
    expect(container.querySelector('.bg-muted')).not.toBeNull()
  })

  it('renders an <img> from file for an image without thumbnail', () => {
    const media = makeMedia({
      media_type: 'image',
      thumbnail: null,
      file: '/media/photo.jpg',
      original_filename: 'photo.jpg',
    })

    render(<MediaCard media={media} />)

    const img = screen.getByRole('img', { name: 'photo.jpg' })
    expect(img.getAttribute('src')).toContain('/media/photo.jpg')
  })

  it('status badge uses semantic token classes', () => {
    const media = makeMedia({ status: 'completed', thumbnail: '/media/t.jpg' })

    const { container } = render(<MediaCard media={media} />)

    // Completed -> success token (from token-based Badge variant).
    expect(container.querySelector('.bg-success')).not.toBeNull()
  })
})
