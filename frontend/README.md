# DeepAgents Control Platform - Frontend

Enterprise administrative platform frontend for creating, configuring, and managing AI agents based on the deepagents framework.

## Tech Stack

- **Framework:** React 19.2 with TypeScript 5.9.3 (strict mode)
- **State Management:** TanStack Query V5 for server state
- **Routing:** React Router v7
- **Forms:** React Hook Form + Zod validation
- **Styling:** Tailwind CSS (responsive, mobile-first)
- **UI Components:** Headless UI, Monaco Editor, Recharts
- **WebSocket:** socket.io-client for real-time streaming
- **Testing:** React Testing Library, Jest
- **Visual Regression:** Storybook 8.6 + Chromatic

## Getting Started

### Prerequisites

- Node.js 18+
- npm 9+

### Installation

```bash
npm install
```

### Development

Start the development server:

```bash
npm start
```

Open http://localhost:3000 to view the app.

### Building

Create a production build:

```bash
npm run build
```

### Testing

Run unit and integration tests:

```bash
npm test
```

Run tests once (CI mode):

```bash
npm test -- --watchAll=false
```

Run tests with coverage:

```bash
npm test -- --coverage --watchAll=false
```

## Storybook

### Running Storybook

Start Storybook development server:

```bash
npm run storybook
```

Open http://localhost:6006 to view component stories.

### Building Storybook

Build static Storybook:

```bash
npm run build-storybook
```

### Visual Regression Testing

Run Chromatic visual regression tests:

```bash
npm run chromatic
```

See [VISUAL_REGRESSION_TESTING.md](./VISUAL_REGRESSION_TESTING.md) for complete documentation.

## Project Structure

```
frontend/
├── .storybook/          # Storybook configuration
├── public/              # Static assets
├── src/
│   ├── api/            # API client (axios with JWT)
│   ├── components/     # React components
│   │   ├── agents/    # Agent-related components
│   │   ├── analytics/ # Analytics components
│   │   ├── common/    # Reusable UI components
│   │   ├── dashboard/ # Dashboard components
│   │   ├── executions/# Execution monitor components
│   │   ├── externalTools/ # External tools components
│   │   ├── templates/ # Template library components
│   │   └── tools/     # Custom tools components
│   ├── contexts/       # React contexts
│   ├── hooks/          # Custom React hooks
│   ├── pages/          # Page components
│   ├── types/          # TypeScript type definitions
│   ├── utils/          # Utility functions
│   └── index.tsx       # App entry point
├── package.json
└── tsconfig.json
```

## Key Features

### Pages

- `/login`, `/register` - Authentication
- `/dashboard` - Metrics, graphs, statistics
- `/agents` - Agent Studio (create/edit agents)
- `/executions` - Execution Monitor (live streaming)
- `/templates` - Template Library (8 pre-configured)
- `/analytics` - Detailed analytics
- `/tools` - Custom Tool Marketplace
- `/external-tools` - External Tools Integration

### Component Library

16+ fully documented components with Storybook stories:

- **Agents:** AgentCard
- **Dashboard:** MetricCard, AgentHealthCard, TokenUsageChart, ExecutionStatsChart
- **Templates:** TemplateCard
- **Executions:** TraceItem, PlanViewer
- **Tools:** ToolCard
- **Common:** Button, Card, Input, Select, Textarea, Modal, LoadingSpinner

### State Management

- **TanStack Query:** Server state, API calls, caching
- **Local State:** Component-level state with useState
- **Context:** Shared state without prop drilling

### API Integration

- JWT authentication with automatic token refresh
- Axios interceptors for error handling
- WebSocket streaming for real-time execution traces
- Type-safe API client with TypeScript

## Environment Variables

Create a `.env.local` file:

```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
```

## Code Style

### TypeScript

- Strict mode enabled
- Explicit types for all props, state, and functions
- No `any` types
- Interfaces for component props

### React Patterns

- Functional components with hooks
- Custom hooks for reusable logic
- Proper error boundaries
- Loading and error states for all async operations

### Styling

- Tailwind CSS utility classes
- Mobile-first responsive design
- Consistent spacing and colors
- Accessible components (ARIA labels, semantic HTML)

## Testing Strategy

### Unit Tests

- Component behavior and rendering
- Custom hooks logic
- Utility functions
- Form validation

### Integration Tests

- User flows (login, create agent, execute)
- API integration
- WebSocket streaming
- Error handling

### Visual Regression Tests

- Storybook stories for all major components
- Chromatic for automated visual testing
- Approved baselines for UI changes

**Current Status:** 388/417 tests passing (93% coverage)

See [TESTING_REPORT.md](./TESTING_REPORT.md) for detailed test results.

## Performance

- Code splitting with React.lazy
- Memoization with React.memo, useCallback, useMemo
- Virtual scrolling for large lists
- Optimized bundle size (~500KB gzipped)

## Accessibility

- WCAG 2.1 Level AA compliant
- Keyboard navigation support
- Screen reader friendly
- ARIA labels and roles
- Focus management

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Deployment

### Docker Production Build

```bash
docker build -f Dockerfile.prod -t deepagents-frontend .
docker run -p 3000:80 deepagents-frontend
```

### Nginx Configuration

See [nginx.conf](./nginx.conf) for production configuration.

## Documentation

- [Visual Regression Testing Guide](./VISUAL_REGRESSION_TESTING.md)
- [Testing Report](./TESTING_REPORT.md)
- [API Documentation](http://localhost:8000/docs) (when backend is running)

## Contributing

1. Create a feature branch
2. Make changes
3. Add tests
4. Create Storybook stories for UI components
5. Run tests and visual regression tests
6. Create pull request
7. Review Chromatic changes
8. Merge after approval

## Troubleshooting

### Common Issues

**"Cannot connect to backend"**
- Ensure backend is running on port 8000
- Check REACT_APP_API_URL in .env.local
- Verify CORS is enabled in backend

**"Storybook won't start"**
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Check for TypeScript errors in stories
- Verify .storybook configuration

**"Visual regression tests failing"**
- Review changes in Chromatic dashboard
- Accept intentional changes
- Fix unintended regressions

## License

Proprietary - DeepAgents Control Platform

## Support

For questions or issues:
- Check documentation first
- Review existing GitHub issues
- Open a new issue with detailed description
- Contact the frontend team

---

**Version:** 1.0.0
**Last Updated:** November 10, 2025
