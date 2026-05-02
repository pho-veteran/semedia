import type { SearchResult } from '../types/api'

export type SearchRenderEntry =
  | { kind: 'single'; item: SearchResult }
  | { kind: 'video-group'; mediaId: number; lead: SearchResult; previews: SearchResult[]; hidden: SearchResult[] }

export function buildSearchRenderEntries(results: SearchResult[]): SearchRenderEntry[] {
  if (results.length === 0) {
    return []
  }

  // Group video scenes by media_id
  const videoGroups = new Map<number, SearchResult[]>()
  const processedVideoMediaIds = new Set<number>()

  for (const result of results) {
    if (result.result_type === 'video_scene') {
      if (!videoGroups.has(result.media_id)) {
        videoGroups.set(result.media_id, [])
      }
      videoGroups.get(result.media_id)!.push(result)
    }
  }

  // Build entries in order of first occurrence
  const entries: SearchRenderEntry[] = []

  for (const result of results) {
    if (result.result_type === 'image') {
      entries.push({ kind: 'single', item: result })
    } else if (result.result_type === 'video_scene') {
      // Only process each video group once (on first occurrence)
      if (!processedVideoMediaIds.has(result.media_id)) {
        processedVideoMediaIds.add(result.media_id)

        const scenes = videoGroups.get(result.media_id)!

        if (scenes.length === 1) {
          entries.push({ kind: 'single', item: scenes[0] })
        } else {
          const lead = scenes[0]
          const previews = scenes.slice(1, 3)
          const hidden = scenes.slice(3)

          entries.push({
            kind: 'video-group',
            mediaId: result.media_id,
            lead,
            previews,
            hidden,
          })
        }
      }
    }
  }

  return entries
}
