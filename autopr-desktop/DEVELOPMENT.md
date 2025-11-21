# AutoPR Desktop - Development Guide

This guide provides detailed information for developers working on the AutoPR Desktop application.

## Table of Contents

- [Environment Setup](#environment-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Performance](#performance)
- [Security](#security)

## Environment Setup

### Initial Setup

1. **Clone the repository and navigate to the desktop app:**
   ```bash
   cd autopr-desktop
   ```

2. **Install all dependencies:**
   ```bash
   # Node.js dependencies
   npm install

   # Python sidecar dependencies
   pip install -r sidecar/requirements.txt

   # Verify Rust installation
   rustc --version
   cargo --version
   ```

3. **Set up environment variables (optional):**
   Create a `.env` file in the `autopr-desktop` directory:
   ```env
   VITE_WEBSOCKET_URL=ws://localhost:8765
   VITE_API_BASE_URL=http://localhost:8000
   ```

### IDE Configuration

#### VS Code

Install recommended extensions:
```json
{
  "recommendations": [
    "tauri-apps.tauri-vscode",
    "rust-lang.rust-analyzer",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "formulahendry.auto-rename-tag"
  ]
}
```

Add to `.vscode/settings.json`:
```json
{
  "rust-analyzer.linkedProjects": ["src-tauri/Cargo.toml"],
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "[rust]": {
    "editor.defaultFormatter": "rust-lang.rust-analyzer"
  }
}
```

## Project Structure

### Frontend (`src/`)

```
src/
├── App.tsx                 # Root component with routing
├── main.tsx                # Application entry point
├── pages/                  # Page components
│   ├── Dashboard.tsx       # Main dashboard view
│   ├── Configuration.tsx   # Settings and config editor
│   ├── PlatformAnalytics.tsx  # Platform detection results
│   └── Logs.tsx            # Real-time log viewer
├── components/             # Reusable UI components
│   └── ui/                 # shadcn/ui components
│       ├── button.tsx
│       ├── card.tsx
│       └── badge.tsx
├── assets/                 # Static assets
└── schema.json            # JSON schema for configuration
```

### Backend (`src-tauri/`)

```
src-tauri/
├── src/
│   ├── main.rs            # Tauri app initialization
│   └── lib.rs             # Core library with IPC handlers
├── tauri.conf.json        # Tauri configuration
├── Cargo.toml             # Rust dependencies
└── capabilities/          # Tauri permissions
    └── default.json
```

### Python Sidecar (`sidecar/`)

```
sidecar/
├── main.py                # Sidecar entry point
├── websocket_handler.py   # WebSocket server for live updates
├── generate_schema.py     # Schema generation utility
└── requirements.txt       # Python dependencies
```

## Development Workflow

### Starting Development Server

```bash
# Full stack development (recommended)
npm run tauri dev

# Frontend only (for UI work)
npm run dev
```

### Making Changes

1. **Frontend Changes (React/TypeScript)**
   - Edit files in `src/`
   - Changes auto-reload via HMR
   - Check browser DevTools for errors

2. **Backend Changes (Rust)**
   - Edit files in `src-tauri/src/`
   - Application restarts automatically
   - Check terminal for compilation errors

3. **Sidecar Changes (Python)**
   - Edit files in `sidecar/`
   - Requires manual restart of `npm run tauri dev`

### Code Style

**TypeScript/React:**
- Use functional components with hooks
- Follow React best practices
- Use TypeScript strict mode
- Format with Prettier

**Rust:**
- Follow Rust style guidelines (rustfmt)
- Use clippy for linting: `cargo clippy`
- Write idiomatic Rust code

**Python:**
- Follow PEP 8 style guide
- Use type hints
- Format with Black (if available)

## Architecture

### Communication Flow

```
┌─────────────────┐
│  React Frontend │
│   (TypeScript)  │
└────────┬────────┘
         │ IPC
         ├──────────┐
         │          │
    ┌────▼────┐  ┌─▼─────────┐
    │  Tauri  │  │ WebSocket │
    │  (Rust) │  │  (Python) │
    └────┬────┘  └─┬─────────┘
         │         │
         └─────┬───┘
               │
         ┌─────▼──────┐
         │   AutoPR   │
         │   Engine   │
         └────────────┘
```

### IPC (Inter-Process Communication)

The Rust backend exposes commands that can be called from the frontend:

**Defining a command (Rust):**
```rust
#[tauri::command]
fn my_custom_command(arg: String) -> Result<String, String> {
    // Implementation
    Ok(format!("Processed: {}", arg))
}
```

**Calling from frontend (TypeScript):**
```typescript
import { invoke } from '@tauri-apps/api/core';

const result = await invoke<string>('my_custom_command', { 
  arg: 'test' 
});
```

### State Management

The application uses React hooks for state management:

```typescript
// Local state
const [data, setData] = useState<Data>([]);

// Effect for side effects
useEffect(() => {
  // Load data
  invoke('get_data').then(setData);
}, []);
```

### WebSocket Integration

The Python sidecar provides real-time updates via WebSocket:

**Server (Python):**
```python
# sidecar/websocket_handler.py
async def handle_client(websocket):
    await websocket.send(json.dumps({
        'type': 'log',
        'data': 'Log message'
    }))
```

**Client (TypeScript):**
```typescript
const ws = new WebSocket('ws://localhost:8765');
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  // Handle message
};
```

## API Reference

### Tauri Commands

Commands exposed by the Rust backend:

```rust
// Example commands (add actual commands here)
#[tauri::command]
fn get_config() -> Result<Config, String>

#[tauri::command]
fn save_config(config: Config) -> Result<(), String>

#[tauri::command]
fn run_detection(path: String) -> Result<DetectionResult, String>
```

### WebSocket Messages

Message types from Python sidecar:

```typescript
type WebSocketMessage = 
  | { type: 'log', level: string, message: string }
  | { type: 'status', status: string }
  | { type: 'progress', current: number, total: number }
  | { type: 'result', data: any };
```

## Testing

### Frontend Testing

```bash
# Run tests (if configured)
npm test

# Type checking
npm run build  # TypeScript will error if types are wrong
```

### Rust Testing

```bash
cd src-tauri

# Run unit tests
cargo test

# Run with output
cargo test -- --nocapture

# Test specific module
cargo test module_name
```

### Python Testing

```bash
cd sidecar

# Run tests (if configured)
pytest

# With coverage
pytest --cov=.
```

### Manual Testing

1. **Build and test the app:**
   ```bash
   npm run tauri build
   ```

2. **Test the installer:**
   - Navigate to `src-tauri/target/release/bundle/`
   - Install and run the application
   - Verify all features work

## Performance

### Frontend Optimization

- Use `React.memo()` for expensive components
- Implement virtualization for long lists
- Lazy load routes:
  ```typescript
  const Dashboard = lazy(() => import('./pages/Dashboard'));
  ```

### Backend Optimization

- Use async Rust where appropriate
- Implement connection pooling
- Cache expensive computations

### Build Optimization

```bash
# Optimize Rust binary
cargo build --release

# Optimize frontend bundle
npm run build -- --minify
```

## Security

### Tauri Security

1. **Content Security Policy (CSP)**
   - Configured in `tauri.conf.json`
   - Restrict external resources

2. **Capability System**
   - Define permissions in `capabilities/default.json`
   - Principle of least privilege

3. **IPC Security**
   - Validate all inputs from frontend
   - Use type-safe communication

### Best Practices

- Never expose sensitive data in IPC commands
- Sanitize user inputs
- Use HTTPS for external APIs
- Keep dependencies updated:
  ```bash
  npm audit
  cargo audit
  ```

## Debugging

### Frontend Debugging

1. **Browser DevTools**
   - Open: `Ctrl+Shift+I` (Windows/Linux) or `Cmd+Option+I` (macOS)
   - Use React DevTools extension

2. **Console Logging**
   ```typescript
   console.log('Debug info:', data);
   ```

### Rust Debugging

1. **Print Debugging**
   ```rust
   println!("Debug: {:?}", value);
   dbg!(&value);
   ```

2. **Enable Backtrace**
   ```bash
   RUST_BACKTRACE=1 npm run tauri dev
   ```

3. **Use VS Code Debugger**
   - Configure `launch.json` for Rust debugging
   - Set breakpoints in VS Code

### Python Debugging

1. **Print Debugging**
   ```python
   print(f"Debug: {value}")
   ```

2. **Logging**
   ```python
   import logging
   logging.debug("Debug message")
   ```

## Common Tasks

### Adding a New Page

1. Create component in `src/pages/NewPage.tsx`
2. Add route in `src/App.tsx`:
   ```typescript
   <Route path="/new-page" element={<NewPage />} />
   ```
3. Add navigation link

### Adding a Tauri Command

1. Add function in `src-tauri/src/lib.rs`:
   ```rust
   #[tauri::command]
   fn my_command() -> Result<String, String> {
       Ok("Success".to_string())
   }
   ```

2. Register in `src-tauri/src/main.rs`:
   ```rust
   .invoke_handler(tauri::generate_handler![my_command])
   ```

3. Call from frontend:
   ```typescript
   import { invoke } from '@tauri-apps/api/core';
   const result = await invoke('my_command');
   ```

### Updating Dependencies

```bash
# Node.js dependencies
npm update

# Check for outdated packages
npm outdated

# Rust dependencies
cd src-tauri
cargo update

# Python dependencies
pip install --upgrade -r sidecar/requirements.txt
```

## Resources

- [Tauri Documentation](https://tauri.app/)
- [Tauri API Reference](https://tauri.app/reference/javascript/api/)
- [React Documentation](https://react.dev/)
- [Rust Book](https://doc.rust-lang.org/book/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
