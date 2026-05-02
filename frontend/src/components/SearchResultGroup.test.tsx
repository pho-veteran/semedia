import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { SearchResultGroup } from './SearchResultGroup'
import type { SearchResult } from '../types/api'

const onOpenMedia = vi.fn()

const createSceneResult = (overrides: Partial<SearchResult>): SearchResult => ({
  media_id: 1,
  scene_id: 1,
  media_type: 'video',
  result_type: 'video_scene',
  original_filename: 'demo.mp4',
  score: 0.9,
  vector_score: 0.85,
  keyword_score: 0.95,
  caption: 'office desk',
  file_url: '/media/demo.mp4',
  thumbnail_url: '/media/demo-scene.jpg',
  file_size: 4096,
  created_at: '2026-05-01T12:00:00Z',
  start_time: 0,
  end_time: 5,
  explanation: {
    match_type: 'visual',
    exact_phrase_match: false,
    rich_caption: false,
    rerank_boost: 0,
  },
  ...overrides,
})

const leadScene = createSceneResult({
  scene_id: 1,
  start_time: 0,
  end_time: 5,
  score: 0.95,
})

const previewScene1 = createSceneResult({
  scene_id: 2,
  start_time: 5,
  end_time: 10,
  score: 0.85,
})

const previewScene2 = createSceneResult({
  scene_id: 3,
  start_time: 10,
  end_time: 15,
  score: 0.80,
})

const hiddenScene1 = createSceneResult({
  scene_id: 4,
  start_time: 15,
  end_time: 20,
  score: 0.75,
})

const hiddenScene2 = createSceneResult({
  scene_id: 5,
  start_time: 20,
  end_time: 25,
  score: 0.70,
})

beforeEach(() => {
  onOpenMedia.mockClear()
})

describe('SearchResultGroup', () => {
  it('renders the lead scene using SearchResultCard', () => {
    render(
      <SearchResultGroup
        mediaId={1}
        lead={leadScene}
        previews={[]}
        hidden={[]}
        onOpenMedia={onOpenMedia}
      />
    )

    expect(screen.getByText('demo.mp4')).toBeInTheDocument()
    expect(screen.getByText('0:00 - 0:05')).toBeInTheDocument()
  })

  it('calls onOpenMedia with mediaId and startTime when lead is clicked', () => {
    render(
      <SearchResultGroup
        mediaId={1}
        lead={leadScene}
        previews={[]}
        hidden={[]}
        onOpenMedia={onOpenMedia}
      />
    )

    fireEvent.click(screen.getByRole('button', { name: 'Open demo.mp4' }))

    expect(onOpenMedia).toHaveBeenCalledWith(1, 0)
  })

  it('does not render preview strip when previews array is empty', () => {
    render(
      <SearchResultGroup
        mediaId={1}
        lead={leadScene}
        previews={[]}
        hidden={[]}
        onOpenMedia={onOpenMedia}
      />
    )

    expect(screen.queryByText(/^Show \d+ more scene/)).not.toBeInTheDocument()
  })

  it('renders preview strip with compact scene buttons when previews exist', () => {
    render(
      <SearchResultGroup
        mediaId={1}
        lead={leadScene}
        previews={[previewScene1, previewScene2]}
        hidden={[]}
        onOpenMedia={onOpenMedia}
      />
    )

    expect(screen.getByLabelText(/Open scene #2/)).toBeInTheDocument()
    expect(screen.getByLabelText(/Open scene #3/)).toBeInTheDocument()
  })

  it('renders preview scene thumbnails with time ranges', () => {
    render(
      <SearchResultGroup
        mediaId={1}
        lead={leadScene}
        previews={[previewScene1, previewScene2]}
        hidden={[]}
        onOpenMedia={onOpenMedia}
      />
    )

    expect(screen.getByText('0:05 - 0:10')).toBeInTheDocument()
    expect(screen.getByText('0:10 - 0:15')).toBeInTheDocument()
  })

  it('renders preview scene scores', () => {
    render(
      <SearchResultGroup
        mediaId={1}
        lead={leadScene}
        previews={[previewScene1, previewScene2]}
        hidden={[]}
        onOpenMedia={onOpenMedia}
      />
    )

    expect(screen.getByText('85%')).toBeInTheDocument()
    expect(screen.getByText('80%')).toBeInTheDocument()
  })

  it('calls onOpenMedia with correct startTime when preview scene is clicked', () => {
    render(
      <SearchResultGroup
        mediaId={1}
        lead={leadScene}
        previews={[previewScene1, previewScene2]}
        hidden={[]}
        onOpenMedia={onOpenMedia}
      />
    )

    fireEvent.click(screen.getByLabelText(/Open scene #2/))

    expect(onOpenMedia).toHaveBeenCalledWith(1, 5)
  })

  it('does not render expansion button when hidden array is empty', () => {
    render(
      <SearchResultGroup
        mediaId={1}
        lead={leadScene}
        previews={[previewScene1]}
        hidden={[]}
        onOpenMedia={onOpenMedia}
      />
    )

    expect(screen.queryByText(/^Show \d+ more scene/)).not.toBeInTheDocument()
  })

  it('renders expansion button with correct count when hidden scenes exist', () => {
    render(
      <SearchResultGroup
        mediaId={1}
        lead={leadScene}
        previews={[previewScene1]}
        hidden={[hiddenScene1, hiddenScene2]}
        onOpenMedia={onOpenMedia}
      />
    )

    expect(screen.getByText('Show 2 more scenes')).toBeInTheDocument()
  })

  it('expands to show hidden scenes when expansion button is clicked', () => {
    render(
      <SearchResultGroup
        mediaId={1}
        lead={leadScene}
        previews={[previewScene1]}
        hidden={[hiddenScene1, hiddenScene2]}
        onOpenMedia={onOpenMedia}
      />
    )

    fireEvent.click(screen.getByText('Show 2 more scenes'))

    expect(screen.getByText('0:15 - 0:20')).toBeInTheDocument()
    expect(screen.getByText('0:20 - 0:25')).toBeInTheDocument()
  })

  it('changes button text to "Hide extra scenes" when expanded', () => {
    render(
      <SearchResultGroup
        mediaId={1}
        lead={leadScene}
        previews={[previewScene1]}
        hidden={[hiddenScene1, hiddenScene2]}
        onOpenMedia={onOpenMedia}
      />
    )

    fireEvent.click(screen.getByText('Show 2 more scenes'))

    expect(screen.getByText('Hide extra scenes')).toBeInTheDocument()
    expect(screen.queryByText('Show 2 more scenes')).not.toBeInTheDocument()
  })

  it('collapses hidden scenes when hide button is clicked', () => {
    render(
      <SearchResultGroup
        mediaId={1}
        lead={leadScene}
        previews={[previewScene1]}
        hidden={[hiddenScene1, hiddenScene2]}
        onOpenMedia={onOpenMedia}
      />
    )

    fireEvent.click(screen.getByText('Show 2 more scenes'))
    expect(screen.getByText('0:15 - 0:20')).toBeInTheDocument()

    fireEvent.click(screen.getByText('Hide extra scenes'))
    expect(screen.queryByText('0:15 - 0:20')).not.toBeInTheDocument()
  })

  it('calls onOpenMedia with correct startTime when hidden scene is clicked', () => {
    render(
      <SearchResultGroup
        mediaId={1}
        lead={leadScene}
        previews={[previewScene1]}
        hidden={[hiddenScene1, hiddenScene2]}
        onOpenMedia={onOpenMedia}
      />
    )

    fireEvent.click(screen.getByText('Show 2 more scenes'))

    fireEvent.click(screen.getByLabelText(/Open scene #4/))

    expect(onOpenMedia).toHaveBeenCalledWith(1, 15)
  })

  it('renders hidden scenes in compact layout similar to previews', () => {
    render(
      <SearchResultGroup
        mediaId={1}
        lead={leadScene}
        previews={[previewScene1]}
        hidden={[hiddenScene1, hiddenScene2]}
        onOpenMedia={onOpenMedia}
      />
    )

    fireEvent.click(screen.getByText('Show 2 more scenes'))

    expect(screen.getByText('75%')).toBeInTheDocument()
    expect(screen.getByText('70%')).toBeInTheDocument()
  })

  it('applies className prop to root element', () => {
    const { container } = render(
      <SearchResultGroup
        mediaId={1}
        lead={leadScene}
        previews={[]}
        hidden={[]}
        onOpenMedia={onOpenMedia}
        className="custom-class"
      />
    )

    const root = container.firstChild
    expect(root).toHaveClass('custom-class')
  })

  it('applies isFocused prop to lead card', () => {
    render(
      <SearchResultGroup
        mediaId={1}
        lead={leadScene}
        previews={[]}
        hidden={[]}
        onOpenMedia={onOpenMedia}
        isFocused={true}
      />
    )

    const leadCard = screen.getByRole('button', { name: 'Open demo.mp4' })
    expect(leadCard).toHaveClass('ring-2')
  })

  it('handles single hidden scene correctly', () => {
    render(
      <SearchResultGroup
        mediaId={1}
        lead={leadScene}
        previews={[previewScene1]}
        hidden={[hiddenScene1]}
        onOpenMedia={onOpenMedia}
      />
    )

    expect(screen.getByText('Show 1 more scene')).toBeInTheDocument()
  })

  it('renders preview captions when available', () => {
    const sceneWithCaption = createSceneResult({
      scene_id: 2,
      start_time: 5,
      end_time: 10,
      caption: 'person typing at desk',
    })

    render(
      <SearchResultGroup
        mediaId={1}
        lead={leadScene}
        previews={[sceneWithCaption]}
        hidden={[]}
        onOpenMedia={onOpenMedia}
      />
    )

    expect(screen.getByText('person typing at desk')).toBeInTheDocument()
  })
})
