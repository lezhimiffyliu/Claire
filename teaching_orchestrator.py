"""
Teaching Orchestrator - Mode-aware agent orchestration with rule enforcement

This module prevents the agent from "free-wheeling" by:
1. Injecting explicit mode and known facts into prompts
2. Requiring structured action output from agent
3. Enforcing hard rules based on verifier results

Core principle: If verifier says CORRECT → must acknowledge and stop.
No Socratic追问 when the student has already solved it correctly.
"""

import json
import logging
from typing import Optional

from session_state import (
    TeachingMode, AgentAction, TeachingDecision, TeachingContext
)
from grader import GradingResult

logger = logging.getLogger(__name__)


def build_mode_aware_prompt(
    context: TeachingContext,
    user_input: str = "",
) -> str:
    """
    Build prompt with explicit mode, verifier result, and constraints.

    This ensures the agent knows:
    1. What mode we're in
    2. What the verifier determined (ground truth)
    3. What actions are allowed/forbidden

    Args:
        context: Full teaching context with verifier results
        user_input: Student's latest input (if continuing dialogue)

    Returns:
        Prompt string for the agent
    """
    mode = context.mode

    # Build base context
    prompt_parts = []

    # === MODE HEADER ===
    if mode == TeachingMode.GRADE_UPLOADED_ATTEMPT:
        prompt_parts.append(f"""MODE: GRADE_UPLOADED_ATTEMPT
A student just submitted handwritten work for grading.

PROBLEM:
{context.question_text}

OFFICIAL ANSWER:
{context.official_answer or "Not provided"}

STUDENT'S ANSWER:
{context.student_answer or "Not extracted"}

STUDENT'S STEPS:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(context.student_steps)) if context.student_steps else "(No steps extracted)"}

VERIFIER RESULT (GROUND TRUTH):
- Status: {"CORRECT" if context.is_correct else "INCORRECT" if not context.is_uncertain else "UNCERTAIN"}
- Certainty: {"CERTAIN" if not context.is_uncertain else "UNCERTAIN"}
- Details: {context.verifier_result.get('reason', '') if context.verifier_result else ''}

ERROR ANALYSIS (LLM GUESS, NOT AUTHORITATIVE):
- Suspected Type: {context.error_type or "None"}
- Suspected Issues: {context.error_candidates if context.error_candidates else "None"}
- Initial Feedback: {context.feedback}
""")

        # === DECISION RULES ===
        if context.is_correct:
            prompt_parts.append("""
MANDATORY RULE (HIGHEST PRIORITY):
The verifier has CONFIRMED the student's answer is CORRECT.
You MUST output action: "confirm_correct_and_stop"
You MUST NOT ask follow-up questions or continue teaching.
Acknowledge correctness briefly and STOP.
""")
        elif context.is_uncertain:
            prompt_parts.append("""
DECISION RULE:
The verifier is UNCERTAIN (could not determine correctness automatically).
You should output action: "ask_clarification"
Ask the student to explain their reasoning or check a specific step.
""")
        else:
            prompt_parts.append("""
DECISION RULE:
The verifier confirmed the answer is INCORRECT.
You may output action: "give_feedback" or "give_hint"
Use Socratic method - guide, don't solve for them.
""")

    elif mode == TeachingMode.CONTINUE_TEACHING:
        prompt_parts.append(f"""MODE: CONTINUE_TEACHING
Continuing Socratic dialogue with a student.

ORIGINAL PROBLEM:
{context.question_text}

KNOWN FACTS:
- Student's original answer was: {"CORRECT" if context.is_correct else "INCORRECT"}
- Current conversation:
{chr(10).join(f"{'Student' if msg['role'] == 'user' else 'Claire'}: {msg['content'][:100]}..." for msg in context.conversation_history[-4:])}

STUDENT'S LATEST INPUT:
{user_input}

DECISION RULE:
If student has now provided correct understanding/answer: "confirm_correct_and_stop"
If student is stuck or wrong: "give_hint" or "ask_clarification"
If student explicitly asks for full solution: "show_full_solution" (but discourage this)
""")

    elif mode == TeachingMode.SOLVE_NEW_PROBLEM:
        prompt_parts.append(f"""MODE: SOLVE_NEW_PROBLEM
Student is asking for help with a new problem.

PROBLEM:
{context.question_text}

STUDENT SAYS:
{user_input}

Use Socratic method - guide step by step, don't give away the answer.
Output action: "give_hint" or "ask_clarification"
""")

    elif mode == TeachingMode.FULL_SOLUTION:
        prompt_parts.append(f"""MODE: FULL_SOLUTION
Student has explicitly requested the full solution.

PROBLEM:
{context.question_text}

Output action: "show_full_solution"
Provide complete worked solution with all steps.
""")

    # === OUTPUT FORMAT ===
    prompt_parts.append("""
OUTPUT FORMAT (CRITICAL):
You MUST output ONLY valid JSON in this exact format:
{
  "action": "confirm_correct_and_stop" | "give_hint" | "give_feedback" | "ask_clarification" | "show_full_solution",
  "message": "What to show the student (your actual response text)",
  "reasoning": "Why you chose this action (for debugging)"
}

Do NOT output any text before or after the JSON.
Do NOT use markdown code blocks.
Just pure JSON.
""")

    return "\n".join(prompt_parts)


def parse_agent_decision(raw_output: str) -> Optional[TeachingDecision]:
    """
    Parse agent's structured JSON output into TeachingDecision.

    Args:
        raw_output: Raw text from agent

    Returns:
        TeachingDecision if parseable, None otherwise
    """
    try:
        # Clean up common formatting issues
        output = raw_output.strip()

        # Remove markdown code blocks if present
        if output.startswith("```"):
            lines = output.split("\n")
            # Find first and last ``` markers
            start_idx = 0
            end_idx = len(lines)
            for i, line in enumerate(lines):
                if line.strip().startswith("```"):
                    if start_idx == 0:
                        start_idx = i + 1
                    else:
                        end_idx = i
                        break
            output = "\n".join(lines[start_idx:end_idx])

        output = output.strip()

        # Parse JSON
        data = json.loads(output)

        action_str = data.get("action", "")
        message = data.get("message", "")
        reasoning = data.get("reasoning", "")

        # Validate action
        try:
            action = AgentAction(action_str)
        except ValueError:
            logger.warning(f"Invalid action from agent: {action_str}")
            return None

        return TeachingDecision(
            action=action,
            message=message,
            reasoning=reasoning,
            confidence=data.get("confidence", 1.0),
        )

    except json.JSONDecodeError as e:
        logger.error(f"Agent output is not valid JSON: {e}")
        logger.debug(f"Raw output (first 300 chars): {raw_output[:300]}")
        return None
    except Exception as e:
        logger.error(f"Failed to parse agent decision: {e}")
        return None


def enforce_teaching_rules(
    decision: TeachingDecision,
    context: TeachingContext,
) -> TeachingDecision:
    """
    Enforce hard rules based on verifier result.

    CRITICAL RULES:
    1. If verifier says CORRECT → MUST use confirm_correct_and_stop
    2. If verifier says INCORRECT → allow hint/feedback only
    3. If verifier is UNCERTAIN → allow ask_clarification only

    This prevents the agent from continuing to teach when student is already correct.

    Args:
        decision: Agent's proposed decision
        context: Teaching context with verifier results

    Returns:
        Enforced decision (may be modified if violates rules)
    """
    # RULE 1: If correct, MUST confirm and stop
    if context.is_correct:
        if decision.action != AgentAction.CONFIRM_CORRECT_AND_STOP:
            logger.warning(
                f"RULE ENFORCEMENT: Student is CORRECT but agent wanted to '{decision.action}'. "
                f"Forcing confirm_correct_and_stop."
            )
            return TeachingDecision(
                action=AgentAction.CONFIRM_CORRECT_AND_STOP,
                message="Great work! Your answer is correct. Well done!",
                reasoning="Enforced: verifier confirmed student answer is correct",
                confidence=1.0,
            )

    # RULE 2: If uncertain, prefer clarification
    if context.is_uncertain:
        # Allow ask_clarification or give_hint
        if decision.action not in [
            AgentAction.ASK_CLARIFICATION,
            AgentAction.GIVE_HINT,
            AgentAction.SHOW_FULL_SOLUTION,  # Allow if student explicitly requested
        ]:
            logger.warning(
                f"RULE ENFORCEMENT: Verifier is UNCERTAIN but agent wanted '{decision.action}'. "
                f"Forcing ask_clarification."
            )
            return TeachingDecision(
                action=AgentAction.ASK_CLARIFICATION,
                message=(
                    "I couldn't verify your answer automatically. "
                    "Can you walk me through your reasoning for this step?"
                ),
                reasoning="Enforced: verifier is uncertain, need student clarification",
                confidence=0.7,
            )

    # RULE 3: If incorrect, prohibit confirm_correct_and_stop
    if not context.is_correct and not context.is_uncertain:
        if decision.action == AgentAction.CONFIRM_CORRECT_AND_STOP:
            logger.warning(
                "RULE ENFORCEMENT: Student is INCORRECT but agent wanted to confirm correct. "
                "Forcing give_feedback."
            )
            return TeachingDecision(
                action=AgentAction.GIVE_FEEDBACK,
                message=context.feedback or "There's an issue with your answer. Let's work through it.",
                reasoning="Enforced: verifier says incorrect, cannot confirm correct",
                confidence=0.9,
            )

    # If mode is GRADE_UPLOADED_ATTEMPT and we haven't returned yet,
    # ensure we don't continue Socratic indefinitely
    if context.mode == TeachingMode.GRADE_UPLOADED_ATTEMPT:
        if decision.action not in [
            AgentAction.CONFIRM_CORRECT_AND_STOP,
            AgentAction.GIVE_FEEDBACK,
            AgentAction.GIVE_HINT,
            AgentAction.ASK_CLARIFICATION,
        ]:
            # Shouldn't be asking for full solution right after grading
            logger.warning(
                f"RULE ENFORCEMENT: In GRADE mode but agent wanted '{decision.action}'. "
                f"Forcing give_feedback."
            )
            return TeachingDecision(
                action=AgentAction.GIVE_FEEDBACK,
                message=decision.message,  # Keep the message but change action
                reasoning="Enforced: grade mode should give feedback, not continue indefinitely",
            )

    # Decision passes all rules
    return decision


def orchestrate_teaching_response(
    context: TeachingContext,
    agent,  # ClaireAgent instance
    user_input: str = "",
) -> TeachingDecision:
    """
    Main orchestration function.

    Process:
    1. Build mode-aware prompt with verifier facts
    2. Call agent to get structured decision (JSON)
    3. Parse decision
    4. Enforce hard rules based on verifier result
    5. Return final decision

    Args:
        context: Complete teaching context
        agent: ClaireAgent instance
        user_input: Student's latest input (if continuing)

    Returns:
        TeachingDecision with action and message
    """
    # Step 1: Build prompt
    prompt = build_mode_aware_prompt(context, user_input)

    # Step 2: Call agent with structured output mode
    try:
        # We'll add a new method to ClaireAgent for this
        result = agent.process_structured_teaching(prompt, context.conversation_history)
        raw_output = result.get("output", "")

        # Step 3: Parse decision
        decision = parse_agent_decision(raw_output)

        if not decision:
            # Parsing failed - fallback to safe default
            logger.error("Failed to parse agent decision, using fallback")
            if context.is_correct:
                decision = TeachingDecision(
                    action=AgentAction.CONFIRM_CORRECT_AND_STOP,
                    message="Your answer is correct!",
                    reasoning="Fallback: parsing failed but verifier says correct",
                )
            else:
                decision = TeachingDecision(
                    action=AgentAction.GIVE_HINT,
                    message=context.hint or "Let's work through this step by step.",
                    reasoning="Fallback: parsing failed",
                )

        # Step 4: Enforce rules
        enforced_decision = enforce_teaching_rules(decision, context)

        logger.info(
            f"Teaching decision: {enforced_decision.action} "
            f"(original: {decision.action if decision != enforced_decision else 'same'})"
        )

        return enforced_decision

    except Exception as e:
        logger.error(f"Orchestration error: {e}")
        import traceback
        traceback.print_exc()

        # Fallback to safe default
        if context.is_correct:
            return TeachingDecision(
                action=AgentAction.CONFIRM_CORRECT_AND_STOP,
                message="Your answer is correct!",
                reasoning=f"Error fallback: {e}",
            )
        else:
            return TeachingDecision(
                action=AgentAction.GIVE_HINT,
                message=context.hint or "Let's work through this together.",
                reasoning=f"Error fallback: {e}",
            )


def context_from_grading_result(
    problem,  # Problem object
    grading_result: GradingResult,
    analysis,  # SolutionAnalysis from vision_analyzer
    part_index: int = 0,
) -> TeachingContext:
    """
    Build TeachingContext from grading result.

    This is a helper for app.py to convert existing data into the new format.

    Args:
        problem: Problem object
        grading_result: GradingResult from grader or vision analyzer
        analysis: SolutionAnalysis from vision analyzer
        part_index: Which part to focus on

    Returns:
        TeachingContext
    """
    part = analysis.parts[part_index] if part_index < len(analysis.parts) else analysis.parts[0]
    problem_part = problem.parts[part_index] if part_index < len(problem.parts) else problem.parts[0]

    return TeachingContext(
        problem_id=problem.id,
        problem_stem=problem.stem or "",
        question_text=problem_part.question_text or "",
        official_answer=problem_part.final_answer,
        topic=problem.topic,
        concepts=getattr(problem, "concepts", []),
        student_answer=part.student_final_answer,
        student_steps=part.steps,
        is_correct=part.is_correct,
        is_uncertain=part.is_uncertain,
        verifier_result=part.verifier_result,
        error_type=part.error_type,
        error_candidates=part.error_candidates,
        feedback=part.feedback,
        hint=part.hint,
        confidence=part.confidence,
        mode=TeachingMode.GRADE_UPLOADED_ATTEMPT,
        conversation_history=[],
    )
