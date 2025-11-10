import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { CpuChipIcon } from '@heroicons/react/24/outline';
import { MetricCard } from '../MetricCard';

describe('MetricCard', () => {
  it('renders metric information', () => {
    render(
      <MetricCard
        title="Total Agents"
        value={42}
        icon={<CpuChipIcon data-testid="cpu-icon" />}
      />
    );

    expect(screen.getByText('Total Agents')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(screen.getByTestId('cpu-icon')).toBeInTheDocument();
  });

  it('renders subtitle when provided', () => {
    render(
      <MetricCard
        title="Total Agents"
        value={42}
        subtitle="5 active"
        icon={<CpuChipIcon />}
      />
    );

    expect(screen.getByText('5 active')).toBeInTheDocument();
  });

  it('does not render subtitle when not provided', () => {
    const { container } = render(
      <MetricCard
        title="Total Agents"
        value={42}
        icon={<CpuChipIcon />}
      />
    );

    const subtitleElements = container.querySelectorAll('.text-sm.text-gray-500');
    expect(subtitleElements.length).toBe(0);
  });

  it('renders positive trend indicator', () => {
    render(
      <MetricCard
        title="Total Agents"
        value={42}
        icon={<CpuChipIcon />}
        trend={{ value: 15.5, isPositive: true }}
      />
    );

    const trendElement = screen.getByText(/15.5% vs last period/i);
    expect(trendElement).toBeInTheDocument();
    expect(trendElement).toHaveClass('text-green-600');
    expect(screen.getByText('↑', { exact: false })).toBeInTheDocument();
  });

  it('renders negative trend indicator', () => {
    render(
      <MetricCard
        title="Total Agents"
        value={42}
        icon={<CpuChipIcon />}
        trend={{ value: -8.3, isPositive: false }}
      />
    );

    const trendElement = screen.getByText(/8.3% vs last period/i);
    expect(trendElement).toBeInTheDocument();
    expect(trendElement).toHaveClass('text-red-600');
    expect(screen.getByText('↓', { exact: false })).toBeInTheDocument();
  });

  it('handles click events when onClick is provided', async () => {
    const user = userEvent.setup();
    const handleClick = jest.fn();

    const { container } = render(
      <MetricCard
        title="Total Agents"
        value={42}
        icon={<CpuChipIcon />}
        onClick={handleClick}
      />
    );

    // Find the Card component (outermost div with p-6 class)
    const card = container.querySelector('.p-6.cursor-pointer');
    expect(card).toBeInTheDocument();
    expect(card).toHaveClass('cursor-pointer');

    await user.click(card!);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('does not have cursor-pointer class when onClick is not provided', () => {
    const { container } = render(
      <MetricCard
        title="Total Agents"
        value={42}
        icon={<CpuChipIcon />}
      />
    );

    const card = container.querySelector('.p-6');
    expect(card).toBeInTheDocument();
    expect(card).not.toHaveClass('cursor-pointer');
  });

  it('renders string values', () => {
    render(
      <MetricCard
        title="Success Rate"
        value="95.5%"
        icon={<CpuChipIcon />}
      />
    );

    expect(screen.getByText('95.5%')).toBeInTheDocument();
  });

  it('renders all elements together', () => {
    render(
      <MetricCard
        title="Total Executions"
        value={150}
        subtitle="12 today"
        icon={<CpuChipIcon data-testid="icon" />}
        trend={{ value: 25, isPositive: true }}
        onClick={() => {}}
      />
    );

    expect(screen.getByText('Total Executions')).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument();
    expect(screen.getByText('12 today')).toBeInTheDocument();
    expect(screen.getByTestId('icon')).toBeInTheDocument();
    expect(screen.getByText(/25% vs last period/i)).toBeInTheDocument();
  });
});
