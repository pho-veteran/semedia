import { API_BASE_URL } from '../config'
import type {
  ImageSearchResponse,
  MediaDetail,
  MediaSummary,
  PaginatedResponse,
  RuntimeStatus,
  SearchResponse,
  UploadResponse,
} from '../types/api'

export class ApiError extends Error {
  status: number

  body: unknown

  constructor(message: string, status: number, body: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(new URL(path, API_BASE_URL), init)
  const contentType = response.headers.get('content-type') ?? ''
  const isJson = contentType.includes('application/json')
  const body = isJson ? await response.json() : await response.text()

  if (!response.ok) {
    const message =
      typeof body === 'object' && body !== null && 'detail' in body && typeof body.detail === 'string'
        ? body.detail
        : typeof body === 'object' && body !== null && 'message' in body && typeof body.message === 'string'
          ? body.message
          : typeof body === 'string' && body.trim()
            ? body
            : `Request failed with status ${response.status}`
    throw new ApiError(message, response.status, body)
  }

  return body as T
}

export function getRuntimeStatus() {
  return request<RuntimeStatus>('/api/v1/runtime/')
}

export function getMediaList() {
  return request<PaginatedResponse<MediaSummary>>('/api/v1/media/')
}

export function getMediaDetail(mediaId: number) {
  return request<MediaDetail>(`/api/v1/media/${mediaId}/`)
}

export async function uploadMediaFile(file: File) {
  const formData = new FormData()
  formData.append('file', file)

  return request<UploadResponse>('/api/v1/media/upload/', {
    method: 'POST',
    body: formData,
  })
}

export async function deleteMediaById(mediaId: number) {
  await request<void>(`/api/v1/media/${mediaId}/`, {
    method: 'DELETE',
  })
}

export function searchMedia(queryText: string, topK = 20) {
  return request<SearchResponse>('/api/v1/search/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query_text: queryText,
      top_k: topK,
    }),
  })
}

export function searchMediaByImage(file: File, topK = 20) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('top_k', String(topK))

  return request<ImageSearchResponse>('/api/v1/search/by-image/', {
    method: 'POST',
    body: formData,
  })
}
