import { render, screen, fireEvent } from '@testing-library/react';
import FilesystemViewer from '../FilesystemViewer';
import type { ExecutionTrace } from '../../../types/execution';

describe('FilesystemViewer', () => {
  const mockWriteFileTrace: ExecutionTrace = {
    execution_id: 1,
    sequence_number: 1,
    event_type: 'filesystem_operation',
    content: {
      tool: 'write_file',
      input: { path: '/test.txt', content: 'Hello World' },
      output: { success: true },
    },
    timestamp: '2025-01-08T12:00:00Z',
  };

  const mockReadFileTrace: ExecutionTrace = {
    execution_id: 1,
    sequence_number: 2,
    event_type: 'filesystem_operation',
    content: {
      tool: 'read_file',
      input: { path: '/test.txt' },
      output: { content: 'Hello World' },
    },
    timestamp: '2025-01-08T12:01:00Z',
  };

  const mockCreateDirTrace: ExecutionTrace = {
    execution_id: 1,
    sequence_number: 3,
    event_type: 'filesystem_operation',
    content: {
      tool: 'create_directory',
      input: { path: '/data' },
      output: { success: true },
    },
    timestamp: '2025-01-08T12:02:00Z',
  };

  const mockDeleteFileTrace: ExecutionTrace = {
    execution_id: 1,
    sequence_number: 4,
    event_type: 'filesystem_operation',
    content: {
      tool: 'delete_file',
      input: { path: '/test.txt' },
      output: { success: true },
    },
    timestamp: '2025-01-08T12:03:00Z',
  };

  test('shows empty state when no filesystem operations', () => {
    render(<FilesystemViewer traces={[]} />);
    expect(screen.getByText('No filesystem operations yet')).toBeInTheDocument();
  });

  test('builds filesystem from write_file traces', () => {
    render(<FilesystemViewer traces={[mockWriteFileTrace]} />);

    expect(screen.getByText('/test.txt')).toBeInTheDocument();
    expect(screen.getByText('1 item')).toBeInTheDocument();
  });

  test('builds filesystem from multiple traces', () => {
    const traces = [mockWriteFileTrace, mockCreateDirTrace];
    render(<FilesystemViewer traces={traces} />);

    expect(screen.getByText('/test.txt')).toBeInTheDocument();
    expect(screen.getByText('/data')).toBeInTheDocument();
    expect(screen.getByText('2 items')).toBeInTheDocument();
  });

  test('displays file content on selection', () => {
    render(<FilesystemViewer traces={[mockWriteFileTrace]} />);

    // Click on the file
    fireEvent.click(screen.getByText('/test.txt'));

    // Should display file content
    expect(screen.getByText('Hello World')).toBeInTheDocument();
    expect(screen.getByText('File')).toBeInTheDocument();
  });

  test('handles file deletion by removing from list', () => {
    const traces = [mockWriteFileTrace, mockDeleteFileTrace];
    render(<FilesystemViewer traces={traces} />);

    // File should be deleted after delete trace
    expect(screen.queryByText('/test.txt')).not.toBeInTheDocument();
    expect(screen.getByText('No filesystem operations yet')).toBeInTheDocument();
  });

  test('displays directory type correctly', () => {
    render(<FilesystemViewer traces={[mockCreateDirTrace]} />);

    fireEvent.click(screen.getByText('/data'));

    // Should display Directory text (appears twice: label and content)
    const directoryTexts = screen.getAllByText('Directory');
    expect(directoryTexts.length).toBeGreaterThan(0);
  });

  test('formats file size correctly', () => {
    const largeFileTrace: ExecutionTrace = {
      execution_id: 1,
      sequence_number: 1,
      event_type: 'filesystem_operation',
      content: {
        tool: 'write_file',
        input: { path: '/large.txt', content: 'a'.repeat(2048) },
        output: { success: true },
      },
      timestamp: '2025-01-08T12:00:00Z',
    };

    render(<FilesystemViewer traces={[largeFileTrace]} />);

    // Should display file size
    expect(screen.getByText('2 KB')).toBeInTheDocument();
  });

  test('updates filesystem when edit_file is called', () => {
    const editTrace: ExecutionTrace = {
      execution_id: 1,
      sequence_number: 2,
      event_type: 'filesystem_operation',
      content: {
        tool: 'edit_file',
        input: { path: '/test.txt', content: 'Updated content' },
        output: { success: true },
      },
      timestamp: '2025-01-08T12:01:00Z',
    };

    const traces = [mockWriteFileTrace, editTrace];
    render(<FilesystemViewer traces={traces} />);

    fireEvent.click(screen.getByText('/test.txt'));

    // Should show updated content
    expect(screen.getByText('Updated content')).toBeInTheDocument();
  });

  test('shows only filesystem_operation traces', () => {
    const nonFilesystemTrace: ExecutionTrace = {
      execution_id: 1,
      sequence_number: 5,
      event_type: 'llm_call',
      content: { model: 'gpt-4' },
      timestamp: '2025-01-08T12:04:00Z',
    };

    const traces = [mockWriteFileTrace, nonFilesystemTrace];
    render(<FilesystemViewer traces={traces} />);

    // Should only show 1 item (filesystem operation)
    expect(screen.getByText('1 item')).toBeInTheDocument();
  });

  test('displays select file prompt when no file selected', () => {
    render(<FilesystemViewer traces={[mockWriteFileTrace]} />);

    expect(screen.getByText('Select a file to view its contents')).toBeInTheDocument();
  });

  test('sorts files alphabetically', () => {
    const trace1: ExecutionTrace = {
      ...mockWriteFileTrace,
      content: {
        tool: 'write_file',
        input: { path: '/z-last.txt', content: 'Last' },
        output: { success: true },
      },
    };

    const trace2: ExecutionTrace = {
      ...mockWriteFileTrace,
      sequence_number: 2,
      content: {
        tool: 'write_file',
        input: { path: '/a-first.txt', content: 'First' },
        output: { success: true },
      },
    };

    render(<FilesystemViewer traces={[trace1, trace2]} />);

    const fileItems = screen.getAllByText(/\.txt$/);
    expect(fileItems[0]).toHaveTextContent('/a-first.txt');
    expect(fileItems[1]).toHaveTextContent('/z-last.txt');
  });
});
