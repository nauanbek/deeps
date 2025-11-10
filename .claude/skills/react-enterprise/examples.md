# React Enterprise Examples

## Complete Agent Management Example

```typescript
// src/pages/AgentStudio.tsx
import { useState } from 'react';
import { useAgents, useCreateAgent, useUpdateAgent, useDeleteAgent } from '@/hooks/useAgents';
import { AgentCard } from '@/components/agents/AgentCard';
import { AgentForm } from '@/components/agents/AgentForm';
import { Button } from '@/components/ui/button';
import type { AgentFormData } from '@/types/agent';

export function AgentStudio() {
  const [isCreating, setIsCreating] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);

  // TanStack Query V5 hooks
  const { data: agents, isPending, error } = useAgents();
  const createMutation = useCreateAgent();
  const updateMutation = useUpdateAgent();
  const deleteMutation = useDeleteAgent();

  const handleCreate = async (data: AgentFormData) => {
    await createMutation.mutateAsync(data);
    setIsCreating(false);
  };

  const handleUpdate = async (data: AgentFormData) => {
    if (!editingId) return;
    await updateMutation.mutateAsync({ id: editingId, data });
    setEditingId(null);
  };

  const handleDelete = async (id: number) => {
    if (confirm('Delete this agent?')) {
      await deleteMutation.mutateAsync(id);
    }
  };

  if (isPending) return <div>Loading agents...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Agent Studio</h1>
        <Button onClick={() => setIsCreating(true)}>
          Create Agent
        </Button>
      </div>

      {isCreating && (
        <div className="mb-6 p-6 border rounded-lg">
          <h2 className="text-xl font-semibold mb-4">New Agent</h2>
          <AgentForm onSubmit={handleCreate} />
          <Button variant="outline" onClick={() => setIsCreating(false)}>
            Cancel
          </Button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {agents?.map((agent) => (
          editingId === agent.id ? (
            <div key={agent.id} className="p-6 border rounded-lg">
              <h2 className="text-xl font-semibold mb-4">Edit Agent</h2>
              <AgentForm
                defaultValues={agent}
                onSubmit={handleUpdate}
              />
              <Button variant="outline" onClick={() => setEditingId(null)}>
                Cancel
              </Button>
            </div>
          ) : (
            <AgentCard
              key={agent.id}
              agent={agent}
              onEdit={setEditingId}
              onDelete={handleDelete}
            />
          )
        ))}
      </div>
    </div>
  );
}
```

## Testing Examples

### Vitest Unit Test
```typescript
// src/components/AgentCard.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AgentCard } from './AgentCard';

const mockAgent = {
  id: 1,
  name: 'Test Agent',
  description: 'Test description',
  modelName: 'gpt-4',
  systemPrompt: 'You are helpful',
  createdAt: new Date().toISOString(),
};

describe('AgentCard', () => {
  it('renders agent information', () => {
    render(<AgentCard agent={mockAgent} />);
    
    expect(screen.getByText('Test Agent')).toBeInTheDocument();
    expect(screen.getByText('Test description')).toBeInTheDocument();
    expect(screen.getByText('gpt-4')).toBeInTheDocument();
  });

  it('calls onEdit when edit button clicked', async () => {
    const onEdit = vi.fn();
    const user = userEvent.setup();
    
    render(<AgentCard agent={mockAgent} onEdit={onEdit} />);
    await user.click(screen.getByRole('button', { name: /edit/i }));
    
    expect(onEdit).toHaveBeenCalledWith(1);
  });

  it('calls onDelete when delete button clicked', async () => {
    const onDelete = vi.fn();
    const user = userEvent.setup();
    
    render(<AgentCard agent={mockAgent} onDelete={onDelete} />);
    await user.click(screen.getByRole('button', { name: /delete/i }));
    
    expect(onDelete).toHaveBeenCalledWith(1);
  });
});
```

### Playwright E2E Test
```typescript
// e2e/agents.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Agent Management', () => {
  test('creates new agent', async ({ page }) => {
    await page.goto('/agents');
    
    await page.getByRole('button', { name: /create agent/i }).click();
    await page.getByLabel(/name/i).fill('E2E Test Agent');
    await page.getByLabel(/model/i).selectOption('gpt-4');
    await page.getByLabel(/system prompt/i).fill('You are a helpful assistant');
    await page.getByRole('button', { name: /save/i }).click();
    
    await expect(page.getByText('E2E Test Agent')).toBeVisible();
  });

  it('edits existing agent', async ({ page }) => {
    await page.goto('/agents');
    
    await page.getByRole('button', { name: /edit/i }).first().click();
    await page.getByLabel(/name/i).fill('Updated Agent');
    await page.getByRole('button', { name: /save/i }).click();
    
    await expect(page.getByText('Updated Agent')).toBeVisible();
  });

  it('deletes agent', async ({ page }) => {
    await page.goto('/agents');
    
    page.on('dialog', dialog => dialog.accept());
    await page.getByRole('button', { name: /delete/i }).first().click();
    
    // Verify agent is removed from list
  });
});
```

## Advanced Zod Validation Examples

```typescript
// src/schemas/agent.ts
import { z } from 'zod';

// Async validation
export const createAgentSchema = z.object({
  name: z
    .string()
    .min(3)
    .refine(
      async (name) => {
        const response = await api.get<{ available: boolean }>(
          `/agents/check-name?name=${encodeURIComponent(name)}`
        );
        return response.available;
      },
      { message: 'Name already taken' }
    ),
  email: z.string().email(),
  modelName: z.enum(['gpt-4', 'claude-3-opus']),
});

// Discriminated union
const emailNotification = z.object({
  type: z.literal('email'),
  email: z.string().email(),
  subject: z.string(),
});

const smsNotification = z.object({
  type: z.literal('sms'),
  phone: z.string().regex(/^\+?[1-9]\d{1,14}$/),
  message: z.string().max(160),
});

export const notificationSchema = z.discriminatedUnion('type', [
  emailNotification,
  smsNotification,
]);

// Array field validation
export const toolSchema = z.object({
  name: z.string(),
  parameters: z.array(z.object({
    name: z.string(),
    type: z.enum(['string', 'number', 'boolean']),
    required: z.boolean(),
  })).min(1),
});

// Usage with useFieldArray
function ToolConfigForm() {
  const form = useForm({
    resolver: zodResolver(toolSchema),
    defaultValues: {
      name: '',
      parameters: [{ name: '', type: 'string', required: false }],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: 'parameters',
  });

  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      {fields.map((field, index) => (
        <div key={field.id}>
          <input {...form.register(`parameters.${index}.name`)} />
          <select {...form.register(`parameters.${index}.type`)}>
            <option value="string">String</option>
            <option value="number">Number</option>
          </select>
          <button type="button" onClick={() => remove(index)}>Remove</button>
        </div>
      ))}
      <button type="button" onClick={() => append({ name: '', type: 'string', required: false })}>
        Add Parameter
      </button>
      <button type="submit">Save</button>
    </form>
  );
}
```

## Virtual Scrolling Example

```typescript
// src/components/AgentVirtualList.tsx
import { useVirtualizer } from '@tanstack/react-virtual';
import { useRef } from 'react';
import type { Agent } from '@/types/agent';

export function AgentVirtualList({ agents }: { agents: Agent[] }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: agents.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80,
    overscan: 5,
  });

  return (
    <div ref={parentRef} className="h-[600px] overflow-auto">
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => {
          const agent = agents[virtualItem.index];
          if (!agent) return null;

          return (
            <div
              key={virtualItem.key}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualItem.size}px`,
                transform: `translateY(${virtualItem.start}px)`,
              }}
            >
              <AgentCard agent={agent} />
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

## Framer Motion Animations

```typescript
// src/components/AnimatedCard.tsx
import { motion, AnimatePresence } from 'framer-motion';

export function AnimatedAgentCard({ agent }: { agent: Agent }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2 }}
      className="p-4 border rounded-lg"
    >
      <h3>{agent.name}</h3>
      <p>{agent.description}</p>
    </motion.div>
  );
}

// List animations
export function AnimatedAgentList({ agents }: { agents: Agent[] }) {
  return (
    <AnimatePresence>
      {agents.map((agent, index) => (
        <motion.div
          key={agent.id}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 20 }}
          transition={{ delay: index * 0.05 }}
        >
          <AgentCard agent={agent} />
        </motion.div>
      ))}
    </AnimatePresence>
  );
}
```

## Docker Multi-Stage Build

```dockerfile
# Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json pnpm-lock.yaml ./
RUN corepack enable pnpm && pnpm install --frozen-lockfile

COPY . .
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN pnpm build

# Production stage
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

```nginx
# nginx.conf
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|svg|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Environment Variables

```bash
# .env.example
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
VITE_ENABLE_DEVTOOLS=true
VITE_ENV=development
```

```typescript
// src/config/env.ts
import { z } from 'zod';

const envSchema = z.object({
  VITE_API_URL: z.string().url(),
  VITE_WS_URL: z.string().startsWith('ws'),
  VITE_ENABLE_DEVTOOLS: z.string().transform(val => val === 'true'),
  VITE_ENV: z.enum(['development', 'staging', 'production']),
});

export const env = envSchema.parse(import.meta.env);
```

## Accessibility Example

```typescript
// src/components/AccessibleModal.tsx
export function Modal({ isOpen, onClose, title, children }: ModalProps) {
  const titleId = useId();

  useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
      className="fixed inset-0 z-50"
    >
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      
      <div className="fixed inset-0 overflow-y-auto">
        <div className="flex min-h-full items-center justify-center p-4">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h2 id={titleId} className="text-xl font-semibold mb-4">
              {title}
            </h2>
            
            {children}
            
            <button
              onClick={onClose}
              className="mt-4 px-4 py-2 bg-gray-200 rounded"
              aria-label="Close dialog"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
```
