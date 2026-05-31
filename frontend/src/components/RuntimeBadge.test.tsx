import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { RuntimeBadge } from './RuntimeBadge'
import type { RuntimeStatus } from '../types/api'

// Task 5.7: Unit test token cho feature component RuntimeBadge.
// Validates: Requirements 3.2
//  - GPU (selected_device === 'cuda') dùng token `success` (text-success / bg-success/*).
//  - CPU dùng token `warning` (text-warning / bg-warning/*).
//  - Không dùng palette hardcode emerald-*/amber-*.

const gpuRuntime: RuntimeStatus = {
  requested_device: 'cuda',
  strict_cuda: false,
  selected_device: 'cuda',
  torch_installed: true,
  cuda_available: true,
  cuda_device_count: 1,
  gpu_name: 'NVIDIA RTX 4090',
}

const cpuRuntime: RuntimeStatus = {
  requested_device: 'cpu',
  strict_cuda: false,
  selected_device: 'cpu',
  torch_installed: true,
  cuda_available: false,
  cuda_device_count: 0,
  gpu_name: '',
}

// Palette hardcode bị cấm trên RuntimeBadge (Requirement 3.2).
const FORBIDDEN_PALETTE = ['emerald-500', 'amber-500']

function assertNoForbiddenPalette(html: string) {
  for (const palette of FORBIDDEN_PALETTE) {
    expect(html).not.toContain(palette)
  }
}

describe('RuntimeBadge uses semantic color tokens', () => {
  it('GPU runtime dùng token success thay vì emerald palette', () => {
    const { container } = render(<RuntimeBadge runtime={gpuRuntime} error={null} />)

    expect(container.querySelector('.text-success')).not.toBeNull()
    expect(container.querySelector('.bg-success\\/5')).not.toBeNull()
    expect(container.querySelector('.text-warning')).toBeNull()
    assertNoForbiddenPalette(container.innerHTML)
  })

  it('CPU runtime dùng token warning thay vì amber palette', () => {
    const { container } = render(<RuntimeBadge runtime={cpuRuntime} error={null} />)

    expect(container.querySelector('.text-warning')).not.toBeNull()
    expect(container.querySelector('.bg-warning\\/5')).not.toBeNull()
    expect(container.querySelector('.text-success')).toBeNull()
    assertNoForbiddenPalette(container.innerHTML)
  })

  it('compact GPU runtime dùng token success', () => {
    const { container } = render(<RuntimeBadge runtime={gpuRuntime} error={null} compact />)

    expect(container.querySelector('.text-success')).not.toBeNull()
    expect(container.querySelector('.bg-success\\/10')).not.toBeNull()
    assertNoForbiddenPalette(container.innerHTML)
  })

  it('compact CPU runtime dùng token warning', () => {
    const { container } = render(<RuntimeBadge runtime={cpuRuntime} error={null} compact />)

    expect(container.querySelector('.text-warning')).not.toBeNull()
    expect(container.querySelector('.bg-warning\\/10')).not.toBeNull()
    assertNoForbiddenPalette(container.innerHTML)
  })
})
