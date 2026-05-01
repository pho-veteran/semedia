import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { SearchPage } from './SearchPage'

describe('SearchPage score filter', () => {
  it('shows results with scores below 0.5 when default filter is permissive', () => {
    // This test will fail until we fix the default scoreFilter from '0.5' to '0.0'
    // The backend returns valid results with scores like 0.18, 0.28, 0.41
    // but the current default filter hides them all

    const mockOnOpenMedia = () => {}

    render(<SearchPage onOpenMedia={mockOnOpenMedia} />)

    // The default score filter should be '0.0' to show all backend results
    // Currently it's '0.5' which hides most text search results
    const [, scoreSelect] = screen.getAllByRole('combobox')
    expect(scoreSelect).toHaveTextContent('≥ 0.0')
  })
})
