import type { RuntimeStatus } from '../types/api'

interface RuntimeBadgeProps {
  runtime: RuntimeStatus | null
  error: string | null
}

export function RuntimeBadge({ runtime, error }: RuntimeBadgeProps) {
  if (error) {
    return (
      <div className="runtime-card runtime-card-error">
        <p className="eyebrow">Runtime</p>
        <strong>Backend unreachable</strong>
        <span>{error}</span>
      </div>
    )
  }

  if (!runtime) {
    return (
      <div className="runtime-card">
        <p className="eyebrow">Runtime</p>
        <strong>Checking backend</strong>
        <span>Loading CUDA and API diagnostics.</span>
      </div>
    )
  }

  const modeLabel = runtime.selected_device === 'cuda' ? 'GPU active' : 'CPU active'
  const deviceLabel = runtime.gpu_name || 'No dedicated GPU visible'

  return (
    <div className={`runtime-card ${runtime.selected_device === 'cuda' ? 'runtime-card-gpu' : ''}`}>
      <p className="eyebrow">Runtime</p>
      <strong>{modeLabel}</strong>
      <span>{deviceLabel}</span>
      <div className="runtime-tags">
        <span className="tag">{runtime.requested_device}</span>
        <span className="tag">{runtime.strict_cuda ? 'strict-cuda' : 'fallback-ok'}</span>
        <span className="tag">{runtime.torch_installed ? 'torch-ready' : 'torch-missing'}</span>
      </div>
    </div>
  )
}
