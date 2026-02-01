# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Calctoa is an AI-powered calculus teaching assistant that combines natural language processing with symbolic mathematics engines. It provides step-by-step problem-solving, concept explanations, and interactive tutoring through a CLI interface.

## Commands

### Running the Application
```bash
# Activate virtual environment first
source venv/bin/activate

# Run the CLI
python3 main.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt

# For full Mathics support (Wolfram-compatible engine)
pip install mathics
```

### Configuration
Edit `.env` file to configure:
- `OPENAI_API_KEY` - Required for AI-powered explanations
- `DEFAULT_ENGINE` - `mathics` (default) or `sympy`
- `DEFAULT_LEVEL` - `beginner`, `intermediate`, or `advanced`
- `LOG_LEVEL` - Logging verbosity

## Architecture

```
User Input → main.py (CLI) → CalctoaAgent.process_query()
                                    ↓
                            Query Type Classification
                            (math_calculation, concept_explanation,
                             problem_solving, teaching_request)
                                    ↓
                    ┌───────────────┴───────────────┐
                    ↓                               ↓
            Math Calculations               Concepts/Teaching
            MathicsEngine                   OpenAI GPT-3.5-turbo
                 ↓ (fallback)               (KnowledgeLoader fallback)
            SymPyBackupEngine
```

### Core Files

- **main.py** - CLI entry point, interactive loop, user interface
- **calctoa_agent.py** - Core AI agent, query routing, session management, OpenAI integration
- **mathics_engine.py** - Wolfram syntax engine, natural language → Mathics conversion
- **sympy_backup.py** - Fallback symbolic math engine using SymPy
- **knowledge_loader.py** - Embedded knowledge base for calculus concepts and examples

### Query Type Detection

The agent classifies queries by keywords:
- **math_calculation**: calculate, solve, evaluate, derivative, integral, limit, math operators
- **concept_explanation**: what is, explain, define, how does, why
- **teaching_request**: teach me, show me, step by step, walk through
- **problem_solving**: problem, exercise, question, solve this

### Math Engine Pattern Matching

MathicsEngine converts natural language to Wolfram syntax:
- "derivative of x²" → `D[x^2, x]`
- "integral of sin(x)" → `Integrate[Sin[x], x]`
- "limit of sin(x)/x as x→0" → `Limit[Sin[x]/x, x -> 0]`

## Key Implementation Details

- Session history maintained for last 10 messages in `CalctoaAgent._conversation_history`
- Math engines return structured dicts with `success`, `result`, `latex`, `steps` keys
- KnowledgeLoader provides fallback when OpenAI API unavailable
- System commands: `help`, `examples`, `capabilities`, `status`, `level`, `engine`, `clear`, `reset`
