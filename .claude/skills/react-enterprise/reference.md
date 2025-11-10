# React Enterprise Reference (2025)

## Quick Reference

### React 19 Changes
- ✅ No `React.memo()`, `useMemo()`, `useCallback()` needed
- ✅ React Compiler handles optimization
- ✅ Only use manual memoization for critical paths

### TanStack Query V5 Breaking Changes
| V4 | V5 |
|----|-----|
| `isLoading` | `isPending` |
| `isInitialLoading` | `isLoading` |
| `cacheTime` | `gcTime` |
| `onSuccess` in query | Remove, use `useEffect` |
| `queryKey` as string | Must be array |

### TypeScript Strict Options
```json
{
  "noUncheckedIndexedAccess": true,  // arr[0] returns T | undefined
  "noImplicitOverride": true,         // Require override keyword
  "exactOptionalPropertyTypes": true  // Distinguish undefined from omitted
}
```

### Const Assertions vs Enums
```typescript
// ❌ OLD: enum (creates runtime code)
enum Status { Active = 'active', Inactive = 'inactive' }

// ✅ NEW: const assertion (zero runtime)
const Status = { Active: 'active', Inactive: 'inactive' } as const;
type Status = typeof Status[keyof typeof Status];
```

## Component Patterns

### Base Component
```typescript
export function Component({ data, onClick }: Props) {
  // No useCallback needed - React Compiler handles it
  const handleClick = () => onClick(data.id);
  
  return <button onClick={handleClick}>{data.name}</button>;
}
```

### Composition Pattern
```typescript
// Compound components
const Card = ({ children }: Props) => <div className="card">{children}</div>;
const CardHeader = ({ children }: Props) => <div className="card-header">{children}</div>;
const CardContent = ({ children }: Props) => <div className="card-content">{children}</div>;

export { Card, CardHeader, CardContent };

// Usage
<Card>
  <CardHeader><h3>Title</h3></CardHeader>
  <CardContent><p>Content</p></CardContent>
</Card>
```

## Data Fetching

### Basic Query
```typescript
const { data, isPending, error } = useQuery({
  queryKey: ['resource'] as const,
  queryFn: fetchResource,
  gcTime: 5 * 60 * 1000,
});
```

### Query with Parameters
```typescript
const { data } = useQuery({
  queryKey: ['resource', id] as const,
  queryFn: () => api.get(`/resource/${id}`),
  enabled: id !== null,
});
```

### Mutation with Optimistic Update
```typescript
const mutation = useMutation({
  mutationFn: createResource,
  onSuccess: (newResource) => {
    queryClient.setQueryData(['resources'], (old) => 
      old ? [...old, newResource] : [newResource]
    );
    queryClient.invalidateQueries({ queryKey: ['resources'] });
  },
});
```

### Parallel Queries
```typescript
const queries = useQueries({
  queries: [
    { queryKey: ['users'], queryFn: fetchUsers },
    { queryKey: ['agents'], queryFn: fetchAgents },
  ],
});

const [usersQuery, agentsQuery] = queries;
```

## State Management

### Zustand Store
```typescript
export const useStore = create<Store>()(
  devtools(
    immer((set) => ({
      count: 0,
      increment: () => set((state) => { state.count += 1; }),
      decrement: () => set((state) => { state.count -= 1; }),
    }))
  )
);

// Selector
export const useCount = () => useStore((state) => state.count);
```

### Store Slicing
```typescript
const createUserSlice = (set) => ({
  user: null,
  setUser: (user) => set({ user }),
});

const createSettingsSlice = (set) => ({
  theme: 'light',
  setTheme: (theme) => set({ theme }),
});

export const useStore = create()((...a) => ({
  ...createUserSlice(...a),
  ...createSettingsSlice(...a),
}));
```

## Forms

### Basic Form
```typescript
const schema = z.object({
  name: z.string().min(3),
  email: z.string().email(),
});

const form = useForm({
  resolver: zodResolver(schema),
  defaultValues: { name: '', email: '' },
});

<form onSubmit={form.handleSubmit(onSubmit)}>
  <input {...form.register('name')} />
  {form.formState.errors.name?.message}
</form>
```

### Async Validation
```typescript
const schema = z.object({
  username: z.string().refine(
    async (val) => {
      const res = await checkAvailability(val);
      return res.available;
    },
    { message: 'Username taken' }
  ),
});
```

### Field Array
```typescript
const { fields, append, remove } = useFieldArray({
  control: form.control,
  name: 'items',
});

{fields.map((field, index) => (
  <div key={field.id}>
    <input {...form.register(`items.${index}.name`)} />
    <button onClick={() => remove(index)}>Remove</button>
  </div>
))}
```

## API Client

### Error Handling
```typescript
try {
  const data = await api.get<Data>('/endpoint');
} catch (error) {
  if (isAPIError(error)) {
    switch (error.type) {
      case 'auth': // Redirect to login
      case 'validation': // Show errors
      case 'not_found': // Show 404
    }
  }
}
```

### Abort Controller
```typescript
const { data } = useQuery({
  queryKey: ['resource'],
  queryFn: async ({ signal }) => {
    return api.get('/resource', { signal });
  },
});
```

### Retry Logic
```typescript
async function fetchWithRetry<T>(
  fn: () => Promise<T>,
  retries = 3,
  delay = 1000
): Promise<T> {
  for (let i = 0; i <= retries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === retries) throw error;
      await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
    }
  }
  throw new Error('Unreachable');
}
```

## WebSocket

### Connection Management
```typescript
const { isConnected, send, disconnect } = useWebSocket(url, {
  onMessage: (data) => console.log(data),
  reconnect: true,
  heartbeat: true,
});

// Send message
send({ type: 'message', payload: data });

// Manual disconnect
disconnect();
```

## Testing

### Component Test
```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

describe('Component', () => {
  it('renders', () => {
    render(<Component />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });
});
```

### Mock API
```typescript
global.fetch = vi.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({ data: 'test' }),
  } as Response)
);
```

### E2E Test
```typescript
import { test, expect } from '@playwright/test';

test('user flow', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button').click();
  await expect(page.getByText('Success')).toBeVisible();
});
```

## Performance

### Code Splitting
```typescript
const LazyComponent = lazy(() => import('./Component'));

<Suspense fallback={<Loading />}>
  <LazyComponent />
</Suspense>
```

### Virtual List
```typescript
const virtualizer = useVirtualizer({
  count: items.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 50,
});
```

### Image Optimization
```typescript
<img src={url} loading="lazy" decoding="async" />
```

## Styling

### Tailwind Classes
```typescript
<div className="flex items-center gap-4 p-4 md:p-6 lg:p-8">
  <h1 className="text-2xl md:text-3xl lg:text-4xl">Title</h1>
</div>
```

### Dark Mode
```typescript
useEffect(() => {
  document.documentElement.classList.toggle('dark', theme === 'dark');
}, [theme]);
```

### CSS Variables
```css
:root {
  --primary: 222.2 47.4% 11.2%;
}
.dark {
  --primary: 210 40% 98%;
}
```

## Build & Deploy

### Vite Build
```bash
pnpm build        # Build for production
pnpm preview      # Preview build locally
```

### Docker Build
```bash
docker build -t app .
docker run -p 80:80 app
```

### Environment Variables
```bash
# .env.local
VITE_API_URL=http://localhost:8000
```

## Accessibility

### ARIA
```typescript
<button aria-label="Close" aria-expanded={isOpen}>
<dialog role="dialog" aria-modal="true" aria-labelledby="title">
<nav role="navigation" aria-label="Main">
```

### Keyboard
```typescript
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Escape') onClose();
  };
  document.addEventListener('keydown', handleKeyDown);
  return () => document.removeEventListener('keydown', handleKeyDown);
}, [onClose]);
```

## Common Patterns

### Loading States
```typescript
if (isPending) return <Skeleton />;
if (error) return <Error error={error} />;
return <Content data={data} />;
```

### Error Recovery
```typescript
<ErrorBoundary fallback={(error, reset) => (
  <div>
    <p>{error.message}</p>
    <button onClick={reset}>Retry</button>
  </div>
)}>
  <App />
</ErrorBoundary>
```

### Debounce
```typescript
const debouncedSearch = useDeferredValue(searchTerm);

useEffect(() => {
  if (debouncedSearch) {
    search(debouncedSearch);
  }
}, [debouncedSearch]);
```

## Migration Checklist

- [ ] Update React to 19
- [ ] Update TanStack Query to V5
- [ ] Enable TypeScript strict mode
- [ ] Remove React.memo/useMemo/useCallback
- [ ] Replace isLoading with isPending
- [ ] Replace cacheTime with gcTime
- [ ] Replace enums with const assertions
- [ ] Add noUncheckedIndexedAccess handling
- [ ] Update Vite to 6+
- [ ] Migrate tests to Vitest

## Dependencies

```json
{
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@tanstack/react-query": "^5.28.0",
    "zustand": "^5.0.0",
    "react-hook-form": "^7.51.0",
    "zod": "^3.23.0",
    "react-router-dom": "^6.22.0",
    "framer-motion": "^11.0.0"
  },
  "devDependencies": {
    "vite": "^6.0.0",
    "typescript": "^5.6.0",
    "vitest": "^2.0.0",
    "@playwright/test": "^1.44.0",
    "tailwindcss": "^4.0.0"
  }
}
```
