/**
 * JSONSchemaEditor Component
 *
 * Monaco Editor wrapper with JSON schema validation and autocomplete.
 * Provides IDE-like editing experience for JSON configurations.
 */

import React, { useRef, useCallback } from 'react';
import Editor, { Monaco } from '@monaco-editor/react';

export interface JSONSchema {
  $schema?: string;
  type: string;
  properties?: Record<string, any>;
  required?: string[];
  [key: string]: any;
}

interface JSONSchemaEditorProps {
  value: string;
  onChange: (value: string) => void;
  schema?: JSONSchema;
  height?: string | number;
  readOnly?: boolean;
  language?: 'json' | 'typescript' | 'javascript';
  theme?: 'vs-dark' | 'vs-light';
  placeholder?: string;
  error?: string;
  onValidate?: (markers: any[]) => void;
}

/**
 * JSONSchemaEditor Component
 *
 * Features:
 * - JSON schema validation
 * - Autocomplete based on schema
 * - Error markers
 * - Format on paste
 * - Syntax highlighting
 *
 * @example
 * ```tsx
 * const schema = {
 *   type: "object",
 *   properties: {
 *     backend_type: { enum: ["state", "filesystem", "store", "composite"] },
 *     config: { type: "object" }
 *   }
 * };
 *
 * <JSONSchemaEditor
 *   value={value}
 *   onChange={setValue}
 *   schema={schema}
 *   error={validationError}
 * />
 * ```
 */
export const JSONSchemaEditor: React.FC<JSONSchemaEditorProps> = ({
  value,
  onChange,
  schema,
  height = '400px',
  readOnly = false,
  language = 'json',
  theme = 'vs-dark',
  placeholder,
  error,
  onValidate,
}) => {
  const editorRef = useRef<any>(null);
  const monacoRef = useRef<Monaco | null>(null);

  const handleEditorDidMount = useCallback(
    (editor: any, monaco: Monaco) => {
      editorRef.current = editor;
      monacoRef.current = monaco;

      // Configure JSON schema if provided
      if (schema && language === 'json') {
        monaco.languages.json.jsonDefaults.setDiagnosticsOptions({
          validate: true,
          schemas: [
            {
              uri: 'http://internal/schema.json',
              fileMatch: ['*'],
              schema: schema,
            },
          ],
        });
      }

      // Set editor options
      editor.updateOptions({
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        fontSize: 14,
        fontFamily: "'Monaco', 'Menlo', 'Ubuntu Mono', 'Consolas', monospace",
        formatOnPaste: true,
        formatOnType: true,
        autoIndent: 'full',
        tabSize: 2,
        readOnly,
        wordWrap: 'on',
        lineNumbers: 'on',
        renderLineHighlight: 'all',
        suggestOnTriggerCharacters: true,
        quickSuggestions: {
          other: true,
          comments: false,
          strings: true,
        },
      });

      // Add validation listener
      if (onValidate) {
        const model = editor.getModel();
        if (model) {
          monaco.editor.onDidChangeMarkers((uris) => {
            const editorUri = model.uri.toString();
            if (uris.find((uri: any) => uri.toString() === editorUri)) {
              const markers = monaco.editor.getModelMarkers({ resource: model.uri });
              onValidate(markers);
            }
          });
        }
      }

      // Show placeholder if empty
      if (!value && placeholder) {
        editor.setValue(`// ${placeholder}\n{}`);
        // Select all so user can start typing
        editor.setPosition({ lineNumber: 2, column: 2 });
      }
    },
    [schema, language, readOnly, onValidate, value, placeholder]
  );

  const handleChange = useCallback(
    (newValue: string | undefined) => {
      if (newValue !== undefined) {
        onChange(newValue);
      }
    },
    [onChange]
  );

  // Format JSON button functionality
  const formatJSON = useCallback(() => {
    if (editorRef.current) {
      editorRef.current.getAction('editor.action.formatDocument')?.run();
    }
  }, []);

  // Validate current JSON
  const validateJSON = useCallback(() => {
    if (!value || !monacoRef.current || !editorRef.current) return null;

    try {
      JSON.parse(value);
      return null;
    } catch (err: any) {
      return err.message;
    }
  }, [value]);

  return (
    <div className="relative">
      <div className={`border rounded-lg overflow-hidden ${error ? 'border-red-500' : 'border-gray-300 dark:border-gray-700'}`}>
        <div className="bg-gray-100 dark:bg-gray-800 px-3 py-2 flex items-center justify-between border-b border-gray-300 dark:border-gray-700">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {language.toUpperCase()} Editor
            {readOnly && <span className="ml-2 text-xs text-gray-500">(Read-only)</span>}
          </span>
          {!readOnly && (
            <button
              type="button"
              onClick={formatJSON}
              className="text-xs px-2 py-1 rounded bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 transition-colors"
              title="Format JSON (Shift+Alt+F)"
            >
              Format
            </button>
          )}
        </div>

        <Editor
          height={height}
          language={language}
          theme={theme}
          value={value}
          onChange={handleChange}
          onMount={handleEditorDidMount}
          options={{
            readOnly,
          }}
          loading={
            <div className="flex items-center justify-center h-full bg-gray-50 dark:bg-gray-900">
              <div className="text-sm text-gray-500">Loading editor...</div>
            </div>
          }
        />
      </div>

      {/* Error message */}
      {error && (
        <div className="mt-2 text-sm text-red-600 dark:text-red-400 flex items-start">
          <svg className="w-4 h-4 mr-1 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {/* Schema validation info */}
      {schema && !error && (
        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          <span>Schema validation enabled</span>
          {schema.required && schema.required.length > 0 && (
            <span className="ml-2">
              • Required: {schema.required.join(', ')}
            </span>
          )}
        </div>
      )}
    </div>
  );
};

/**
 * Hook for managing JSON editor state with validation
 */
export const useJSONEditor = (initialValue: object = {}) => {
  const [value, setValue] = React.useState(JSON.stringify(initialValue, null, 2));
  const [error, setError] = React.useState<string>('');

  const handleChange = useCallback((newValue: string) => {
    setValue(newValue);

    // Validate JSON
    try {
      JSON.parse(newValue);
      setError('');
    } catch (err: any) {
      setError(err.message);
    }
  }, []);

  const getParsedValue = useCallback(() => {
    try {
      return JSON.parse(value);
    } catch {
      return null;
    }
  }, [value]);

  const isValid = useCallback(() => {
    try {
      JSON.parse(value);
      return true;
    } catch {
      return false;
    }
  }, [value]);

  const reset = useCallback((newValue: object = {}) => {
    setValue(JSON.stringify(newValue, null, 2));
    setError('');
  }, []);

  return {
    value,
    error,
    onChange: handleChange,
    getParsedValue,
    isValid,
    reset,
  };
};

export default JSONSchemaEditor;
