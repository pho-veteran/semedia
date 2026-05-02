import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { SearchResultCard } from './SearchResultCard'
import type { SearchResult } from '../types/api'

const onOpenMedia = vi.fn()

const textResult: SearchResult = {
  media_id: 1,
  scene_id: null,
  media_type: 'image',
  result_type: 'image',
  original_filename: 'office.jpg',
  score: 0.59,
  vector_score: 0.3,
  keyword_score: 1.0,
  caption: 'office desk',
  file_url: '/media/office.jpg',
  thumbnail_url: '/media/office.jpg',
  start_time: null,
  end_time: null,
  explanation: {
    match_type: 'caption',
    exact_phrase_match: true,
    rich_caption: false,
    rerank_boost: 0.08,
  },
}

const imageResult: SearchResult = {
  media_id: 2,
  scene_id: null,
  media_type: 'image',
  result_type: 'image',
  original_filename: 'red.jpg',
  score: 0.9,
  vector_score: 0.9,
  keyword_score: 0.0,
  caption: 'a red square',
  file_url: '/media/red.jpg',
  thumbnail_url: '/media/red.jpg',
  start_time: null,
  end_time: null,
  explanation: {
    match_type: 'visual',
    exact_phrase_match: false,
    rich_caption: false,
    rerank_boost: 0.0,
  },
}

const sceneResult: SearchResult = {
  media_id: 3,
  scene_id: 12,
  media_type: 'video',
  result_type: 'video_scene',
  original_filename: 'demo.mp4',
  score: 0.78,
  vector_score: 0.65,
  keyword_score: 0.4,
  caption: 'office desk workspace laptop with bright window light and conference notebooks',
  file_url: '/media/demo.mp4',
  thumbnail_url: '/media/demo-scene.jpg',
  start_time: 12,
  end_time: 18,
  explanation: {
    match_type: 'hybrid',
    exact_phrase_match: true,
    rich_caption: true,
    rerank_boost: 0.1,
  },
}

beforeEach(() => {
  onOpenMedia.mockClear()
})

describe('SearchResultCard explanations', () => {
  it('renders badge-based identity, context, and ranking metadata', () => {
    render(<SearchResultCard item={textResult} onOpenMedia={onOpenMedia} />)

    expect(screen.getByText('Image')).toBeInTheDocument()
    expect(screen.getByText('Exact phrase')).toBeInTheDocument()
    expect(screen.getByText('Caption match · exact phrase in caption')).toBeInTheDocument()
    expect(screen.getByText('Semantic 30%')).toBeInTheDocument()
    expect(screen.getByText('Caption 100%')).toBeInTheDocument()
    expect(screen.getByText('Boost +8%')).toBeInTheDocument()
    expect(screen.getByText('office desk')).toBeInTheDocument()
  })

  it('hides optional badges when the explanation has no extra context', () => {
    render(<SearchResultCard item={imageResult} onOpenMedia={onOpenMedia} />)

    expect(screen.getByText('Image')).toBeInTheDocument()
    expect(screen.getByText('Visual match')).toBeInTheDocument()
    expect(screen.getByText('Semantic 90%')).toBeInTheDocument()
    expect(screen.getByText('Caption 0%')).toBeInTheDocument()
    expect(screen.queryByText('Exact phrase')).not.toBeInTheDocument()
    expect(screen.queryByText('Rich caption')).not.toBeInTheDocument()
    expect(screen.queryByText(/Boost \+/)).not.toBeInTheDocument()
  })

  it('renders scene-specific badges and opens the scene at its start time', () => {
    render(<SearchResultCard item={sceneResult} onOpenMedia={onOpenMedia} />)

    expect(screen.getByText('Scene')).toBeInTheDocument()
    expect(screen.getByText('Scene #12')).toBeInTheDocument()
    expect(screen.getByText('Rich caption')).toBeInTheDocument()
    expect(screen.getByText('Hybrid match · exact phrase in caption · rich caption')).toBeInTheDocument()
    expect(screen.getByText('0:12 - 0:18')).toBeInTheDocument()

    fireEvent.keyDown(screen.getByRole('button', { name: 'Open demo.mp4' }), { key: 'Enter' })

    expect(onOpenMedia).toHaveBeenCalledWith(3, 12)
  })
})
