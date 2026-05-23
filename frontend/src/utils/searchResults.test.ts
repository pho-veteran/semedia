import { describe, it, expect } from 'vitest'
import { buildSearchRenderEntries } from './searchResults'
import type { SearchResult } from '../types/api'

describe('buildSearchRenderEntries', () => {
  const createSearchResult = (overrides: Partial<SearchResult>): SearchResult => ({
    media_id: 1,
    scene_id: null,
    scene_index: null,
    scene_key: null,
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

  it('should return empty array for empty input', () => {
    const result = buildSearchRenderEntries([])
    expect(result).toEqual([])
  })

  it('should wrap single image result as kind: single', () => {
    const results = [
      createSearchResult({
        media_id: 1,
        result_type: 'image',
        original_filename: 'image1.jpg',
      }),
    ]

    const entries = buildSearchRenderEntries(results)

    expect(entries).toHaveLength(1)
    expect(entries[0]).toEqual({
      kind: 'single',
      item: results[0],
    })
  })

  it('should wrap multiple image results as separate single entries', () => {
    const results = [
      createSearchResult({
        media_id: 1,
        result_type: 'image',
        original_filename: 'image1.jpg',
      }),
      createSearchResult({
        media_id: 2,
        result_type: 'image',
        original_filename: 'image2.jpg',
      }),
    ]

    const entries = buildSearchRenderEntries(results)

    expect(entries).toHaveLength(2)
    expect(entries[0]).toEqual({ kind: 'single', item: results[0] })
    expect(entries[1]).toEqual({ kind: 'single', item: results[1] })
  })

  it('should wrap single video scene result as kind: single', () => {
    const results = [
      createSearchResult({
        media_id: 1,
        scene_id: 1,
        result_type: 'video_scene',
        media_type: 'video',
        start_time: 0,
        end_time: 5,
      }),
    ]

    const entries = buildSearchRenderEntries(results)

    expect(entries).toHaveLength(1)
    expect(entries[0]).toEqual({
      kind: 'single',
      item: results[0],
    })
  })

  it('should group multiple video scenes from same media_id', () => {
    const results = [
      createSearchResult({
        media_id: 1,
        scene_id: 1,
        result_type: 'video_scene',
        media_type: 'video',
        start_time: 0,
        end_time: 5,
        score: 0.95,
      }),
      createSearchResult({
        media_id: 1,
        scene_id: 2,
        result_type: 'video_scene',
        media_type: 'video',
        start_time: 5,
        end_time: 10,
        score: 0.85,
      }),
    ]

    const entries = buildSearchRenderEntries(results)

    expect(entries).toHaveLength(1)
    expect(entries[0]).toEqual({
      kind: 'video-group',
      mediaId: 1,
      lead: results[0],
      previews: [results[1]],
      hidden: [],
    })
  })

  it('should limit previews to 2 scenes and put rest in hidden', () => {
    const results = [
      createSearchResult({
        media_id: 1,
        scene_id: 1,
        result_type: 'video_scene',
        media_type: 'video',
        start_time: 0,
        end_time: 5,
      }),
      createSearchResult({
        media_id: 1,
        scene_id: 2,
        result_type: 'video_scene',
        media_type: 'video',
        start_time: 5,
        end_time: 10,
      }),
      createSearchResult({
        media_id: 1,
        scene_id: 3,
        result_type: 'video_scene',
        media_type: 'video',
        start_time: 10,
        end_time: 15,
      }),
      createSearchResult({
        media_id: 1,
        scene_id: 4,
        result_type: 'video_scene',
        media_type: 'video',
        start_time: 15,
        end_time: 20,
      }),
    ]

    const entries = buildSearchRenderEntries(results)

    expect(entries).toHaveLength(1)
    expect(entries[0]).toEqual({
      kind: 'video-group',
      mediaId: 1,
      lead: results[0],
      previews: [results[1], results[2]],
      hidden: [results[3]],
    })
  })

  it('should preserve order by first occurrence of each video', () => {
    const results = [
      createSearchResult({
        media_id: 2,
        scene_id: 1,
        result_type: 'video_scene',
        media_type: 'video',
      }),
      createSearchResult({
        media_id: 1,
        scene_id: 1,
        result_type: 'video_scene',
        media_type: 'video',
      }),
      createSearchResult({
        media_id: 2,
        scene_id: 2,
        result_type: 'video_scene',
        media_type: 'video',
      }),
      createSearchResult({
        media_id: 1,
        scene_id: 2,
        result_type: 'video_scene',
        media_type: 'video',
      }),
    ]

    const entries = buildSearchRenderEntries(results)

    expect(entries).toHaveLength(2)
    expect(entries[0].kind).toBe('video-group')
    expect((entries[0] as any).mediaId).toBe(2)
    expect(entries[1].kind).toBe('video-group')
    expect((entries[1] as any).mediaId).toBe(1)
  })

  it('should mix images and video groups preserving order', () => {
    const results = [
      createSearchResult({
        media_id: 1,
        result_type: 'image',
        original_filename: 'image1.jpg',
      }),
      createSearchResult({
        media_id: 2,
        scene_id: 1,
        result_type: 'video_scene',
        media_type: 'video',
      }),
      createSearchResult({
        media_id: 2,
        scene_id: 2,
        result_type: 'video_scene',
        media_type: 'video',
      }),
      createSearchResult({
        media_id: 3,
        result_type: 'image',
        original_filename: 'image2.jpg',
      }),
    ]

    const entries = buildSearchRenderEntries(results)

    expect(entries).toHaveLength(3)
    expect(entries[0]).toEqual({ kind: 'single', item: results[0] })
    expect(entries[1]).toEqual({
      kind: 'video-group',
      mediaId: 2,
      lead: results[1],
      previews: [results[2]],
      hidden: [],
    })
    expect(entries[2]).toEqual({ kind: 'single', item: results[3] })
  })

  it('should handle complex scenario with multiple videos and images', () => {
    const results = [
      createSearchResult({
        media_id: 10,
        scene_id: 1,
        result_type: 'video_scene',
        media_type: 'video',
      }),
      createSearchResult({
        media_id: 20,
        result_type: 'image',
        original_filename: 'img1.jpg',
      }),
      createSearchResult({
        media_id: 10,
        scene_id: 2,
        result_type: 'video_scene',
        media_type: 'video',
      }),
      createSearchResult({
        media_id: 10,
        scene_id: 3,
        result_type: 'video_scene',
        media_type: 'video',
      }),
      createSearchResult({
        media_id: 10,
        scene_id: 4,
        result_type: 'video_scene',
        media_type: 'video',
      }),
      createSearchResult({
        media_id: 30,
        scene_id: 1,
        result_type: 'video_scene',
        media_type: 'video',
      }),
      createSearchResult({
        media_id: 40,
        result_type: 'image',
        original_filename: 'img2.jpg',
      }),
    ]

    const entries = buildSearchRenderEntries(results)

    expect(entries).toHaveLength(4)
    expect(entries[0]).toEqual({
      kind: 'video-group',
      mediaId: 10,
      lead: results[0],
      previews: [results[2], results[3]],
      hidden: [results[4]],
    })
    expect(entries[1]).toEqual({ kind: 'single', item: results[1] })
    expect(entries[2]).toEqual({ kind: 'single', item: results[5] })
    expect(entries[3]).toEqual({ kind: 'single', item: results[6] })
  })
})
