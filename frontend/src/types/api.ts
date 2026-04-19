export type MediaType = 'image' | 'video'
export type ProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed'
export type UploadQueueStatus = ProcessingStatus | 'uploading'

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface MediaSummary {
  id: number
  file: string
  original_filename: string
  media_type: MediaType
  mime_type: string
  file_size: number
  status: ProcessingStatus
  duration: number | null
  caption: string
  index_key: string
  uploaded_at: string
  updated_at: string
  enqueued_at: string | null
  processed_at: string | null
  scene_count: number
}

export interface VideoScene {
  id: number
  scene_index: number
  start_time: number
  end_time: number
  keyframe_image: string
  thumbnail_image: string
  caption: string
  index_key: string
}

export interface MediaDetail extends MediaSummary {
  error_message: string
  scenes: VideoScene[]
}

export interface UploadResponse {
  message: string
  processing_enqueued: boolean
  dispatch_backend: string
  data: MediaSummary
}

export interface SearchResult {
  media_id: number
  media_type: MediaType
  result_type: 'image' | 'video_scene'
  original_filename: string
  score: number
  caption: string
  file_url: string
  thumbnail_url: string
  start_time: number | null
  end_time: number | null
}

export interface SearchResponse {
  query_mode: 'text'
  query_text: string
  count: number
  results: SearchResult[]
}

export interface ImageSearchResponse {
  query_mode: 'image'
  query_image_name: string
  count: number
  results: SearchResult[]
}

export interface RuntimeStatus {
  requested_device: string
  strict_cuda: boolean
  preload_models?: boolean
  selected_device: string
  torch_installed: boolean
  cuda_available: boolean
  cuda_device_count: number
  gpu_name: string
}

export interface UploadQueueItem {
  id: string
  name: string
  mediaId: number | null
  status: UploadQueueStatus
  updatedAt: string
  message: string
}
