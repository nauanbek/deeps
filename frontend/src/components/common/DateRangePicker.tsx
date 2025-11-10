import React, { useState, useEffect } from 'react';
import { subDays, startOfMonth, endOfMonth, subMonths, startOfDay, endOfDay } from 'date-fns';

export interface DateRangePickerProps {
  onRangeChange: (startDate: string, endDate: string) => void;
  defaultRange?: 'last7days' | 'last30days' | 'last90days' | 'thisMonth' | 'lastMonth';
}

type PresetRange = 'last7days' | 'last30days' | 'last90days' | 'thisMonth' | 'lastMonth' | 'custom';

const DateRangePicker: React.FC<DateRangePickerProps> = ({
  onRangeChange,
  defaultRange = 'last7days',
}) => {
  const [selectedRange, setSelectedRange] = useState<PresetRange>(defaultRange);
  const [customStartDate, setCustomStartDate] = useState<string>('');
  const [customEndDate, setCustomEndDate] = useState<string>('');

  const calculateDateRange = (range: PresetRange): { start: Date; end: Date } => {
    const now = new Date();
    const endOfToday = endOfDay(now);

    switch (range) {
      case 'last7days':
        return { start: startOfDay(subDays(now, 7)), end: endOfToday };
      case 'last30days':
        return { start: startOfDay(subDays(now, 30)), end: endOfToday };
      case 'last90days':
        return { start: startOfDay(subDays(now, 90)), end: endOfToday };
      case 'thisMonth':
        return { start: startOfDay(startOfMonth(now)), end: endOfToday };
      case 'lastMonth': {
        const lastMonth = subMonths(now, 1);
        return {
          start: startOfDay(startOfMonth(lastMonth)),
          end: endOfDay(endOfMonth(lastMonth)),
        };
      }
      default:
        return { start: startOfDay(subDays(now, 7)), end: endOfToday };
    }
  };

  const handleRangeChange = (range: PresetRange) => {
    setSelectedRange(range);

    if (range !== 'custom') {
      const { start, end } = calculateDateRange(range);
      onRangeChange(start.toISOString(), end.toISOString());
    }
  };

  const handleCustomDateChange = () => {
    if (customStartDate && customEndDate) {
      // Parse dates in UTC to avoid timezone issues
      const start = new Date(customStartDate + 'T00:00:00.000Z');
      const end = new Date(customEndDate + 'T23:59:59.999Z');
      onRangeChange(start.toISOString(), end.toISOString());
    }
  };

  useEffect(() => {
    if (customStartDate && customEndDate) {
      handleCustomDateChange();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [customStartDate, customEndDate]);

  useEffect(() => {
    // Trigger initial range on mount
    if (selectedRange !== 'custom') {
      const { start, end } = calculateDateRange(selectedRange);
      onRangeChange(start.toISOString(), end.toISOString());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex flex-col gap-3">
      <div>
        <label htmlFor="date-range-select" className="block text-sm font-medium text-gray-700 mb-1">
          Date Range
        </label>
        <select
          id="date-range-select"
          value={selectedRange}
          onChange={(e) => handleRangeChange(e.target.value as PresetRange)}
          className="block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus-visible:outline-none focus-visible:ring-blue-500 focus-visible:border-blue-500 text-gray-900"
        >
          <option value="last7days">Last 7 days</option>
          <option value="last30days">Last 30 days</option>
          <option value="last90days">Last 90 days</option>
          <option value="thisMonth">This month</option>
          <option value="lastMonth">Last month</option>
          <option value="custom">Custom range</option>
        </select>
      </div>

      {selectedRange === 'custom' && (
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="custom-start-date" className="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              id="custom-start-date"
              type="date"
              value={customStartDate}
              onChange={(e) => setCustomStartDate(e.target.value)}
              className="block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus-visible:outline-none focus-visible:ring-blue-500 focus-visible:border-blue-500 text-gray-900"
            />
          </div>
          <div>
            <label htmlFor="custom-end-date" className="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              id="custom-end-date"
              type="date"
              value={customEndDate}
              onChange={(e) => setCustomEndDate(e.target.value)}
              className="block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus-visible:outline-none focus-visible:ring-blue-500 focus-visible:border-blue-500 text-gray-900"
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default DateRangePicker;
