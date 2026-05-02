import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { SearchPage } from './SearchPage'

describe('SearchPage score filter', () => {
  it('shows results with scores below 0.5 when default filter is permissive', () => {
    const mockOnOpenMedia = () => {}

    render(<SearchPage onOpenMedia={mockOnOpenMedia} />)

    const [, scoreSelect] = screen.getAllByRole('combobox')
    expect(scoreSelect).toHaveTextContent('≥ 0.0')
  })

  it('starts without ranking explanation copy before any search results exist', () => {
    const mockOnOpenMedia = () => {}

    render(<SearchPage onOpenMedia={mockOnOpenMedia} />)

    expect(screen.queryByText(/Semantic/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Rich caption/)).not.toBeInTheDocument()
  })
})
