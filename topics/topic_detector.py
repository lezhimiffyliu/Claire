"""
Fine-grained Calculus Topic Detection

Uses LLM to detect specific topics from the calculus taxonomy.
This replaces the old coarse-grained pattern detection.
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Optional

# Load taxonomy at module level
TAXONOMY_PATH = Path(__file__).parent / "calculus_topics.md"

# All valid topic IDs (extracted from taxonomy)
VALID_TOPICS = [
    # Calculus I - Limits
    "limit_definition", "one_sided_limits", "infinite_limits", "limits_at_infinity",
    "squeeze_theorem", "continuity", "discontinuities_classification", "intermediate_value_theorem",

    # Calculus I - Derivatives Definition
    "limit_definition_of_derivative", "derivative_as_rate_of_change", "tangent_line",

    # Calculus I - Derivative Rules
    "power_rule", "product_rule", "quotient_rule", "chain_rule",

    # Calculus I - Special Derivatives
    "trigonometric_derivatives", "exponential_derivatives", "logarithmic_derivatives", "inverse_trig_derivatives",

    # Calculus I - Derivative Techniques
    "implicit_differentiation", "logarithmic_differentiation",

    # Calculus I - Derivative Applications
    "related_rates", "linear_approximation", "differentials", "lhopitals_rule",

    # Calculus I - Curve Analysis
    "critical_points", "first_derivative_test", "second_derivative_test",
    "concavity", "inflection_points", "curve_sketching",

    # Calculus I - Optimization
    "optimization_word_problems", "absolute_extrema", "closed_interval_method",

    # Calculus I - Integrals Intro
    "antiderivatives", "indefinite_integrals", "initial_value_problems",

    # Calculus II - Definite Integrals
    "riemann_sums", "definite_integral_definition",
    "fundamental_theorem_of_calculus_part1", "fundamental_theorem_of_calculus_part2",
    "average_value_of_function",

    # Calculus II - Integration Techniques
    "u_substitution", "integration_by_parts", "trigonometric_integrals",
    "trigonometric_substitution", "partial_fractions", "improper_integrals",

    # Calculus II - Integration Applications
    "area_between_curves", "volume_disk_method", "volume_washer_method",
    "volume_shell_method", "arc_length", "surface_area_of_revolution",
    "work_problems", "center_of_mass",

    # Calculus II - Differential Equations
    "separable_equations", "exponential_growth_decay", "slope_fields",

    # Calculus II - Sequences
    "sequence_convergence", "monotone_sequences", "bounded_sequences", "squeeze_theorem_sequences",

    # Calculus II - Series Basics
    "geometric_series", "telescoping_series", "harmonic_series", "p_series",

    # Calculus II - Convergence Tests
    "divergence_test", "integral_test", "comparison_test", "limit_comparison_test",
    "ratio_test", "root_test", "alternating_series_test", "absolute_vs_conditional_convergence",

    # Calculus II - Power Series
    "power_series", "radius_of_convergence", "interval_of_convergence",
    "taylor_series", "maclaurin_series", "taylor_polynomial_approximation",

    # Calculus II - Parametric & Polar
    "parametric_equations", "parametric_derivatives", "parametric_arc_length",
    "polar_coordinates", "polar_curves", "polar_area",

    # Calculus III - Vectors
    "vectors_2d_3d", "dot_product", "cross_product",
    "lines_in_space", "planes_in_space", "quadric_surfaces",

    # Calculus III - Vector Functions
    "vector_valued_functions", "derivatives_of_vector_functions",
    "arc_length_parameter", "curvature", "tangent_normal_binormal",

    # Calculus III - Partial Derivatives
    "partial_derivatives", "higher_order_partials", "chain_rule_multivariable",
    "implicit_differentiation_multivariable", "gradient", "directional_derivative",
    "tangent_planes", "linear_approximation_multivariable",

    # Calculus III - Multivariable Optimization
    "critical_points_multivariable", "second_derivative_test_multivariable",
    "lagrange_multipliers", "constrained_optimization", "absolute_extrema_multivariable",

    # Calculus III - Multiple Integrals
    "double_integrals_rectangular", "double_integrals_polar",
    "triple_integrals_rectangular", "triple_integrals_cylindrical", "triple_integrals_spherical",
    "change_of_variables_jacobian", "center_of_mass_moments",

    # Calculus III - Vector Calculus
    "vector_fields", "line_integrals_scalar", "line_integrals_vector",
    "conservative_fields", "potential_functions", "greens_theorem",
    "curl", "divergence", "surface_integrals", "stokes_theorem", "divergence_theorem",
]

# Topic display names (for UI)
TOPIC_DISPLAY_NAMES = {
    # Limits
    "limit_definition": "Limit Definition",
    "one_sided_limits": "One-Sided Limits",
    "infinite_limits": "Infinite Limits",
    "limits_at_infinity": "Limits at Infinity",
    "squeeze_theorem": "Squeeze Theorem",
    "continuity": "Continuity",
    "discontinuities_classification": "Types of Discontinuities",
    "intermediate_value_theorem": "Intermediate Value Theorem",

    # Derivatives
    "limit_definition_of_derivative": "Limit Definition of Derivative",
    "derivative_as_rate_of_change": "Derivative as Rate of Change",
    "tangent_line": "Tangent Line",
    "power_rule": "Power Rule",
    "product_rule": "Product Rule",
    "quotient_rule": "Quotient Rule",
    "chain_rule": "Chain Rule",
    "trigonometric_derivatives": "Trig Derivatives",
    "exponential_derivatives": "Exponential Derivatives",
    "logarithmic_derivatives": "Logarithmic Derivatives",
    "inverse_trig_derivatives": "Inverse Trig Derivatives",
    "implicit_differentiation": "Implicit Differentiation",
    "logarithmic_differentiation": "Logarithmic Differentiation",
    "related_rates": "Related Rates",
    "linear_approximation": "Linear Approximation",
    "differentials": "Differentials",
    "lhopitals_rule": "L'Hôpital's Rule",

    # Curve Analysis
    "critical_points": "Critical Points",
    "first_derivative_test": "First Derivative Test",
    "second_derivative_test": "Second Derivative Test",
    "concavity": "Concavity",
    "inflection_points": "Inflection Points",
    "curve_sketching": "Curve Sketching",

    # Optimization
    "optimization_word_problems": "Optimization Word Problems",
    "absolute_extrema": "Absolute Extrema",
    "closed_interval_method": "Closed Interval Method",

    # Integration
    "antiderivatives": "Antiderivatives",
    "indefinite_integrals": "Indefinite Integrals",
    "initial_value_problems": "Initial Value Problems",
    "riemann_sums": "Riemann Sums",
    "definite_integral_definition": "Definite Integral Definition",
    "fundamental_theorem_of_calculus_part1": "FTC Part 1",
    "fundamental_theorem_of_calculus_part2": "FTC Part 2",
    "average_value_of_function": "Average Value",
    "u_substitution": "u-Substitution",
    "integration_by_parts": "Integration by Parts",
    "trigonometric_integrals": "Trig Integrals",
    "trigonometric_substitution": "Trig Substitution",
    "partial_fractions": "Partial Fractions",
    "improper_integrals": "Improper Integrals",

    # Integration Applications
    "area_between_curves": "Area Between Curves",
    "volume_disk_method": "Volume (Disk)",
    "volume_washer_method": "Volume (Washer)",
    "volume_shell_method": "Volume (Shell)",
    "arc_length": "Arc Length",
    "surface_area_of_revolution": "Surface Area of Revolution",
    "work_problems": "Work Problems",
    "center_of_mass": "Center of Mass",

    # Differential Equations
    "separable_equations": "Separable Equations",
    "exponential_growth_decay": "Exponential Growth/Decay",
    "slope_fields": "Slope Fields",

    # Sequences & Series
    "sequence_convergence": "Sequence Convergence",
    "monotone_sequences": "Monotone Sequences",
    "bounded_sequences": "Bounded Sequences",
    "squeeze_theorem_sequences": "Squeeze Theorem (Sequences)",
    "geometric_series": "Geometric Series",
    "telescoping_series": "Telescoping Series",
    "harmonic_series": "Harmonic Series",
    "p_series": "p-Series",
    "divergence_test": "Divergence Test",
    "integral_test": "Integral Test",
    "comparison_test": "Comparison Test",
    "limit_comparison_test": "Limit Comparison Test",
    "ratio_test": "Ratio Test",
    "root_test": "Root Test",
    "alternating_series_test": "Alternating Series Test",
    "absolute_vs_conditional_convergence": "Absolute vs Conditional Convergence",
    "power_series": "Power Series",
    "radius_of_convergence": "Radius of Convergence",
    "interval_of_convergence": "Interval of Convergence",
    "taylor_series": "Taylor Series",
    "maclaurin_series": "Maclaurin Series",
    "taylor_polynomial_approximation": "Taylor Polynomial",

    # Parametric & Polar
    "parametric_equations": "Parametric Equations",
    "parametric_derivatives": "Parametric Derivatives",
    "parametric_arc_length": "Parametric Arc Length",
    "polar_coordinates": "Polar Coordinates",
    "polar_curves": "Polar Curves",
    "polar_area": "Polar Area",

    # Calculus III - Vectors
    "vectors_2d_3d": "Vectors",
    "dot_product": "Dot Product",
    "cross_product": "Cross Product",
    "lines_in_space": "Lines in Space",
    "planes_in_space": "Planes in Space",
    "quadric_surfaces": "Quadric Surfaces",

    # Vector Functions
    "vector_valued_functions": "Vector-Valued Functions",
    "derivatives_of_vector_functions": "Vector Function Derivatives",
    "arc_length_parameter": "Arc Length Parameter",
    "curvature": "Curvature",
    "tangent_normal_binormal": "TNB Frame",

    # Partial Derivatives
    "partial_derivatives": "Partial Derivatives",
    "higher_order_partials": "Higher Order Partials",
    "chain_rule_multivariable": "Chain Rule (Multivariable)",
    "implicit_differentiation_multivariable": "Implicit Diff (Multivariable)",
    "gradient": "Gradient",
    "directional_derivative": "Directional Derivative",
    "tangent_planes": "Tangent Planes",
    "linear_approximation_multivariable": "Linear Approximation (Multi)",

    # Multivariable Optimization
    "critical_points_multivariable": "Critical Points (Multi)",
    "second_derivative_test_multivariable": "Second Derivative Test (Multi)",
    "lagrange_multipliers": "Lagrange Multipliers",
    "constrained_optimization": "Constrained Optimization",
    "absolute_extrema_multivariable": "Absolute Extrema (Multi)",

    # Multiple Integrals
    "double_integrals_rectangular": "Double Integrals (Rectangular)",
    "double_integrals_polar": "Double Integrals (Polar)",
    "triple_integrals_rectangular": "Triple Integrals (Rectangular)",
    "triple_integrals_cylindrical": "Triple Integrals (Cylindrical)",
    "triple_integrals_spherical": "Triple Integrals (Spherical)",
    "change_of_variables_jacobian": "Change of Variables (Jacobian)",
    "center_of_mass_moments": "Center of Mass / Moments",

    # Vector Calculus
    "vector_fields": "Vector Fields",
    "line_integrals_scalar": "Line Integrals (Scalar)",
    "line_integrals_vector": "Line Integrals (Vector)",
    "conservative_fields": "Conservative Fields",
    "potential_functions": "Potential Functions",
    "greens_theorem": "Green's Theorem",
    "curl": "Curl",
    "divergence": "Divergence",
    "surface_integrals": "Surface Integrals",
    "stokes_theorem": "Stokes' Theorem",
    "divergence_theorem": "Divergence Theorem",
}

# Topic to course mapping
TOPIC_COURSE = {}
_calc1_topics = [
    "limit_definition", "one_sided_limits", "infinite_limits", "limits_at_infinity",
    "squeeze_theorem", "continuity", "discontinuities_classification", "intermediate_value_theorem",
    "limit_definition_of_derivative", "derivative_as_rate_of_change", "tangent_line",
    "power_rule", "product_rule", "quotient_rule", "chain_rule",
    "trigonometric_derivatives", "exponential_derivatives", "logarithmic_derivatives", "inverse_trig_derivatives",
    "implicit_differentiation", "logarithmic_differentiation",
    "related_rates", "linear_approximation", "differentials", "lhopitals_rule",
    "critical_points", "first_derivative_test", "second_derivative_test",
    "concavity", "inflection_points", "curve_sketching",
    "optimization_word_problems", "absolute_extrema", "closed_interval_method",
    "antiderivatives", "indefinite_integrals", "initial_value_problems",
]
_calc2_topics = [
    "riemann_sums", "definite_integral_definition",
    "fundamental_theorem_of_calculus_part1", "fundamental_theorem_of_calculus_part2",
    "average_value_of_function",
    "u_substitution", "integration_by_parts", "trigonometric_integrals",
    "trigonometric_substitution", "partial_fractions", "improper_integrals",
    "area_between_curves", "volume_disk_method", "volume_washer_method",
    "volume_shell_method", "arc_length", "surface_area_of_revolution",
    "work_problems", "center_of_mass",
    "separable_equations", "exponential_growth_decay", "slope_fields",
    "sequence_convergence", "monotone_sequences", "bounded_sequences", "squeeze_theorem_sequences",
    "geometric_series", "telescoping_series", "harmonic_series", "p_series",
    "divergence_test", "integral_test", "comparison_test", "limit_comparison_test",
    "ratio_test", "root_test", "alternating_series_test", "absolute_vs_conditional_convergence",
    "power_series", "radius_of_convergence", "interval_of_convergence",
    "taylor_series", "maclaurin_series", "taylor_polynomial_approximation",
    "parametric_equations", "parametric_derivatives", "parametric_arc_length",
    "polar_coordinates", "polar_curves", "polar_area",
]
_calc3_topics = [
    "vectors_2d_3d", "dot_product", "cross_product",
    "lines_in_space", "planes_in_space", "quadric_surfaces",
    "vector_valued_functions", "derivatives_of_vector_functions",
    "arc_length_parameter", "curvature", "tangent_normal_binormal",
    "partial_derivatives", "higher_order_partials", "chain_rule_multivariable",
    "implicit_differentiation_multivariable", "gradient", "directional_derivative",
    "tangent_planes", "linear_approximation_multivariable",
    "critical_points_multivariable", "second_derivative_test_multivariable",
    "lagrange_multipliers", "constrained_optimization", "absolute_extrema_multivariable",
    "double_integrals_rectangular", "double_integrals_polar",
    "triple_integrals_rectangular", "triple_integrals_cylindrical", "triple_integrals_spherical",
    "change_of_variables_jacobian", "center_of_mass_moments",
    "vector_fields", "line_integrals_scalar", "line_integrals_vector",
    "conservative_fields", "potential_functions", "greens_theorem",
    "curl", "divergence", "surface_integrals", "stokes_theorem", "divergence_theorem",
]

for t in _calc1_topics:
    TOPIC_COURSE[t] = "calc_i"
for t in _calc2_topics:
    TOPIC_COURSE[t] = "calc_ii"
for t in _calc3_topics:
    TOPIC_COURSE[t] = "calc_iii"


def get_topic_display(topic_id: str) -> str:
    """Get display name for a topic ID."""
    return TOPIC_DISPLAY_NAMES.get(topic_id, topic_id.replace("_", " ").title())


def get_topic_course(topic_id: str) -> str:
    """Get which calculus course a topic belongs to."""
    return TOPIC_COURSE.get(topic_id, "calc_i")


# ============================================================
# LLM-based Topic Detection
# ============================================================

DETECTION_PROMPT = '''你是一个微积分教学助手。

下面是标准的 calculus topics taxonomy（你必须严格从中选择）：

{taxonomy}

现在给你一段课程材料/题目内容，请判断它主要涉及哪些具体知识点。

要求：
1. 只能从上面的 taxonomy 中选择已有的 topic ID（snake_case 格式）
2. 必须选择细粒度 topics（例如 integration_by_parts，而不是 integration）
3. 最多返回 5 个
4. 按重要性排序
5. 只输出 JSON，不要解释

输入内容：
{content}

输出格式：
{{"topics": ["topic_id_1", "topic_id_2", ...]}}
'''


def _get_detection_llm():
    """Get LLM for topic detection. Uses DeepSeek (cheaper)."""
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from claire_agent import get_secret

        # Use DeepSeek (cheaper)
        deepseek_key = get_secret("DEEPSEEK_API_KEY")
        if deepseek_key:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model="deepseek-chat",
                api_key=deepseek_key,
                base_url="https://api.deepseek.com",
                temperature=0,
                max_tokens=256,
            )

        # Fallback to Claude
        anthropic_key = get_secret("ANTHROPIC_API_KEY")
        if anthropic_key:
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model="claude-sonnet-4-20250514",
                api_key=anthropic_key,
                temperature=0,
                max_tokens=256,
            )

    except Exception as e:
        print(f"[topic_detector] Error getting LLM: {e}")

    return None


def _load_taxonomy() -> str:
    """Load the taxonomy markdown file."""
    try:
        return TAXONOMY_PATH.read_text(encoding="utf-8")
    except Exception:
        # Return a simplified version if file not found
        return "\n".join(f"- {t}" for t in VALID_TOPICS)


def detect_topics_llm(content: str, max_topics: int = 5) -> list[str]:
    """
    Detect fine-grained topics from content using LLM.

    Args:
        content: Text content (lecture material, problem, etc.)
        max_topics: Maximum number of topics to return

    Returns:
        List of topic IDs from the taxonomy
    """
    if not content or len(content.strip()) < 20:
        return []

    llm = _get_detection_llm()
    if not llm:
        print("[topic_detector] No LLM available, falling back to keyword detection")
        return detect_topics_keyword(content)[:max_topics]

    # Truncate content if too long
    if len(content) > 3000:
        content = content[:3000] + "\n...[truncated]..."

    taxonomy = _load_taxonomy()
    prompt = DETECTION_PROMPT.format(taxonomy=taxonomy, content=content)

    try:
        from langchain_core.messages import HumanMessage
        result = llm.invoke([HumanMessage(content=prompt)])
        response_text = result.content.strip()

        # Extract JSON
        topics = _extract_topics_from_response(response_text)

        # Validate topics
        valid_topics = [t for t in topics if t in VALID_TOPICS]

        if valid_topics:
            return valid_topics[:max_topics]

    except Exception as e:
        print(f"[topic_detector] LLM error: {e}")

    # Fallback to keyword detection
    return detect_topics_keyword(content)[:max_topics]


def _extract_topics_from_response(response: str) -> list[str]:
    """Extract topic list from LLM response."""
    # Try to parse JSON
    try:
        # Find JSON in response
        json_match = re.search(r'\{[^{}]*"topics"[^{}]*\}', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            if isinstance(data.get("topics"), list):
                return data["topics"]
    except json.JSONDecodeError:
        pass

    # Try to extract list directly
    list_match = re.search(r'\[([^\]]+)\]', response)
    if list_match:
        items = re.findall(r'"([^"]+)"', list_match.group(1))
        return items

    return []


# ============================================================
# Keyword-based Fallback
# ============================================================

TOPIC_KEYWORDS = {
    # Limits
    "limit_definition": ["limit", "lim", "→", "approaches"],
    "one_sided_limits": ["one-sided", "left limit", "right limit", "x^+", "x^-"],
    "infinite_limits": ["infinite limit", "→∞", "to infinity"],
    "squeeze_theorem": ["squeeze", "sandwich"],
    "continuity": ["continuous", "continuity"],
    "lhopitals_rule": ["l'hopital", "l'hôpital", "0/0", "∞/∞"],

    # Derivatives
    "power_rule": ["power rule", "x^n", "nx^{n-1}"],
    "product_rule": ["product rule", "(fg)'", "f'g + fg'"],
    "quotient_rule": ["quotient rule", "(f/g)'"],
    "chain_rule": ["chain rule", "f(g(x))", "composite"],
    "implicit_differentiation": ["implicit", "dy/dx"],
    "related_rates": ["related rate", "rate of change", "how fast", "dv/dt", "dr/dt"],
    "tangent_line": ["tangent line", "tangent at"],

    # Integration
    "u_substitution": ["u-sub", "substitution", "let u ="],
    "integration_by_parts": ["by parts", "∫udv", "uv - ∫vdu"],
    "trigonometric_integrals": ["∫sin", "∫cos", "∫tan", "∫sec"],
    "trigonometric_substitution": ["trig sub", "x = sin", "x = tan", "x = sec"],
    "partial_fractions": ["partial fraction"],
    "improper_integrals": ["improper", "∫_0^∞", "∫_{-∞}"],

    # Applications
    "area_between_curves": ["area between", "region bounded"],
    "volume_disk_method": ["disk method", "disk/washer"],
    "volume_shell_method": ["shell method", "cylindrical shell"],
    "arc_length": ["arc length"],

    # Series
    "taylor_series": ["taylor", "taylor series"],
    "maclaurin_series": ["maclaurin"],
    "power_series": ["power series", "Σx^n"],
    "ratio_test": ["ratio test"],
    "root_test": ["root test"],
    "comparison_test": ["comparison test"],
    "geometric_series": ["geometric series", "ar^n"],
    "p_series": ["p-series", "1/n^p"],

    # Multivariable
    "partial_derivatives": ["∂", "partial derivative", "f_x", "f_y"],
    "gradient": ["gradient", "∇f", "grad f"],
    "directional_derivative": ["directional derivative"],
    "lagrange_multipliers": ["lagrange", "λ", "constraint", "subject to"],
    "double_integrals_rectangular": ["double integral", "∬", "dxdy", "dydx"],
    "double_integrals_polar": ["polar", "rdrdθ", "r dr dθ"],
    "triple_integrals_rectangular": ["triple integral", "∭", "dxdydz"],
    "triple_integrals_cylindrical": ["cylindrical", "rdzdrdθ"],
    "triple_integrals_spherical": ["spherical", "ρ²sinφ"],

    # Vector Calculus
    "greens_theorem": ["green's theorem", "green theorem"],
    "stokes_theorem": ["stokes", "stoke's"],
    "divergence_theorem": ["divergence theorem", "gauss"],
    "curl": ["curl", "∇×"],
    "divergence": ["divergence", "∇·", "div"],
    "line_integrals_vector": ["line integral", "∫_C F·dr"],
    "surface_integrals": ["surface integral", "∬_S"],
}


def detect_topics_keyword(content: str) -> list[str]:
    """
    Fallback: Detect topics using keyword matching.
    Less accurate but works without LLM.
    """
    content_lower = content.lower()
    scores = {}

    for topic, keywords in TOPIC_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in content_lower)
        if score > 0:
            scores[topic] = score

    # Sort by score descending
    sorted_topics = sorted(scores.keys(), key=lambda t: scores[t], reverse=True)

    return sorted_topics[:5]


# ============================================================
# Batch Detection (for multiple questions/materials)
# ============================================================

def detect_topics_batch(contents: list[str], llm=None) -> list[list[str]]:
    """
    Detect topics for multiple pieces of content.
    Reuses LLM instance for efficiency.
    """
    if llm is None:
        llm = _get_detection_llm()

    results = []
    for content in contents:
        if llm:
            topics = detect_topics_llm(content)
        else:
            topics = detect_topics_keyword(content)
        results.append(topics)

    return results


# ============================================================
# Aggregate Topics (for exam scope analysis)
# ============================================================

def aggregate_topics(all_topics: list[list[str]]) -> dict[str, int]:
    """
    Aggregate topic counts from multiple questions/materials.

    Returns:
        Dict mapping topic_id to count
    """
    counts = {}
    for topics in all_topics:
        for topic in topics:
            counts[topic] = counts.get(topic, 0) + 1

    return counts


def get_top_topics(all_topics: list[list[str]], n: int = 10) -> list[tuple[str, int]]:
    """
    Get the most frequent topics.

    Returns:
        List of (topic_id, count) tuples sorted by count descending
    """
    counts = aggregate_topics(all_topics)
    sorted_topics = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_topics[:n]
