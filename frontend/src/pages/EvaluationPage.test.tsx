import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'

import { EvaluationPage } from './EvaluationPage'
import * as client from '../api/client'
import * as evaluationHook from '../hooks/useEvaluation'
import type { EvaluationState } from '../hooks/useEvaluation'
import type { SeedEvaluationMediaResponse } from '../types/api'

vi.mock('../api/client')
vi.mock('../hooks/useEvaluation')

const mockEvaluationState: EvaluationState = {
  status: 'idle',
  total: 0,
  completed: 0,
  queryResults: [],
  runningAggregate: null,
  summary: null,
  error: null,
}

const mockUseEvaluationState = {
  state: mockEvaluationState,
  run: vi.fn(),
  stop: vi.fn(),
  loadRun: vi.fn<() => Promise<void>>(),
}

function createFetchResponse(body: unknown): Response {
  return {
    ok: true,
    json: async () => body,
  } as Response
}

function createSeedResponse(overrides: Partial<SeedEvaluationMediaResponse> = {}): SeedEvaluationMediaResponse {
  return {
    message: 'Evaluation media seeding finished.',
    total: 1,
    uploaded: 1,
    completed: 1,
    failed: 0,
    skipped: 0,
    elapsed_seconds: 0.5,
    results: [],
    ...overrides,
  }
}

describe('EvaluationPage seeding', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(evaluationHook.useEvaluation).mockReturnValue(mockUseEvaluationState)
    vi.stubGlobal('fetch', vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/api/v1/evaluation/baselines')) {
        return Promise.resolve(createFetchResponse({ baselines: [] }))
      }
      if (url.includes('/api/v1/evaluation/runs')) {
        return Promise.resolve(createFetchResponse({ runs: [] }))
      }
      return Promise.resolve(createFetchResponse({}))
    }) as typeof fetch)
  })

  it('renders seed button', () => {
    render(<EvaluationPage />)

    expect(screen.getByRole('button', { name: /Seed Evaluation Media/i })).toBeInTheDocument()
  })

  it('shows seeding summary after success', async () => {
    vi.mocked(client.seedEvaluationMedia).mockResolvedValue(createSeedResponse({
      total: 2,
      uploaded: 2,
      completed: 2,
      elapsed_seconds: 1.23,
    }))

    render(<EvaluationPage />)

    fireEvent.click(screen.getByRole('button', { name: /Seed Evaluation Media/i }))

    await waitFor(() => {
      expect(screen.getByText('Evaluation media seeded')).toBeInTheDocument()
    })
    expect(screen.getByText('Evaluation media seeding finished.')).toBeInTheDocument()
    expect(screen.getByText(/Total:/)).toBeInTheDocument()
    expect(screen.getByText(/Uploaded:/)).toBeInTheDocument()
    expect(screen.getByText(/Completed:/)).toBeInTheDocument()
  })

  it('shows seed error after failure', async () => {
    vi.mocked(client.seedEvaluationMedia).mockRejectedValue(new Error('Seed failed hard'))

    render(<EvaluationPage />)

    fireEvent.click(screen.getByRole('button', { name: /Seed Evaluation Media/i }))

    await waitFor(() => {
      expect(screen.getByText('Error: Seed failed hard')).toBeInTheDocument()
    })
  })

  it('disables run button while seeding', async () => {
    let resolveSeed: ((value: SeedEvaluationMediaResponse) => void) | undefined
    vi.mocked(client.seedEvaluationMedia).mockReturnValue(
      new Promise((resolve) => {
        resolveSeed = resolve
      })
    )

    render(<EvaluationPage />)

    fireEvent.click(screen.getByRole('button', { name: /Seed Evaluation Media/i }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Seeding…/i })).toBeDisabled()
      expect(screen.getByRole('button', { name: /Run Evaluation/i })).toBeDisabled()
    })

    resolveSeed?.(createSeedResponse({ message: 'done' }))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Seed Evaluation Media/i })).toBeEnabled()
    })
  })
})
