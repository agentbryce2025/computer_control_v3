# Local Setup Guide

This guide explains how to set up the terminal interface for Claude computer control on your local machine.

## Prerequisites

1. Python 3.11 or higher
2. pip (Python package manager)
3. An Anthropic API key from [console.anthropic.com](https://console.anthropic.com)
4. Git

## Basic Setup

1. Clone the repository:
```bash
git clone https://github.com/agentbryce2025/computer_control_v3.git
cd computer_control_v3
```

2. Create and activate a virtual environment:
```bash
# On Linux/macOS
python -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

3. Install the package in development mode:
```bash
pip install -e .
```

4. Set up your API key:
```bash
# On Linux/macOS
export ANTHROPIC_API_KEY=your_api_key_here

# On Windows (Command Prompt)
set ANTHROPIC_API_KEY=your_api_key_here

# On Windows (PowerShell)
$env:ANTHROPIC_API_KEY="your_api_key_here"
```

## Running the Terminal Interface

There are two ways to run the terminal interface:

1. Using the run script:
```bash
./run_terminal.sh
```

2. Using the Python module directly:
```bash
python -m computer_use_demo.terminal
```

### Command Line Options

The terminal interface supports several options:

```bash
python -m computer_use_demo.terminal [OPTIONS]

Options:
  --api-key TEXT     Anthropic API key (can also use ANTHROPIC_API_KEY env var)
  --provider TEXT    API provider: anthropic, bedrock, or vertex (default: anthropic)
  --model TEXT      Model to use (defaults to provider's default)
  --hide-images     Don't notify about screenshots
```

## Usage

1. Start typing commands and interact with Claude
2. Special commands:
   - Type `exit` or press Ctrl+C to quit
   - Type `clear` to clear the conversation history

## Troubleshooting

1. If you see "Permission denied" when running run_terminal.sh:
```bash
chmod +x run_terminal.sh
chmod +x computer_use_demo/terminal.py
```

2. If you get module not found errors:
```bash
pip install -e .
```

3. If you get API key errors, make sure your API key is set:
```bash
echo $ANTHROPIC_API_KEY  # Should show your key
```