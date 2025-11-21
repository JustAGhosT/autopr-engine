# AutoPR Desktop

A cross-platform desktop application for AutoPR Engine built with Tauri, React, and TypeScript.

## Overview

AutoPR Desktop provides a user-friendly interface for managing and monitoring AutoPR workflows, configurations, and platform analytics. The application combines a modern React frontend with a lightweight Rust backend, leveraging Tauri for native desktop capabilities.

### Features

- **Dashboard**: Real-time workflow status and platform detection overview
- **Configuration Management**: Visual editor for AutoPR settings and workflows
- **Platform Analytics**: Detailed insights into detected platforms and compatibility
- **Live Logs**: Real-time log streaming via WebSocket connection
- **Python Sidecar**: Embedded Python runtime for AutoPR Engine integration

## Architecture

```
autopr-desktop/
├── src/                    # React frontend (TypeScript)
│   ├── pages/             # Application pages
│   │   ├── Dashboard.tsx
│   │   ├── Configuration.tsx
│   │   ├── PlatformAnalytics.tsx
│   │   └── Logs.tsx
│   ├── components/        # Reusable UI components
│   └── App.tsx            # Main application component
├── src-tauri/             # Rust backend
│   ├── src/
│   │   ├── main.rs       # Tauri application entry point
│   │   └── lib.rs        # Core library functions
│   └── tauri.conf.json   # Tauri configuration
└── sidecar/               # Python sidecar process
    ├── main.py           # Sidecar entry point
    ├── websocket_handler.py
    └── requirements.txt
```

## Prerequisites

### Required

1. **Node.js** (v20 or higher)
   - Download: https://nodejs.org/
   - Verify: `node --version`

2. **Rust** (latest stable)
   - Install: https://rustup.rs/
   - Verify: `rustc --version`

3. **Python** (3.8 or higher)
   - Download: https://python.org/
   - Verify: `python --version`

### Platform-Specific Requirements

#### Windows
- Microsoft C++ Build Tools
- WebView2 (usually pre-installed on Windows 11)

#### macOS
- Xcode Command Line Tools: `xcode-select --install`

#### Linux
- Dependencies vary by distribution. See: https://tauri.app/start/prerequisites/#linux

## Getting Started

### Installation

1. **Navigate to the desktop app directory:**
   ```bash
   cd autopr-desktop
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Install Python dependencies for the sidecar:**
   ```bash
   pip install -r sidecar/requirements.txt
   ```

### Development

**Start the development server:**
```bash
npm run tauri dev
```

This command will:
1. Start the Vite dev server (React frontend) at http://localhost:1420
2. Compile the Rust backend
3. Launch the Python sidecar process
4. Open the desktop application window

The application supports hot module replacement (HMR) - changes to frontend code will update instantly.

**Frontend-only development:**
```bash
npm run dev
```
This runs only the Vite dev server without launching Tauri, useful for rapid UI development.

### Building for Production

**Build the application:**
```bash
npm run build
```

**Create distributable packages:**
```bash
npm run tauri build
```

This generates platform-specific installers in `src-tauri/target/release/bundle/`:
- **Windows**: `.msi` installer
- **macOS**: `.dmg` disk image and `.app` bundle
- **Linux**: `.deb`, `.AppImage`, or `.rpm` (depending on your system)

## Technology Stack

### Frontend
- **React 19**: UI framework
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool and dev server
- **Tailwind CSS 4**: Utility-first CSS framework
- **shadcn/ui**: Accessible component library
- **React Router**: Client-side routing
- **React JSON Schema Form**: Dynamic form generation

### Backend
- **Tauri 2**: Native desktop framework
- **Rust**: System programming language
- **Python Sidecar**: Embedded Python runtime for AutoPR Engine

### Key Dependencies
- `@tauri-apps/api`: JavaScript API for Tauri backend
- `@rjsf/core`: JSON Schema Form library
- `lucide-react`: Icon library
- `reqwest`: Rust HTTP client

## Project Structure

### Frontend Pages

- **Dashboard** (`src/pages/Dashboard.tsx`)
  - Workflow overview
  - Quick actions
  - System status

- **Configuration** (`src/pages/Configuration.tsx`)
  - JSON Schema-based form for AutoPR settings
  - Workflow builder
  - Environment configuration

- **Platform Analytics** (`src/pages/PlatformAnalytics.tsx`)
  - Detected platforms visualization
  - Compatibility reports
  - Migration opportunities

- **Logs** (`src/pages/Logs.tsx`)
  - Real-time log streaming
  - Log filtering and search
  - Export capabilities

### Backend Components

- **Rust Backend** (`src-tauri/src/`)
  - Native system integration
  - File system operations
  - Process management
  - IPC (Inter-Process Communication)

- **Python Sidecar** (`sidecar/`)
  - AutoPR Engine integration
  - WebSocket server for live updates
  - Background task execution

## Configuration

### Tauri Configuration

Edit `src-tauri/tauri.conf.json` to customize:
- Application metadata (name, version, identifier)
- Window properties (size, title)
- Build commands
- Bundle settings
- Security policies

### Vite Configuration

Edit `vite.config.ts` for:
- Build optimizations
- Plugin configuration
- Path aliases
- Development server settings

## Development Tips

### Debugging

**Frontend debugging:**
- Open DevTools: `Ctrl+Shift+I` (Windows/Linux) or `Cmd+Option+I` (macOS)
- Console logs appear in the browser DevTools

**Rust backend debugging:**
- Logs appear in the terminal running `npm run tauri dev`
- Use `println!()` or `dbg!()` macros
- Enable Rust backtrace: `RUST_BACKTRACE=1 npm run tauri dev`

**Python sidecar debugging:**
- Check `sidecar/main.py` for log output
- Logs are captured in the Logs page

### Hot Reload

- **Frontend**: Automatic HMR via Vite
- **Rust**: Application restarts automatically on code changes
- **Python sidecar**: Requires manual restart

## Troubleshooting

### Build Errors

**"Rust compiler not found"**
- Ensure Rust is installed: `rustc --version`
- Restart your terminal/IDE after installing Rust

**"npm dependencies error"**
- Clear cache: `npm cache clean --force`
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`

**"Python sidecar fails to start"**
- Verify Python version: `python --version` (must be 3.8+)
- Install sidecar dependencies: `pip install -r sidecar/requirements.txt`

### Runtime Issues

**"Application won't start"**
- Check for port conflicts (default: 1420)
- Verify all prerequisites are installed
- Check console logs for error messages

**"WebSocket connection failed"**
- Ensure Python sidecar is running
- Check firewall settings
- Verify WebSocket port configuration

## Contributing

See the main AutoPR Engine repository for contribution guidelines.

## Recommended IDE Setup

- [VS Code](https://code.visualstudio.com/) with extensions:
  - [Tauri](https://marketplace.visualstudio.com/items?itemName=tauri-apps.tauri-vscode)
  - [rust-analyzer](https://marketplace.visualstudio.com/items?itemName=rust-lang.rust-analyzer)
  - [ESLint](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint)
  - [Tailwind CSS IntelliSense](https://marketplace.visualstudio.com/items?itemName=bradlc.vscode-tailwindcss)

## Resources

- [Tauri Documentation](https://tauri.app/)
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [TypeScript Documentation](https://www.typescriptlang.org/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)

## License

See the main AutoPR Engine repository for license information.
