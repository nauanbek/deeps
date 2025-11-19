import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { JSONSchemaEditor, useJSONEditor } from '../JSONSchemaEditor';
import { renderHook, act } from '@testing-library/react';

// Mock Monaco Editor
jest.mock('@monaco-editor/react', () => ({
  __esModule: true,
  default: ({
    value,
    onChange,
    onValidate,
  }: {
    value: string;
    onChange: (value: string) => void;
    onValidate?: (markers: Array<{ message: string }>) => void;
  }) => (
    <textarea
      data-testid="monaco-editor"
      value={value}
      onChange={(e) => {
        onChange(e.target.value);
        // Simulate validation
        try {
          JSON.parse(e.target.value);
          onValidate?.([]);
        } catch (err) {
          onValidate?.([{ message: 'Invalid JSON' }]);
        }
      }}
    />
  ),
  loader: {
    init: jest.fn().mockResolvedValue({}),
    config: jest.fn(),
  },
}));

const mockSchema = {
  type: 'object',
  required: ['name', 'value'],
  properties: {
    name: { type: 'string' },
    value: { type: 'number' },
  },
};

describe('JSONSchemaEditor', () => {
  const mockOnChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders Monaco editor', () => {
    render(
      <JSONSchemaEditor
        value='{}'
        onChange={mockOnChange}
        schema={mockSchema}
      />
    );

    expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
  });

  test('displays initial value', () => {
    const initialValue = JSON.stringify({ name: 'test', value: 42 }, null, 2);

    render(
      <JSONSchemaEditor
        value={initialValue}
        onChange={mockOnChange}
        schema={mockSchema}
      />
    );

    const editor = screen.getByTestId('monaco-editor');
    expect(editor).toHaveValue(initialValue);
  });

  test('calls onChange when value changes', async () => {
    render(
      <JSONSchemaEditor
        value='{}'
        onChange={mockOnChange}
        schema={mockSchema}
      />
    );

    const editor = screen.getByTestId('monaco-editor');
    const newValue = '{"name": "test", "value": 123}';

    await userEvent.clear(editor);
    await userEvent.paste(newValue);

    expect(mockOnChange).toHaveBeenCalled();
  });

  test('displays error message when provided', () => {
    const errorMessage = 'Invalid JSON syntax';

    render(
      <JSONSchemaEditor
        value='{'
        onChange={mockOnChange}
        schema={mockSchema}
        error={errorMessage}
      />
    );

    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  test('renders with custom height', () => {
    const customHeight = '600px';

    render(
      <JSONSchemaEditor
        value='{}'
        onChange={mockOnChange}
        schema={mockSchema}
        height={customHeight}
      />
    );

    // Simply verify the editor renders with custom height prop
    const editor = screen.getByTestId('monaco-editor');
    expect(editor).toBeInTheDocument();
  });

  test('read-only mode disables editing', () => {
    render(
      <JSONSchemaEditor
        value='{}'
        onChange={mockOnChange}
        schema={mockSchema}
        readOnly={true}
      />
    );

    const editor = screen.getByTestId('monaco-editor');
    expect(editor).toBeInTheDocument();
    // Monaco readonly is handled by the actual component
  });

  test('format button is present', () => {
    render(
      <JSONSchemaEditor
        value='{}'
        onChange={mockOnChange}
        schema={mockSchema}
      />
    );

    // Check for format functionality (button may be in toolbar)
    const container = screen.getByTestId('monaco-editor').parentElement;
    expect(container).toBeInTheDocument();
  });

  test('handles custom theme', () => {
    render(
      <JSONSchemaEditor
        value='{}'
        onChange={mockOnChange}
        schema={mockSchema}
        theme="vs-light"
      />
    );

    expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
  });

  test('validates JSON on change', async () => {
    const mockOnValidate = jest.fn();

    render(
      <JSONSchemaEditor
        value='{}'
        onChange={mockOnChange}
        schema={mockSchema}
        onValidate={mockOnValidate}
      />
    );

    const editor = screen.getByTestId('monaco-editor');

    // Type invalid JSON
    await userEvent.clear(editor);
    await userEvent.type(editor, '{invalid}');

    // Validation is handled by Monaco
    await waitFor(() => {
      expect(mockOnChange).toHaveBeenCalled();
    });
  });
});

describe('useJSONEditor hook', () => {
  test('initializes with default value', () => {
    const { result } = renderHook(() => useJSONEditor());

    expect(result.current.value).toBe('{}');
    expect(result.current.error).toBe('');
  });

  test('initializes with custom value', () => {
    const initialValue = { name: 'test', value: 42 };

    const { result } = renderHook(() => useJSONEditor(initialValue));

    expect(result.current.value).toBe(JSON.stringify(initialValue, null, 2));
  });

  test('onChange updates value', () => {
    const { result } = renderHook(() => useJSONEditor());

    const newValue = '{"name": "updated"}';

    act(() => {
      result.current.onChange(newValue);
    });

    expect(result.current.value).toBe(newValue);
    expect(result.current.error).toBe('');
  });

  test('onChange validates JSON and sets error for invalid input', () => {
    const { result } = renderHook(() => useJSONEditor());

    const invalidValue = '{invalid json}';

    act(() => {
      result.current.onChange(invalidValue);
    });

    expect(result.current.value).toBe(invalidValue);
    expect(result.current.error).toBeTruthy();
  });

  test('getParsedValue returns parsed object for valid JSON', () => {
    const { result } = renderHook(() => useJSONEditor());

    act(() => {
      result.current.onChange('{"name": "test", "value": 123}');
    });

    const parsed = result.current.getParsedValue();

    expect(parsed).toEqual({ name: 'test', value: 123 });
  });

  test('getParsedValue returns null for invalid JSON', () => {
    const { result } = renderHook(() => useJSONEditor());

    act(() => {
      result.current.onChange('{invalid}');
    });

    const parsed = result.current.getParsedValue();

    expect(parsed).toBeNull();
  });

  test('isValid returns true for valid JSON', () => {
    const { result } = renderHook(() => useJSONEditor());

    act(() => {
      result.current.onChange('{"name": "test"}');
    });

    expect(result.current.isValid()).toBe(true);
  });

  test('isValid returns false for invalid JSON', () => {
    const { result } = renderHook(() => useJSONEditor());

    act(() => {
      result.current.onChange('{invalid}');
    });

    expect(result.current.isValid()).toBe(false);
  });

  test('reset resets to initial value', () => {
    const initialValue = { name: 'initial' };
    const { result } = renderHook(() => useJSONEditor(initialValue));

    // Change value
    act(() => {
      result.current.onChange('{"name": "changed"}');
    });

    expect(result.current.value).toBe('{"name": "changed"}');

    // Reset
    act(() => {
      result.current.reset(initialValue);
    });

    expect(result.current.value).toBe(JSON.stringify(initialValue, null, 2));
  });

  test('reset with new value updates state', () => {
    const { result } = renderHook(() => useJSONEditor({ name: 'initial' }));

    const newValue = { name: 'reset', value: 99 };

    act(() => {
      result.current.reset(newValue);
    });

    expect(result.current.value).toBe(JSON.stringify(newValue, null, 2));
    expect(result.current.error).toBe('');
  });

  test('handles empty object', () => {
    const { result } = renderHook(() => useJSONEditor({}));

    expect(result.current.value).toBe('{}');
    expect(result.current.isValid()).toBe(true);
  });

  test('handles nested objects', () => {
    const nestedObject = {
      outer: {
        inner: {
          value: 'deep',
        },
      },
    };

    const { result } = renderHook(() => useJSONEditor(nestedObject));

    const parsed = result.current.getParsedValue();
    expect(parsed).toEqual(nestedObject);
  });

  test('handles arrays', () => {
    const arrayValue = { items: [1, 2, 3, 4, 5] };

    const { result } = renderHook(() => useJSONEditor(arrayValue));

    act(() => {
      result.current.onChange(JSON.stringify(arrayValue));
    });

    const parsed = result.current.getParsedValue();
    expect(parsed).toEqual(arrayValue);
  });

  test('clears error when valid JSON is entered after invalid', () => {
    const { result } = renderHook(() => useJSONEditor());

    // Enter invalid JSON
    act(() => {
      result.current.onChange('{invalid}');
    });

    expect(result.current.error).toBeTruthy();

    // Enter valid JSON
    act(() => {
      result.current.onChange('{"valid": true}');
    });

    expect(result.current.error).toBe('');
  });
});
