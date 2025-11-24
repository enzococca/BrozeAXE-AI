# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository, and includes troubleshooting steps for installing and running the Claude Code CLI locally with this project.

## Project Overview

This is a Flask web application in early development stage. The project currently consists of a minimal Flask setup with a single "Hello World" route.

## Commands

### Running the Application
```bash
# Activate virtual environment (if not already activated)
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Run the Flask development server
python app.py
```

The application will start on http://127.0.0.1:5000/

### Dependencies
Currently, there is no `requirements.txt` file. When creating one, ensure Flask is included:
```bash
pip freeze > requirements.txt
```

## Architecture

### Project Structure
- `app.py` - Main Flask application entry point containing route definitions
- `static/` - Directory for static assets (CSS, JavaScript, images)
- `templates/` - Directory for Jinja2 HTML templates
- `.venv/` - Python virtual environment (do not modify)

### Current Implementation
The application currently has:
- Single route handler at `/` returning "Hello World!"
- Flask development server configuration with debug mode enabled
- Standard Flask project directory structure (though static/ and templates/ are unused)

### Development Patterns
When extending this application:
1. Add new routes directly in `app.py` or create blueprint modules for larger applications
2. Place HTML templates in `templates/` directory
3. Place CSS, JavaScript, and images in `static/` directory
4. Use Flask's built-in Jinja2 templating for dynamic content
5. Consider adding configuration management for different environments

## Important Notes
- The application uses Flask's built-in development server (not suitable for production)
- Debug mode is currently enabled (app.run(debug=True))
- No database or ORM is configured yet
- No testing framework is set up
- No linting or code formatting tools are configured

---

## Using Claude Code CLI in this repo (no global install required)

If you see errors like:

```
zsh: command not found: claude
```

you probably don’t have a global CLI named `claude` in your PATH. The recommended way to run Claude Code with this repo is via `npx`, without any global installs or `sudo`.

### Quick start (recommended)

Run Claude Code in this project directory:

```
npx -y @anthropic-ai/claude-code
```

Alternative entry points if you want specific modes:

```
# Chat-oriented session in the current repo
npx -y @anthropic-ai/claude-code chat

# Code-oriented session (repo-aware)
npx -y @anthropic-ai/claude-code code
```

This uses a temporary local executable and does not require a global `claude` binary.

### Optional: npm scripts (if you want shorthand commands)

You can add these scripts to `package.json` to get nice aliases:

```json
{
  "scripts": {
    "claude": "npx -y @anthropic-ai/claude-code",
    "claude:chat": "npx -y @anthropic-ai/claude-code chat",
    "claude:code": "npx -y @anthropic-ai/claude-code code"
  }
}
```

Then run:

```
npm run claude
# or
npm run claude:chat
npm run claude:code
```

---

## Fixing EACCES and permissions errors on macOS

If you see errors like these when installing packages:

```
npm ERR! code EACCES
npm ERR! syscall mkdir or rename
npm ERR! Error: EACCES: permission denied, ...
```

This is almost always a permissions/ownership issue caused by using `sudo` with Node/npm or a global Node installation that writes to a root-owned directory.

### Do NOT use `sudo npm install`

Using `sudo` creates root-owned files inside your project or global directories which later break local installs. Prefer user-space installs and `npx`.

### Fix ownership of your project’s node_modules

From the project root:

```
sudo chown -R "$USER":staff node_modules package-lock.json || true
```

If `node_modules` doesn’t exist yet, you can skip this. The command makes sure your user owns these paths.

### Fix ownership of your global npm cache (optional)

```
sudo chown -R "$USER":staff ~/.npm
```

### Re-install locally without sudo

```
npm install
npx -y @anthropic-ai/claude-code
```

### If you must use a global `claude` command

Installing globally is not required, but if you want a global command, ensure your global npm prefix is in your PATH and avoid sudo:

```
npm config set prefix "$HOME/.npm-global"
echo 'export PATH="$HOME/.npm-global/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

npm i -g @anthropic-ai/claude-code
claude
```

If you previously installed globally with `sudo`, uninstall with `sudo` once, then reinstall without `sudo` as above:

```
sudo npm uninstall -g @anthropic-ai/claude-code
npm i -g @anthropic-ai/claude-code
```

---

## FAQ

- Q: I installed `@anthropic-ai/claude-code`, but `claude` is still not found.
  - A: Either the package wasn’t installed globally in a PATH-visible prefix, or your PATH isn’t configured. Use `npx -y @anthropic-ai/claude-code` in the project directory, or configure a user-space global prefix as shown above.

- Q: Local `npm install` fails with EACCES in `node_modules`.
  - A: Your `node_modules` or cache is probably owned by root due to a previous `sudo` install. Fix ownership via `chown` (see above) and retry without `sudo`.

- Q: Do I need `claude` to run this Flask app?
  - A: No. The Flask app runs independently. Claude Code CLI is optional, helpful for AI-assisted coding or repo exploration.