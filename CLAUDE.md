# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claire ("Making Calculus Clear") is an AI-powered calculus teaching assistant that combines natural language processing with SymPy symbolic mathematics. It provides step-by-step problem-solving, concept explanations, and interactive tutoring through a CLI interface.

## Commands

### Running the Application
```bash
# Activate virtual environment first
source venv/bin/activate

# Run Web UI (recommended)
streamlit run app.py

# Or run CLI
python3 main.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Configuration
Edit `.env` file to configure:
- `OPENAI_API_KEY` - Required for AI-powered explanations
- `DEFAULT_LEVEL` - `beginner`, `intermediate`, or `advanced`

## Architecture

```
User Input → main.py (CLI) → ClaireAgent.process_query()
                                    ↓
                            Query Type Classification
                            (math_calculation, concept_explanation,
                             problem_solving, teaching_request)
                                    ↓
                    ┌───────────────┴───────────────┐
                    ↓                               ↓
            Math Calculations               Concepts/Teaching
            SymPyBackupEngine               OpenAI GPT-3.5-turbo
                                            (KnowledgeLoader fallback)
```

### Core Files

- **app.py** - Streamlit web UI (recommended)
- **main.py** - CLI entry point (alternative)
- **claire_agent.py** - Core AI agent, query routing, session management, OpenAI integration
- **sympy_backup.py** - Symbolic math engine using SymPy
- **knowledge_loader.py** - Embedded knowledge base for calculus concepts and examples

### Query Type Detection

The agent classifies queries by keywords:
- **math_calculation**: calculate, solve, evaluate, derivative, integral, limit, math operators
- **concept_explanation**: what is, explain, define, how does, why
- **teaching_request**: teach me, show me, step by step, walk through
- **problem_solving**: problem, exercise, question, solve this

### Math Engine Pattern Matching

`_convert_to_sympy()` converts natural language to SymPy syntax:
- "derivative of x^2" → `diff(x**2, x)`
- "integral of sin(x)" → `integrate(sin(x), x)`
- "limit of sin(x)/x as x->0" → `limit(sin(x)/x, x, 0)`

## Key Implementation Details

- Session history maintained for last 10 messages in `ClaireAgent.conversation_history`
- Math engine returns structured dicts with `success`, `result`, `latex`, `engine` keys
- KnowledgeLoader provides fallback when OpenAI API unavailable
- System commands: `help`, `examples`, `capabilities`, `status`, `level`, `clear`, `reset`, `/study`
- **Guided Learning Mode** (`/study`): When enabled, math questions trigger Socratic-style prompts instead of direct answers. Uses `_handle_guided_learning()` method.
