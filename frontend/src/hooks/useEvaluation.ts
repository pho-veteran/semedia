import { useCallback, useRef, useState } from 'react'
import { API_BASE_URL } from '../config'
import type { SearchResultExplanation } from '../types/api'

export interface QueryMetrics {
  'precision@k': number
  'recall@k': number
  mrr: number
  'ndcg@k': number
}

export interface RetrievedResult {
  media_id: number
  scene_id: number | null
  scene_key: string | null
  scene_index?: number | null
  original_filename: string
  score: number
  vector_score: number
  keyword_score: number
  caption: string
  thumbnail_url: string
  file_url: string
  media_type: string
  result_type: string
  start_time: number | null
  end_time: number | null
  explanation?: SearchResultExplanation
}

export interface ExpectedResult {
  key: string
  result_type: string
  original_filename: string
  thumbnail_url: string
  caption: string
}

export interface QueryResult {
  query_id: string
  query_text: string
  query_type: string
  media_type_target: string
  difficulty: string
  tags: string[]
  'precision@k': number
  'recall@k': number
  mrr: number
  'ndcg@k': number
  retrieved_ids: string[]
  retrieved_scores: number[]
  retrieved_results: RetrievedResult[]
  relevant_ids: string[]
  expected_results?: ExpectedResult[]
}

export interface RunningAggregate {
  'mean_precision@k': number
  'mean_recall@k': number
  mean_mrr: number
  'mean_ndcg@k': number
  num_positive_queries: number
}

export interface GroupMetrics {
  [group: string]: {
    'mean_precision@10': number
    'mean_recall@10': number
    mean_mrr: number
    'mean_ndcg@10': number
    num_queries: number
  }
}

export interface NegativeQuerySummary {
  num_queries: number
  false_positive_rate: number
  mean_false_positives_per_query: number
}

export interface ComparisonResult {
  status: 'ok' | 'regression'
  regressions: string[]
  deltas: Record<string, number>
}

export interface EvaluationSummary {
  num_queries: number
  num_negative_queries: number
  'mean_precision@k': number
  'mean_recall@k': number
  mean_mrr: number
  'mean_ndcg@k': number
  by_type: GroupMetrics
  by_modality: GroupMetrics
  by_difficulty: GroupMetrics
  negative_queries: NegativeQuerySummary
  comparison?: ComparisonResult
  run_id?: number
  created_at?: string
}

export interface SavedRunInfo {
  id: number
  created_at: string
  top_k: number
  num_queries: number
  'mean_precision@k': number | null
  'mean_recall@k': number | null
  mean_mrr: number | null
  'mean_ndcg@k': number | null
}

export type EvalStatus = 'idle' | 'running' | 'completed' | 'error'

export interface EvaluationState {
  status: EvalStatus
  total: number
  completed: number
  queryResults: QueryResult[]
  runningAggregate: RunningAggregate | null
  summary: EvaluationSummary | null
  error: string | null
}

export function useEvaluation() {
  const [state, setState] = useState<EvaluationState>({
    status: 'idle',
    total: 0,
    completed: 0,
    queryResults: [],
    runningAggregate: null,
    summary: null,
    error: null,
  })
  const eventSourceRef = useRef<EventSource | null>(null)

  const run = useCallback((topK = 10, compareTo?: string) => {
    // Close any existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    setState({
      status: 'running',
      total: 0,
      completed: 0,
      queryResults: [],
      runningAggregate: null,
      summary: null,
      error: null,
    })

    const params = new URLSearchParams({ top_k: String(topK) })
    if (compareTo) params.set('compare_to', compareTo)

    const es = new EventSource(`${API_BASE_URL}/api/v1/evaluation/run?${params}`)
    eventSourceRef.current = es

    es.onmessage = (event) => {
      const data = JSON.parse(event.data)

      if (data.type === 'start') {
        setState(prev => ({ ...prev, total: data.total_queries }))
      } else if (data.type === 'query_result') {
        setState(prev => ({
          ...prev,
          completed: data.index + 1,
          queryResults: [...prev.queryResults, data as QueryResult],
          runningAggregate: data.running_aggregate || prev.runningAggregate,
        }))
      } else if (data.type === 'summary') {
        setState(prev => ({
          ...prev,
          status: 'completed',
          summary: data as EvaluationSummary,
        }))
        es.close()
      } else if (data.type === 'error') {
        setState(prev => ({ ...prev, status: 'error', error: data.message }))
        es.close()
      }
    }

    es.onerror = () => {
      setState(prev => {
        // If we already completed, don't override with error
        if (prev.status === 'completed') return prev
        return { ...prev, status: 'error', error: 'Connection lost' }
      })
      es.close()
    }
  }, [])

  const stop = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    setState(prev => ({ ...prev, status: prev.status === 'running' ? 'idle' : prev.status }))
  }, [])

  const loadRun = useCallback(async (runId: number) => {
    const res = await fetch(`${API_BASE_URL}/api/v1/evaluation/runs/${runId}`)
    if (!res.ok) return
    const data = await res.json()
    const summary = { ...data.summary, run_id: data.id, created_at: data.created_at } as EvaluationSummary
    setState({
      status: 'completed',
      total: data.results.length,
      completed: data.results.length,
      queryResults: data.results,
      runningAggregate: null,
      summary,
      error: null,
    })
  }, [])

  return { state, run, stop, loadRun }
}
