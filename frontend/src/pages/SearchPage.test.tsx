import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { SearchPage } from './SearchPage'
import * as client from '../api/client'
import type { SearchResponse, SearchResult } from '../types/api'

vi.mock('../api/client')

const mockOnOpenMedia = vi.fn()

const createSearchResult = (overrides: Partial<SearchResult>): SearchResult => ({
  media_id: 1,
  scene_id: null,
  media_type: 'image',
  result_type: 'image',
  original_filename: 'test.jpg',
  score: 0.9,
  vector_score: 0.85,
  keyword_score: 0.95,
  caption: 'test caption',
  file_url: '/media/test.jpg',
  thumbnail_url: '/media/test_thumb.jpg',
  file_size: 1024,
  created_at: '2026-05-01T12:00:00Z',
  start_time: null,
  end_time: null,
  explanation: {
    match_type: 'visual',
    exact_phrase_match: false,
    rich_caption: false,
    rerank_boost: 0,
  },
  ...overrides,
})

beforeEach(() => {
  mockOnOpenMedia.mockClear()
  vi.mocked(client.searchMedia).mockClear()
  vi.mocked(client.searchMediaByImage).mockClear()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('SearchPage score filter', () => {
  it('shows results with scores below 0.5 when default filter is permissive', () => {
    render(<SearchPage onOpenMedia={mockOnOpenMedia} />)

    const [, scoreSelect] = screen.getAllByRole('combobox')
    expect(scoreSelect).toHaveTextContent('≥ 0.0')
  })

  it('starts without ranking explanation copy before any search results exist', () => {
    render(<SearchPage onOpenMedia={mockOnOpenMedia} />)

    expect(screen.queryByText(/Semantic/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Rich caption/)).not.toBeInTheDocument()
  })

  it('waits longer before firing a text search while typing', () => {
    vi.useFakeTimers()
    vi.mocked(client.searchMedia).mockImplementation(() => new Promise(() => {}))

    render(<SearchPage onOpenMedia={mockOnOpenMedia} />)

    const searchInput = screen.getByPlaceholderText('Search for images and videos...')
    act(() => {
      fireEvent.change(searchInput, { target: { value: 'office' } })
    })

    act(() => {
      vi.advanceTimersByTime(599)
    })
    expect(client.searchMedia).not.toHaveBeenCalled()

    act(() => {
      vi.advanceTimersByTime(1)
    })
    expect(client.searchMedia).toHaveBeenCalledWith('office')
  })
})

describe('SearchPage sorting', () => {
  it('sorts results by created_at when date sort is selected', async () => {
    const mockResponse: SearchResponse = {
      query_mode: 'text',
      query_text: 'office',
      count: 3,
      results: [
        createSearchResult({
          media_id: 1,
          original_filename: 'zzz.jpg',
          created_at: '2026-05-01T10:00:00Z',
          file_size: 100,
          score: 0.95,
        }),
        createSearchResult({
          media_id: 2,
          original_filename: 'aaa.jpg',
          created_at: '2026-05-03T10:00:00Z',
          file_size: 300,
          score: 0.9,
        }),
        createSearchResult({
          media_id: 3,
          original_filename: 'mmm.jpg',
          created_at: '2026-05-02T10:00:00Z',
          file_size: 200,
          score: 0.85,
        }),
      ],
    }

    vi.mocked(client.searchMedia).mockResolvedValue(mockResponse)

    render(<SearchPage onOpenMedia={mockOnOpenMedia} />)

    const searchInput = screen.getByPlaceholderText('Search for images and videos...')
    fireEvent.change(searchInput, { target: { value: 'office' } })
    fireEvent.keyDown(searchInput, { key: 'Enter' })

    await waitFor(() => {
      expect(screen.getByText('3 results for "office"')).toBeInTheDocument()
    })

    const [, , sortSelect] = screen.getAllByRole('combobox')
    fireEvent.click(sortSelect)
    fireEvent.click(screen.getByText('Date'))

    const resultButtons = screen.getAllByRole('button', { name: /Open .*\.jpg/ })
    expect(resultButtons.map((button) => button.getAttribute('aria-label'))).toEqual([
      'Open aaa.jpg',
      'Open mmm.jpg',
      'Open zzz.jpg',
    ])
  })

  it('sorts results by file_size when size sort is selected', async () => {
    const mockResponse: SearchResponse = {
      query_mode: 'text',
      query_text: 'office',
      count: 3,
      results: [
        createSearchResult({
          media_id: 1,
          original_filename: 'aaa.jpg',
          created_at: '2026-05-01T10:00:00Z',
          file_size: 100,
          score: 0.95,
        }),
        createSearchResult({
          media_id: 2,
          original_filename: 'zzz.jpg',
          created_at: '2026-05-03T10:00:00Z',
          file_size: 300,
          score: 0.9,
        }),
        createSearchResult({
          media_id: 3,
          original_filename: 'mmm.jpg',
          created_at: '2026-05-02T10:00:00Z',
          file_size: 200,
          score: 0.85,
        }),
      ],
    }

    vi.mocked(client.searchMedia).mockResolvedValue(mockResponse)

    render(<SearchPage onOpenMedia={mockOnOpenMedia} />)

    const searchInput = screen.getByPlaceholderText('Search for images and videos...')
    fireEvent.change(searchInput, { target: { value: 'office' } })
    fireEvent.keyDown(searchInput, { key: 'Enter' })

    await waitFor(() => {
      expect(screen.getByText('3 results for "office"')).toBeInTheDocument()
    })

    const [, , sortSelect] = screen.getAllByRole('combobox')
    fireEvent.click(sortSelect)
    fireEvent.click(screen.getByText('Size'))

    const resultButtons = screen.getAllByRole('button', { name: /Open .*\.jpg/ })
    expect(resultButtons.map((button) => button.getAttribute('aria-label'))).toEqual([
      'Open zzz.jpg',
      'Open mmm.jpg',
      'Open aaa.jpg',
    ])
  })
})

describe('SearchPage grouped video-scene rendering', () => {
  it('renders a single video-group when multiple scenes from same video are returned', async () => {
    const mockResponse: SearchResponse = {
      query_mode: 'text',
      query_text: 'office desk',
      count: 3,
      results: [
        createSearchResult({
          media_id: 10,
          scene_id: 1,
          result_type: 'video_scene',
          media_type: 'video',
          original_filename: 'demo.mp4',
          start_time: 0,
          end_time: 5,
          score: 0.95,
        }),
        createSearchResult({
          media_id: 10,
          scene_id: 2,
          result_type: 'video_scene',
          media_type: 'video',
          original_filename: 'demo.mp4',
          start_time: 5,
          end_time: 10,
          score: 0.85,
        }),
        createSearchResult({
          media_id: 10,
          scene_id: 3,
          result_type: 'video_scene',
          media_type: 'video',
          original_filename: 'demo.mp4',
          start_time: 10,
          end_time: 15,
          score: 0.80,
        }),
      ],
    }

    vi.mocked(client.searchMedia).mockResolvedValue(mockResponse)

    render(<SearchPage onOpenMedia={mockOnOpenMedia} />)

    const searchInput = screen.getByPlaceholderText('Search for images and videos...')
    fireEvent.change(searchInput, { target: { value: 'office desk' } })
    fireEvent.keyDown(searchInput, { key: 'Enter' })

    await waitFor(() => {
      expect(screen.getByText('1 result for "office desk"')).toBeInTheDocument()
    })

    // Lead scene should be visible
    expect(screen.getByText('demo.mp4')).toBeInTheDocument()
    expect(screen.getByText('0:00 - 0:05')).toBeInTheDocument()

    // Preview scenes should be visible
    expect(screen.getByText('0:05 - 0:10')).toBeInTheDocument()
    expect(screen.getByText('0:10 - 0:15')).toBeInTheDocument()
  })

  it('renders images and video-groups in mixed results preserving order', async () => {
    const mockResponse: SearchResponse = {
      query_mode: 'text',
      query_text: 'office',
      count: 4,
      results: [
        createSearchResult({
          media_id: 1,
          result_type: 'image',
          original_filename: 'office1.jpg',
          score: 0.95,
        }),
        createSearchResult({
          media_id: 10,
          scene_id: 1,
          result_type: 'video_scene',
          media_type: 'video',
          original_filename: 'demo.mp4',
          start_time: 0,
          end_time: 5,
          score: 0.90,
        }),
        createSearchResult({
          media_id: 10,
          scene_id: 2,
          result_type: 'video_scene',
          media_type: 'video',
          original_filename: 'demo.mp4',
          start_time: 5,
          end_time: 10,
          score: 0.85,
        }),
        createSearchResult({
          media_id: 2,
          result_type: 'image',
          original_filename: 'office2.jpg',
          score: 0.80,
        }),
      ],
    }

    vi.mocked(client.searchMedia).mockResolvedValue(mockResponse)

    render(<SearchPage onOpenMedia={mockOnOpenMedia} />)

    const searchInput = screen.getByPlaceholderText('Search for images and videos...')
    fireEvent.change(searchInput, { target: { value: 'office' } })
    fireEvent.keyDown(searchInput, { key: 'Enter' })

    await waitFor(() => {
      expect(screen.getByText('3 results for "office"')).toBeInTheDocument()
    })

    // All three top-level entries should be present
    expect(screen.getByText('office1.jpg')).toBeInTheDocument()
    expect(screen.getByText('demo.mp4')).toBeInTheDocument()
    expect(screen.getByText('office2.jpg')).toBeInTheDocument()
  })

  it('opens lead scene when Enter is pressed on focused video-group', async () => {
    const mockResponse: SearchResponse = {
      query_mode: 'text',
      query_text: 'office',
      count: 2,
      results: [
        createSearchResult({
          media_id: 10,
          scene_id: 1,
          result_type: 'video_scene',
          media_type: 'video',
          original_filename: 'demo.mp4',
          start_time: 0,
          end_time: 5,
          score: 0.95,
        }),
        createSearchResult({
          media_id: 10,
          scene_id: 2,
          result_type: 'video_scene',
          media_type: 'video',
          original_filename: 'demo.mp4',
          start_time: 5,
          end_time: 10,
          score: 0.85,
        }),
      ],
    }

    vi.mocked(client.searchMedia).mockResolvedValue(mockResponse)

    render(<SearchPage onOpenMedia={mockOnOpenMedia} />)

    const searchInput = screen.getByPlaceholderText('Search for images and videos...')
    fireEvent.change(searchInput, { target: { value: 'office' } })
    fireEvent.keyDown(searchInput, { key: 'Enter' })

    await waitFor(() => {
      expect(screen.getByText('1 result for "office"')).toBeInTheDocument()
    })

    // Simulate keyboard navigation: ArrowDown to focus first result
    fireEvent.keyDown(window, { key: 'ArrowDown' })

    // Simulate Enter to open the focused result
    fireEvent.keyDown(window, { key: 'Enter' })

    expect(mockOnOpenMedia).toHaveBeenCalledWith(10, 0)
  })

  it('navigates keyboard focus across top-level render entries only', async () => {
    const mockResponse: SearchResponse = {
      query_mode: 'text',
      query_text: 'office',
      count: 5,
      results: [
        createSearchResult({
          media_id: 1,
          result_type: 'image',
          original_filename: 'office1.jpg',
          score: 0.95,
        }),
        createSearchResult({
          media_id: 10,
          scene_id: 1,
          result_type: 'video_scene',
          media_type: 'video',
          original_filename: 'demo.mp4',
          start_time: 0,
          end_time: 5,
          score: 0.90,
        }),
        createSearchResult({
          media_id: 10,
          scene_id: 2,
          result_type: 'video_scene',
          media_type: 'video',
          original_filename: 'demo.mp4',
          start_time: 5,
          end_time: 10,
          score: 0.85,
        }),
        createSearchResult({
          media_id: 2,
          result_type: 'image',
          original_filename: 'office2.jpg',
          score: 0.80,
        }),
      ],
    }

    vi.mocked(client.searchMedia).mockResolvedValue(mockResponse)

    render(<SearchPage onOpenMedia={mockOnOpenMedia} />)

    const searchInput = screen.getByPlaceholderText('Search for images and videos...')
    fireEvent.change(searchInput, { target: { value: 'office' } })
    fireEvent.keyDown(searchInput, { key: 'Enter' })

    await waitFor(() => {
      expect(screen.getByText('3 results for "office"')).toBeInTheDocument()
    })

    // ArrowDown once: focus first entry (image)
    fireEvent.keyDown(window, { key: 'ArrowDown' })
    const firstCard = screen.getByRole('button', { name: 'Open office1.jpg' })
    expect(firstCard).toHaveClass('ring-primary')

    // ArrowDown again: focus second entry (video-group lead)
    fireEvent.keyDown(window, { key: 'ArrowDown' })
    const secondCard = screen.getByRole('button', { name: 'Open demo.mp4' })
    expect(secondCard).toHaveClass('ring-primary')

    // ArrowDown again: focus third entry (image)
    fireEvent.keyDown(window, { key: 'ArrowDown' })
    const thirdCard = screen.getByRole('button', { name: 'Open office2.jpg' })
    expect(thirdCard).toHaveClass('ring-primary')
  })

  it('opens preview scene when clicked directly', async () => {
    const mockResponse: SearchResponse = {
      query_mode: 'text',
      query_text: 'office',
      count: 2,
      results: [
        createSearchResult({
          media_id: 10,
          scene_id: 1,
          result_type: 'video_scene',
          media_type: 'video',
          original_filename: 'demo.mp4',
          start_time: 0,
          end_time: 5,
          score: 0.95,
        }),
        createSearchResult({
          media_id: 10,
          scene_id: 2,
          result_type: 'video_scene',
          media_type: 'video',
          original_filename: 'demo.mp4',
          start_time: 5,
          end_time: 10,
          score: 0.85,
        }),
      ],
    }

    vi.mocked(client.searchMedia).mockResolvedValue(mockResponse)

    render(<SearchPage onOpenMedia={mockOnOpenMedia} />)

    const searchInput = screen.getByPlaceholderText('Search for images and videos...')
    fireEvent.change(searchInput, { target: { value: 'office' } })
    fireEvent.keyDown(searchInput, { key: 'Enter' })

    await waitFor(() => {
      expect(screen.getByText('1 result for "office"')).toBeInTheDocument()
    })

    // Click the preview scene directly
    const previewScene = screen.getByLabelText(/Open scene #2/)
    fireEvent.click(previewScene)

    expect(mockOnOpenMedia).toHaveBeenCalledWith(10, 5)
  })

  it('resets expanded grouped scenes when a new search returns the same media group', async () => {
    const firstResponse: SearchResponse = {
      query_mode: 'text',
      query_text: 'office',
      count: 4,
      results: [
        createSearchResult({ media_id: 10, scene_id: 1, result_type: 'video_scene', media_type: 'video', original_filename: 'demo.mp4', start_time: 0, end_time: 5, score: 0.95 }),
        createSearchResult({ media_id: 10, scene_id: 2, result_type: 'video_scene', media_type: 'video', original_filename: 'demo.mp4', start_time: 5, end_time: 10, score: 0.85 }),
        createSearchResult({ media_id: 10, scene_id: 3, result_type: 'video_scene', media_type: 'video', original_filename: 'demo.mp4', start_time: 10, end_time: 15, score: 0.8 }),
        createSearchResult({ media_id: 10, scene_id: 4, result_type: 'video_scene', media_type: 'video', original_filename: 'demo.mp4', start_time: 15, end_time: 20, score: 0.75 }),
      ],
    }

    const secondResponse: SearchResponse = {
      query_mode: 'text',
      query_text: 'office updated',
      count: 4,
      results: [
        createSearchResult({ media_id: 10, scene_id: 1, result_type: 'video_scene', media_type: 'video', original_filename: 'demo.mp4', start_time: 0, end_time: 5, score: 0.96 }),
        createSearchResult({ media_id: 10, scene_id: 2, result_type: 'video_scene', media_type: 'video', original_filename: 'demo.mp4', start_time: 5, end_time: 10, score: 0.86 }),
        createSearchResult({ media_id: 10, scene_id: 3, result_type: 'video_scene', media_type: 'video', original_filename: 'demo.mp4', start_time: 10, end_time: 15, score: 0.81 }),
        createSearchResult({ media_id: 10, scene_id: 4, result_type: 'video_scene', media_type: 'video', original_filename: 'demo.mp4', start_time: 15, end_time: 20, score: 0.76 }),
      ],
    }

    vi.mocked(client.searchMedia)
      .mockResolvedValueOnce(firstResponse)
      .mockResolvedValueOnce(secondResponse)

    render(<SearchPage onOpenMedia={mockOnOpenMedia} />)

    const searchInput = screen.getByPlaceholderText('Search for images and videos...')
    fireEvent.change(searchInput, { target: { value: 'office' } })
    fireEvent.keyDown(searchInput, { key: 'Enter' })

    await waitFor(() => {
      expect(screen.getByText('1 result for "office"')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('Show 1 more scene'))
    expect(screen.getByText('0:15 - 0:20')).toBeInTheDocument()

    fireEvent.change(searchInput, { target: { value: 'office updated' } })
    fireEvent.keyDown(searchInput, { key: 'Enter' })

    await waitFor(() => {
      expect(screen.getByText('1 result for "office updated"')).toBeInTheDocument()
    })

    expect(screen.queryByText('0:15 - 0:20')).not.toBeInTheDocument()
    expect(screen.getByText('Show 1 more scene')).toBeInTheDocument()
  })

  it('does not intercept Enter when a preview scene button has focus', async () => {
    const mockResponse: SearchResponse = {
      query_mode: 'text',
      query_text: 'office',
      count: 2,
      results: [
        createSearchResult({ media_id: 10, scene_id: 1, result_type: 'video_scene', media_type: 'video', original_filename: 'demo.mp4', start_time: 0, end_time: 5, score: 0.95 }),
        createSearchResult({ media_id: 10, scene_id: 2, result_type: 'video_scene', media_type: 'video', original_filename: 'demo.mp4', start_time: 5, end_time: 10, score: 0.85 }),
      ],
    }

    vi.mocked(client.searchMedia).mockResolvedValue(mockResponse)

    render(<SearchPage onOpenMedia={mockOnOpenMedia} />)

    const searchInput = screen.getByPlaceholderText('Search for images and videos...')
    fireEvent.change(searchInput, { target: { value: 'office' } })
    fireEvent.keyDown(searchInput, { key: 'Enter' })

    await waitFor(() => {
      expect(screen.getByText('1 result for "office"')).toBeInTheDocument()
    })

    const previewButton = screen.getByLabelText(/Open scene #2/)
    previewButton.focus()

    fireEvent.keyDown(window, { key: 'Enter' })

    expect(mockOnOpenMedia).not.toHaveBeenCalled()
  })
})
