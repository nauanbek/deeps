import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import DateRangePicker from '../DateRangePicker';
import { subDays, startOfMonth, endOfMonth, subMonths, format } from 'date-fns';

describe('DateRangePicker', () => {
  const mockOnRangeChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders with default preset', () => {
    render(<DateRangePicker onRangeChange={mockOnRangeChange} />);
    expect(screen.getByRole('combobox')).toBeInTheDocument();
  });

  it('calls onRangeChange with last 7 days on mount with default', () => {
    render(<DateRangePicker onRangeChange={mockOnRangeChange} defaultRange="last7days" />);
    expect(mockOnRangeChange).toHaveBeenCalledTimes(1);
    const [startDate, endDate] = mockOnRangeChange.mock.calls[0];
    expect(startDate).toBeTruthy();
    expect(endDate).toBeTruthy();
  });

  it('selects last 30 days preset', () => {
    render(<DateRangePicker onRangeChange={mockOnRangeChange} />);
    const select = screen.getByRole('combobox');

    fireEvent.change(select, { target: { value: 'last30days' } });

    expect(mockOnRangeChange).toHaveBeenCalled();
    const [startDate, endDate] = mockOnRangeChange.mock.calls[mockOnRangeChange.mock.calls.length - 1];
    expect(startDate).toBeTruthy();
    expect(endDate).toBeTruthy();
  });

  it('selects last 90 days preset', () => {
    render(<DateRangePicker onRangeChange={mockOnRangeChange} />);
    const select = screen.getByRole('combobox');

    fireEvent.change(select, { target: { value: 'last90days' } });

    expect(mockOnRangeChange).toHaveBeenCalled();
  });

  it('selects this month preset', () => {
    render(<DateRangePicker onRangeChange={mockOnRangeChange} />);
    const select = screen.getByRole('combobox');

    fireEvent.change(select, { target: { value: 'thisMonth' } });

    expect(mockOnRangeChange).toHaveBeenCalled();
  });

  it('selects last month preset', () => {
    render(<DateRangePicker onRangeChange={mockOnRangeChange} />);
    const select = screen.getByRole('combobox');

    fireEvent.change(select, { target: { value: 'lastMonth' } });

    expect(mockOnRangeChange).toHaveBeenCalled();
  });

  it('shows custom date inputs when custom range is selected', () => {
    render(<DateRangePicker onRangeChange={mockOnRangeChange} />);
    const select = screen.getByRole('combobox');

    fireEvent.change(select, { target: { value: 'custom' } });

    expect(screen.getByLabelText(/start date/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/end date/i)).toBeInTheDocument();
  });

  it('calls onRangeChange when custom dates are selected', () => {
    render(<DateRangePicker onRangeChange={mockOnRangeChange} />);
    const select = screen.getByRole('combobox');

    fireEvent.change(select, { target: { value: 'custom' } });

    const startInput = screen.getByLabelText(/start date/i);
    const endInput = screen.getByLabelText(/end date/i);

    fireEvent.change(startInput, { target: { value: '2024-01-01' } });
    fireEvent.change(endInput, { target: { value: '2024-01-31' } });

    // Should be called twice (once for start, once for end)
    expect(mockOnRangeChange).toHaveBeenCalled();
    const lastCall = mockOnRangeChange.mock.calls[mockOnRangeChange.mock.calls.length - 1];
    const [startDate, endDate] = lastCall;

    // Verify dates are in ISO format and contain the correct dates
    expect(startDate).toContain('2024-01-01');
    expect(endDate).toContain('2024-01-31');
    expect(startDate).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
    expect(endDate).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
  });

  it('formats dates in ISO format', () => {
    render(<DateRangePicker onRangeChange={mockOnRangeChange} defaultRange="last7days" />);

    const [startDate, endDate] = mockOnRangeChange.mock.calls[0];

    // Check ISO format
    expect(startDate).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
    expect(endDate).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/);
  });
});
