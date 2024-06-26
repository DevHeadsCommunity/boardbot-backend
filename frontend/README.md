# Test App

## Repository Structure

```
.
├── README.md
├── bun.lockb
├── index.html
├── package.json
├── postcss.config.js
├── public
│   └── logo.png
├── src
│   ├── App.tsx
│   ├── assets
│   ├── context
│   │   └── webSocketContext.tsx
│   ├── hooks
│   │   ├── useConsumer.ts
│   │   ├── usePublisher.ts
│   │   └── useWebSocket.ts
│   ├── index.css
│   ├── main.tsx
│   └── vite-env.d.ts
├── tailwind.config.js
├── tsconfig.json
├── tsconfig.node.json
└── vite.config.ts

6 directories, 18 files
```

## Getting Started

### Project Setup

1. Extract the repo
2. Navigate to the project directory:
   ```sh
   cd test-app
   ```
3. Install the required packages:
   ```sh
   bun install
   ```
4. Run the project:
   ```sh
   bun run dev
   ```
