import { useCallback, useEffect, useState } from 'react'
import { FlaskConical, Play, Square, ChevronDown, ChevronRight, Check, X, AlertTriangle } from 'lucide-react'
import { API_BASE_URL } from '../config'
import {
  useEvaluation,
  type QueryResult,
  type GroupMetrics,
  type ComparisonResult,
  type RetrievedResult,
  type SavedRunInfo,
} from '../hooks/useEvaluation'
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Select,
  SimpleSelectItem,
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '../components/ui'
import {
  contextBadges,
  explanationSummary,
  formatBoost,
  identityBadges,
  shouldShowBoostBadge,
} from '../lib/presentation'
import { cn } from '../lib/utils'
import { formatDateTime, formatScore, toAbsoluteUrl } from '../utils/format'

// --- Label explanations (shown via legend + tooltips) ---

const TYPE_HELP: Record<string, string> = {
  object: 'Object query — find a specific thing (e.g. "airplane")',
  action: 'Action query — find motion/activity, usually in video (e.g. "dog running")',
  scene: 'Scene query — find an overall setting (e.g. "city skyline")',
}
const DIFFICULTY_HELP: Record<string, string> = {
  easy: 'Easy — direct, literal phrasing of the target',
  medium: 'Medium — paraphrased or less direct phrasing',
  hard: 'Hard — tricky wording or a negative/near-miss query',
}
const TARGET_HELP: Record<string, string> = {
  image: 'Target — the correct match is an image',
  video: 'Target — the correct match is a video scene',
  mixed: 'Target — the correct match may be an image or a video',
}
const TAG_HELP: Record<string, string> = {
  negative: 'No relevant asset exists in the corpus; a good system returns nothing strong',
  'near-miss': 'Looks related to a real asset but is not a correct match',
}
const FILTER_HELP: Record<string, string> = {
  all: 'All judged queries',
  hits: 'Queries where at least one relevant item was retrieved',
  misses: 'Queries where no relevant item was retrieved',
  negative: 'Queries that should return nothing relevant',
  object: TYPE_HELP.object,
  action: TYPE_HELP.action,
  scene: TYPE_HELP.scene,
  easy: DIFFICULTY_HELP.easy,
  medium: DIFFICULTY_HELP.medium,
  hard: DIFFICULTY_HELP.hard,
}
const RECALL_HELP = 'Recall@10 — was the relevant item found anywhere in the top 10 results'
const MRR_HELP = 'MRR — 1 ÷ the rank of the first correct hit (100% = ranked first)'

// --- Metric helpers ---

function metricColor(value: number, thresholds: [number, number] = [0.5, 0.8]): string {
  if (value >= thresholds[1]) return 'text-green-600 dark:text-green-400'
  if (value >= thresholds[0]) return 'text-amber-600 dark:text-amber-400'
  return 'text-red-600 dark:text-red-400'
}

function formatMetric(value: number): string {
  return (value * 100).toFixed(1) + '%'
}

function deltaDisplay(delta: number): { text: string; className: string } {
  const pct = (delta * 100).toFixed(1)
  if (delta > 0.001) return { text: `↑${pct}%`, className: 'text-green-600 dark:text-green-400' }
  if (delta < -0.001) return { text: `↓${pct}%`, className: 'text-red-600 dark:text-red-400' }
  return { text: '—', className: 'text-muted-foreground' }
}

// --- Components ---

function MetricCard({ label, value, delta }: { label: string; value: number; delta?: number }) {
  const d = delta !== undefined ? deltaDisplay(delta) : null
  return (
    <Card>
      <CardContent className="pt-4 pb-3 px-4">
        <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide">{label}</p>
        <p className={cn('text-2xl font-bold tabular-nums mt-1', metricColor(value))}>
          {formatMetric(value)}
        </p>
        {d && <p className={cn('text-xs mt-0.5', d.className)}>{d.text}</p>}
      </CardContent>
    </Card>
  )
}

function ProgressBar({ completed, total }: { completed: number; total: number }) {
  const pct = total > 0 ? (completed / total) * 100 : 0
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{completed} / {total} queries</span>
        <span>{pct.toFixed(0)}%</span>
      </div>
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <div
          className="h-full bg-brand rounded-full transition-all duration-300 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

function GroupTable({ data, label }: { data: GroupMetrics; label: string }) {
  const entries = Object.entries(data)
  if (!entries.length) return null
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">{label}</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b text-muted-foreground">
              <th className="text-left px-4 py-2 font-medium">Group</th>
              <th className="text-right px-3 py-2 font-medium">R@10</th>
              <th className="text-right px-3 py-2 font-medium">MRR</th>
              <th className="text-right px-3 py-2 font-medium">NDCG</th>
              <th className="text-right px-4 py-2 font-medium">Queries</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([group, m]) => (
              <tr key={group} className="border-b last:border-0">
                <td className="px-4 py-2 font-medium capitalize">{group}</td>
                <td className={cn('text-right px-3 py-2 tabular-nums', metricColor(m['mean_recall@10']))}>{formatMetric(m['mean_recall@10'])}</td>
                <td className={cn('text-right px-3 py-2 tabular-nums', metricColor(m.mean_mrr))}>{formatMetric(m.mean_mrr)}</td>
                <td className={cn('text-right px-3 py-2 tabular-nums', metricColor(m['mean_ndcg@10']))}>{formatMetric(m['mean_ndcg@10'])}</td>
                <td className="text-right px-4 py-2 text-muted-foreground">{m.num_queries}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </CardContent>
    </Card>
  )
}

function ResultCard({ result, rid, hit }: { result: RetrievedResult; rid: string; hit: boolean }) {
  const thumbUrl = toAbsoluteUrl(result.thumbnail_url || result.file_url)
  const expl = result.explanation
  return (
    <div className={cn('rounded-lg border-2 overflow-hidden', hit ? 'border-green-500' : 'border-red-400/60')}>
      <div className="relative aspect-[16/10] bg-muted">
        {thumbUrl ? (
          <img src={thumbUrl} alt={result.original_filename} className="w-full h-full object-cover" loading="lazy" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-xs text-muted-foreground">No image</div>
        )}
        <div className={cn('absolute top-1 left-1 rounded-full p-0.5', hit ? 'bg-green-500' : 'bg-red-500')}>
          {hit ? <Check size={10} className="text-white" /> : <X size={10} className="text-white" />}
        </div>
        <div className="absolute top-1 right-1">
          <Badge className="bg-black/60 text-white text-[10px] px-1.5 py-0 border-0" title="Final fused score">
            {formatScore(result.score)}
          </Badge>
        </div>
      </div>
      <div className="p-1.5 space-y-1">
        <p className="text-[11px] font-medium truncate" title={result.original_filename}>{result.original_filename}</p>
        <p className="text-[10px] text-muted-foreground truncate" title={rid}>{rid}</p>

        <div className="flex flex-wrap gap-1">
          {identityBadges(result).map(b => (
            <Badge key={b} variant="secondary" className="text-[9px] px-1 py-0">{b}</Badge>
          ))}
          {expl && contextBadges(expl).map(b => (
            <Badge key={b} variant="outline" className="text-[9px] px-1 py-0 bg-accent text-accent-foreground">{b}</Badge>
          ))}
        </div>

        <div className="flex flex-wrap gap-1">
          <Badge variant="outline" className="text-[9px] px-1 py-0" title="CLIP visual similarity (0.7 weight)">
            Sem {formatScore(result.vector_score)}
          </Badge>
          <Badge variant="outline" className="text-[9px] px-1 py-0" title="TF-IDF caption match (0.3 weight)">
            Cap {formatScore(result.keyword_score)}
          </Badge>
          {expl && shouldShowBoostBadge(expl.rerank_boost) && (
            <Badge variant="outline" className="text-[9px] px-1 py-0 bg-success/10 border-success/20" title="Rerank boost added on top of fusion">
              Boost {formatBoost(expl.rerank_boost)}
            </Badge>
          )}
        </div>

        {expl && <p className="text-[10px] text-foreground/80">{explanationSummary(expl)}</p>}
        {result.caption && <p className="text-[10px] text-muted-foreground line-clamp-2">{result.caption}</p>}
      </div>
    </div>
  )
}

function Legend() {
  return (
    <div className="rounded-lg border bg-muted/30 p-3 text-xs text-muted-foreground space-y-1.5">
      <p><span className="font-medium text-foreground">Type</span> — <b>object</b>: a thing · <b>action</b>: motion (usually video) · <b>scene</b>: overall setting</p>
      <p><span className="font-medium text-foreground">Difficulty</span> — <b>easy</b>: literal phrasing · <b>medium</b>: paraphrased · <b>hard</b>: tricky or negative</p>
      <p><span className="font-medium text-foreground">Target</span> — <b>image</b> / <b>video</b> / <b>mixed</b>: which media type should match</p>
      <p><span className="font-medium text-foreground">Tags</span> — <b>negative</b>: no correct asset exists (good = nothing strong returned) · <b>near-miss</b>: looks related but is wrong</p>
      <p><span className="font-medium text-foreground">Columns</span> — <b>R@10</b>: {RECALL_HELP.split('— ')[1]} · <b>MRR</b>: {MRR_HELP.split('— ')[1]}</p>
      <p><span className="font-medium text-foreground">Card scores</span> — <b>%</b>: fused score · <b>Sem</b>: CLIP visual (0.7) · <b>Cap</b>: caption TF-IDF (0.3) · <b>Boost</b>: rerank bonus · green border = correct (relevant) hit, red = not relevant</p>
    </div>
  )
}

function collapseKey(id: string): string {
  if (id.startsWith('scene:')) {
    const parts = id.split(':')
    if (parts.length === 3) return `scene:${parts[1]}`
  }
  return id
}

function ExpectedResults({ query }: { query: QueryResult }) {
  if (query.tags.includes('negative')) {
    return (
      <div className="text-xs text-muted-foreground rounded-md border border-dashed p-2">
        <span className="font-medium text-foreground">Expected:</span> no relevant asset — negative query, so the ideal result is nothing strong.
      </div>
    )
  }
  const expected = query.expected_results
  if (!expected || expected.length === 0) return null
  const retrievedKeys = new Set(query.retrieved_ids.map(collapseKey))
  return (
    <div className="space-y-1.5">
      <p className="text-xs font-medium">Expected (ground truth)</p>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
        {expected.map(e => {
          const found = retrievedKeys.has(e.key)
          const thumb = toAbsoluteUrl(e.thumbnail_url)
          return (
            <div key={e.key} className={cn('rounded-lg border-2 overflow-hidden', found ? 'border-green-500' : 'border-amber-500')}>
              <div className="relative aspect-[16/10] bg-muted">
                {thumb ? (
                  <img src={thumb} alt={e.original_filename} className="w-full h-full object-cover" loading="lazy" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-xs text-muted-foreground">No image</div>
                )}
                <div className="absolute top-1 left-1">
                  <Badge className={cn('text-[9px] px-1 py-0 border-0 text-white', found ? 'bg-green-500' : 'bg-amber-500')}>
                    {found ? 'Found in top 10' : 'Missed'}
                  </Badge>
                </div>
              </div>
              <div className="p-1.5">
                <p className="text-[10px] font-medium truncate" title={e.original_filename}>{e.original_filename}</p>
                <p className="text-[10px] text-muted-foreground truncate" title={e.key}>{e.key}</p>
                {e.caption && <p className="text-[10px] text-muted-foreground line-clamp-2">{e.caption}</p>}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function QueryDrillDown({ query }: { query: QueryResult }) {
  const relevantSet = new Set(query.relevant_ids.map(id => {
    // Apply video credit key logic: scene:file:index -> scene:file
    if (id.startsWith('scene:')) {
      const parts = id.split(':')
      if (parts.length === 3) return `scene:${parts[1]}`
    }
    return id
  }))

  function isHit(retrievedId: string): boolean {
    if (retrievedId.startsWith('scene:')) {
      const parts = retrievedId.split(':')
      if (parts.length === 3) {
        return relevantSet.has(`scene:${parts[1]}`)
      }
    }
    return relevantSet.has(retrievedId)
  }

  return (
    <div className="space-y-3 pt-3 border-t">
      <div className="flex flex-wrap gap-1.5">
        <Badge variant="outline" className="text-xs" title={TYPE_HELP[query.query_type]}>Type: {query.query_type}</Badge>
        <Badge variant="outline" className="text-xs" title={DIFFICULTY_HELP[query.difficulty]}>Difficulty: {query.difficulty}</Badge>
        <Badge variant="outline" className="text-xs" title={TARGET_HELP[query.media_type_target]}>Target: {query.media_type_target}</Badge>
        {query.tags.map(t => <Badge key={t} variant="secondary" className="text-xs" title={TAG_HELP[t] ?? `Tag: ${t}`}>{t}</Badge>)}
      </div>

      <ExpectedResults query={query} />

      <p className="text-xs font-medium">Retrieved (top {query.retrieved_results.length})</p>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
        {query.retrieved_results.map((result, i) => (
          <ResultCard key={query.retrieved_ids[i] + i} result={result} rid={query.retrieved_ids[i]} hit={isHit(query.retrieved_ids[i])} />
        ))}
      </div>

      {/* Show missed relevant items (legacy fallback when expected_results absent) */}
      {!query.expected_results && (() => {
        const retrievedSet = new Set(query.retrieved_ids.map(id => {
          if (id.startsWith('scene:')) {
            const parts = id.split(':')
            if (parts.length === 3) return `scene:${parts[1]}`
          }
          return id
        }))
        const missed = query.relevant_ids.filter(id => {
          const key = id.startsWith('scene:') && id.split(':').length === 3
            ? `scene:${id.split(':')[1]}`
            : id
          return !retrievedSet.has(key)
        })
        if (!missed.length) return null
        return (
          <div className="text-xs text-muted-foreground">
            <span className="font-medium">Missed relevant:</span> {missed.join(', ')}
          </div>
        )
      })()}
    </div>
  )
}

function QueryList({ results, filter }: { results: QueryResult[]; filter: string }) {
  const [expanded, setExpanded] = useState<string | null>(null)

  const filtered = results.filter(r => {
    if (filter === 'all') return true
    if (filter === 'hits') return r['recall@k'] > 0
    if (filter === 'misses') return r['recall@k'] === 0
    if (filter === 'negative') return r.tags.includes('negative')
    return r.query_type === filter || r.difficulty === filter
  })

  return (
    <div className="space-y-1">
      {filtered.map(q => (
        <div key={q.query_id} className="border rounded-lg">
          <button
            className="w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-muted/50 transition-colors"
            onClick={() => setExpanded(expanded === q.query_id ? null : q.query_id)}
          >
            {expanded === q.query_id ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            <span className="text-xs font-mono text-muted-foreground w-10">{q.query_id}</span>
            <span className="text-sm flex-1 truncate">{q.query_text}</span>
            <Badge variant="outline" className="text-[10px]" title={TYPE_HELP[q.query_type]}>{q.query_type}</Badge>
            <Badge variant="outline" className="text-[10px]" title={DIFFICULTY_HELP[q.difficulty]}>{q.difficulty}</Badge>
            <span className={cn('text-xs tabular-nums w-12 text-right', metricColor(q['recall@k']))} title={RECALL_HELP}>
              {formatMetric(q['recall@k'])}
            </span>
            <span className={cn('text-xs tabular-nums w-12 text-right', metricColor(q.mrr))} title={MRR_HELP}>
              {formatMetric(q.mrr)}
            </span>
          </button>
          {expanded === q.query_id && (
            <div className="px-3 pb-3">
              <QueryDrillDown query={q} />
            </div>
          )}
        </div>
      ))}
      {filtered.length === 0 && (
        <p className="text-sm text-muted-foreground text-center py-8">No queries match this filter.</p>
      )}
    </div>
  )
}

function ComparisonView({ comparison }: { comparison: ComparisonResult }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          Baseline Comparison
          <Badge variant={comparison.status === 'ok' ? 'default' : 'destructive'} className="text-xs">
            {comparison.status === 'ok' ? 'No Regressions' : 'Regression Detected'}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
          {Object.entries(comparison.deltas).map(([name, delta]) => {
            const d = deltaDisplay(delta)
            const isRegression = comparison.regressions.includes(name)
            return (
              <div key={name} className={cn('p-2 rounded border', isRegression && 'border-red-500/50 bg-red-50 dark:bg-red-950/20')}>
                <p className="text-[10px] text-muted-foreground truncate">{name}</p>
                <p className={cn('text-sm font-medium', d.className)}>
                  {d.text}
                  {isRegression && <AlertTriangle size={12} className="inline ml-1 text-red-500" />}
                </p>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}

// --- Main Page ---

export function EvaluationPage() {
  const { state, run, stop, loadRun } = useEvaluation()
  const [baselines, setBaselines] = useState<string[]>([])
  const [selectedBaseline, setSelectedBaseline] = useState<string>('')
  const [queryFilter, setQueryFilter] = useState('all')
  const [loadedBaseline, setLoadedBaseline] = useState<Record<string, any> | null>(null)
  const [runs, setRuns] = useState<SavedRunInfo[]>([])

  const fetchRuns = useCallback(() => {
    return fetch(`${API_BASE_URL}/api/v1/evaluation/runs?limit=20`)
      .then(r => r.json())
      .then(d => (d.runs || []) as SavedRunInfo[])
      .catch(() => [] as SavedRunInfo[])
  }, [])

  // Fetch available baselines
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/v1/evaluation/baselines`)
      .then(r => r.json())
      .then(d => setBaselines(d.baselines || []))
      .catch(() => {})
  }, [])

  // On mount, load saved runs and auto-load the most recent one.
  useEffect(() => {
    fetchRuns().then(list => {
      setRuns(list)
      if (list.length > 0) loadRun(list[0].id)
    })
  }, [fetchRuns, loadRun])

  // After a live run completes and is persisted, refresh the saved-run list.
  const completedRunId = state.summary?.run_id
  useEffect(() => {
    if (completedRunId) fetchRuns().then(setRuns)
  }, [completedRunId, fetchRuns])

  const handleRun = useCallback(() => {
    run(10, selectedBaseline || undefined)
  }, [run, selectedBaseline])

  // Load baseline for manual comparison
  const handleLoadBaseline = useCallback((name: string) => {
    if (!name) { setLoadedBaseline(null); return }
    fetch(`${API_BASE_URL}/api/v1/evaluation/baselines/${name}`)
      .then(r => r.json())
      .then(d => setLoadedBaseline(d.report || d))
      .catch(() => {})
  }, [])

  const summary = state.summary
  const agg = state.runningAggregate
  const showMetrics = summary || agg

  // Compute deltas from loaded baseline
  const baselineDeltas: Record<string, number> | null = (() => {
    if (!loadedBaseline || !summary) return null
    return {
      'mean_precision@k': (summary['mean_precision@k'] || 0) - (loadedBaseline['mean_precision@k'] || 0),
      'mean_recall@k': (summary['mean_recall@k'] || 0) - (loadedBaseline['mean_recall@k'] || 0),
      'mean_mrr': (summary.mean_mrr || 0) - (loadedBaseline.mean_mrr || 0),
      'mean_ndcg@k': (summary['mean_ndcg@k'] || 0) - (loadedBaseline['mean_ndcg@k'] || 0),
    }
  })()

  return (
    <div className="flex flex-col gap-6 animate-fade-in">
      {/* Header */}
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <FlaskConical size={28} className="text-brand" />
            Search Quality Evaluation
          </h1>
          <p className="text-sm text-muted-foreground">
            Run the 120-query benchmark against the live search stack and inspect per-query results.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {runs.length > 0 && (
            <Select
              value={state.summary?.run_id ? String(state.summary.run_id) : ''}
              onValueChange={(v) => { if (v) loadRun(Number(v)) }}
              placeholder="View saved run…"
              className="w-[200px]"
            >
              {runs.map(r => (
                <SimpleSelectItem key={r.id} value={String(r.id)}>
                  {formatDateTime(r.created_at)}
                </SimpleSelectItem>
              ))}
            </Select>
          )}
          {baselines.length > 0 && (
            <Select value={selectedBaseline} onValueChange={setSelectedBaseline} placeholder="Compare to baseline…" className="w-[180px]">
              <SimpleSelectItem value="">None</SimpleSelectItem>
              {baselines.map(b => <SimpleSelectItem key={b} value={b}>{b}</SimpleSelectItem>)}
            </Select>
          )}
          {state.status === 'running' ? (
            <Button variant="destructive" size="sm" onClick={stop}>
              <Square size={14} className="mr-1.5" /> Stop
            </Button>
          ) : (
            <Button size="sm" onClick={handleRun}>
              <Play size={14} className="mr-1.5" /> Run Evaluation
            </Button>
          )}
        </div>
      </header>

      {/* Loaded saved-run indicator */}
      {state.status === 'completed' && state.summary?.created_at && (
        <p className="text-xs text-muted-foreground -mt-2">
          Showing saved run #{state.summary.run_id} from {formatDateTime(state.summary.created_at)}
        </p>
      )}

      {/* Progress */}
      {state.status === 'running' && <ProgressBar completed={state.completed} total={state.total} />}

      {/* Error */}
      {state.status === 'error' && (
        <Card className="border-red-500/50">
          <CardContent className="py-3 text-sm text-red-600 dark:text-red-400">
            Error: {state.error}
          </CardContent>
        </Card>
      )}

      {/* Metrics */}
      {showMetrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <MetricCard
            label="Precision@10"
            value={summary?.['mean_precision@k'] ?? agg?.['mean_precision@k'] ?? 0}
            delta={baselineDeltas?.['mean_precision@k']}
          />
          <MetricCard
            label="Recall@10"
            value={summary?.['mean_recall@k'] ?? agg?.['mean_recall@k'] ?? 0}
            delta={baselineDeltas?.['mean_recall@k']}
          />
          <MetricCard
            label="MRR"
            value={summary?.mean_mrr ?? agg?.mean_mrr ?? 0}
            delta={baselineDeltas?.['mean_mrr']}
          />
          <MetricCard
            label="NDCG@10"
            value={summary?.['mean_ndcg@k'] ?? agg?.['mean_ndcg@k'] ?? 0}
            delta={baselineDeltas?.['mean_ndcg@k']}
          />
        </div>
      )}

      {/* Comparison from SSE */}
      {summary?.comparison && <ComparisonView comparison={summary.comparison} />}

      {/* Tabs: Summary / Per-Query */}
      {(state.status === 'completed' || state.queryResults.length > 0) && (
        <Tabs defaultValue="summary">
          <TabsList>
            <TabsTrigger value="summary">Summary</TabsTrigger>
            <TabsTrigger value="queries">Per-Query ({state.queryResults.length})</TabsTrigger>
            {baselines.length > 0 && <TabsTrigger value="compare">Compare</TabsTrigger>}
          </TabsList>

          <TabsContent value="summary" className="space-y-4 mt-4">
            {summary && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <GroupTable data={summary.by_type} label="By Query Type" />
                  <GroupTable data={summary.by_difficulty} label="By Difficulty" />
                  <GroupTable data={summary.by_modality} label="By Modality" />
                </div>
                {summary.negative_queries && summary.negative_queries.num_queries > 0 && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Negative Queries</CardTitle>
                    </CardHeader>
                    <CardContent className="flex gap-6 text-sm">
                      <div>
                        <span className="text-muted-foreground">Queries:</span>{' '}
                        <span className="font-medium">{summary.negative_queries.num_queries}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">FP Rate:</span>{' '}
                        <span className="font-medium">{formatMetric(summary.negative_queries.false_positive_rate)}</span>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Mean FPs/query:</span>{' '}
                        <span className="font-medium">{summary.negative_queries.mean_false_positives_per_query.toFixed(1)}</span>
                      </div>
                    </CardContent>
                  </Card>
                )}
              </>
            )}
            {!summary && state.status === 'running' && (
              <p className="text-sm text-muted-foreground text-center py-8">Evaluation in progress…</p>
            )}
          </TabsContent>

          <TabsContent value="queries" className="mt-4 space-y-3">
            <Legend />
            <div className="flex gap-2 flex-wrap">
              {['all', 'hits', 'misses', 'negative', 'object', 'action', 'scene', 'easy', 'medium', 'hard'].map(f => (
                <Button
                  key={f}
                  variant={queryFilter === f ? 'default' : 'outline'}
                  size="sm"
                  className="text-xs h-7"
                  title={FILTER_HELP[f]}
                  onClick={() => setQueryFilter(f)}
                >
                  {f}
                </Button>
              ))}
            </div>
            <div className="flex items-center gap-3 px-3 text-[10px] text-muted-foreground">
              <span className="flex-1" />
              <span className="w-12 text-right" title={RECALL_HELP}>R@10</span>
              <span className="w-12 text-right" title={MRR_HELP}>MRR</span>
            </div>
            <QueryList results={state.queryResults} filter={queryFilter} />
          </TabsContent>

          <TabsContent value="compare" className="mt-4 space-y-4">
            <div className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground">Load baseline:</span>
              <Select value={selectedBaseline} onValueChange={(v) => { setSelectedBaseline(v); handleLoadBaseline(v) }} placeholder="Select baseline…" className="w-[200px]">
                {baselines.map(b => <SimpleSelectItem key={b} value={b}>{b}</SimpleSelectItem>)}
              </Select>
            </div>
            {loadedBaseline && summary && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader className="pb-2"><CardTitle className="text-sm">Current Run</CardTitle></CardHeader>
                  <CardContent className="space-y-1 text-sm">
                    <p>R@10: <span className="font-medium">{formatMetric(summary['mean_recall@k'])}</span></p>
                    <p>MRR: <span className="font-medium">{formatMetric(summary.mean_mrr)}</span></p>
                    <p>NDCG@10: <span className="font-medium">{formatMetric(summary['mean_ndcg@k'])}</span></p>
                    <p>P@10: <span className="font-medium">{formatMetric(summary['mean_precision@k'])}</span></p>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="pb-2"><CardTitle className="text-sm">Baseline: {selectedBaseline}</CardTitle></CardHeader>
                  <CardContent className="space-y-1 text-sm">
                    <p>R@10: <span className="font-medium">{formatMetric(loadedBaseline['mean_recall@10'] ?? loadedBaseline['mean_recall@k'] ?? 0)}</span></p>
                    <p>MRR: <span className="font-medium">{formatMetric(loadedBaseline['mean_mrr'] ?? 0)}</span></p>
                    <p>NDCG@10: <span className="font-medium">{formatMetric(loadedBaseline['mean_ndcg@10'] ?? loadedBaseline['mean_ndcg@k'] ?? 0)}</span></p>
                    <p>P@10: <span className="font-medium">{formatMetric(loadedBaseline['mean_precision@10'] ?? loadedBaseline['mean_precision@k'] ?? 0)}</span></p>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>
        </Tabs>
      )}

      {/* Idle state */}
      {state.status === 'idle' && state.queryResults.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <FlaskConical size={48} className="mx-auto text-muted-foreground/40 mb-4" />
            <p className="text-muted-foreground">
              Click <strong>Run Evaluation</strong> to execute the benchmark against the live search stack.
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              120 queries • P@10, R@10, MRR, NDCG@10 • per-query drill-down with thumbnails
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
