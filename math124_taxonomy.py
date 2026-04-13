"""
UW Math 124 (Calculus I) Taxonomy for Benchmark / Question Bank Tagging
========================================================================

Two-layer taxonomy aligned with UW Math 124 - Spring 2026 syllabus.
Textbook: Stewart, Calculus: Early Transcendentals, 9th Edition.

Scope note: UW Math 124 covers limits through optimization. It does NOT
cover antiderivatives / definite integrals (those are in Math 125). It
DOES cover parametric equations and derivatives of parametrized curves
(Sec. 10.1-10.2), which many other Calc I courses defer to Calc II.

Layers:
- TOPICS: product-level tags for recommender systems (coarse, ~11 buckets)
- CONCEPTS: pedagogy-level tags per topic (fine but clusterable)

Orthogonal dimensions for AI agent benchmarking:
- SKILL_TYPES, DIFFICULTY, REPRESENTATION, COMMON_PITFALLS

Example usage:
    from math124_taxonomy import TAXONOMY, TOPICS, CONCEPTS

    question_tags = {
        "topic": "chain_rule_and_implicit",
        "concepts": ["chain_rule", "implicit_differentiation"],
        "skill_type": "computational",
        "difficulty": "standard",
        "representation": "symbolic",
        "common_pitfalls": ["sign_error_prone"],
    }
"""

# ---------------------------------------------------------------------------
# TOPIC LAYER  (product-facing, for recommender / clustering)
# ---------------------------------------------------------------------------
TOPICS = [
    "tangents_and_velocity",          # Week 1: tangents to circles, Sec 2.1
    "limits_and_continuity",          # Sec 2.2, 2.3, 2.5, 2.6
    "derivative_definition",          # Sec 2.7, 2.8
    "derivative_rules",               # Sec 3.1, 3.2, 3.3
    "chain_rule_and_implicit",        # Sec 3.4, 3.5
    "parametric_equations",           # Sec 10.1, 10.2
    "logarithmic_differentiation",    # Sec 3.6
    "related_rates",                  # Sec 3.9
    "linear_approximation",           # Sec 3.10
    "extrema_and_shape",              # Sec 4.1, 4.3
    "lhopitals_rule",                 # Sec 4.4
    "curve_sketching",                # Sec 4.5
    "optimization",                   # Sec 4.7
]

# ---------------------------------------------------------------------------
# CONCEPT LAYER  (pedagogy-facing, per topic)
# ---------------------------------------------------------------------------
CONCEPTS = {
    "tangents_and_velocity": [
        "tangent_to_circle",
        "secant_line",
        "average_velocity",
        "instantaneous_velocity",
        "slope_as_limit",
    ],

    "limits_and_continuity": [
        "limits",  # alias
        "limit_intuition",
        "limit_laws",
        "one_sided_limits",
        "infinite_limits",
        "limits_at_infinity",
        "vertical_asymptotes",
        "horizontal_asymptotes",
        "slant_asymptotes",
        "squeeze_theorem",
        "trig_limits",
        "indeterminate_form_algebraic",
        "continuity_definition",
        "continuity_at_a_point",
        "removable_discontinuity",
        "jump_discontinuity",
        "intermediate_value_theorem",
        "piecewise_continuity",
    ],

    "derivative_definition": [
        "limit_definition_of_derivative",
        "derivative_as_slope",
        "derivative_as_rate_of_change",
        "tangent_line_equation",
        "differentiability",
        "differentiability_vs_continuity",
        "nondifferentiable_points",
        "derivative_from_graph",
        "higher_order_derivatives",
    ],

    "derivative_rules": [
        "derivatives",  # alias
        "differentiation",  # alias
        "constant_rule",
        "power_rule",
        "sum_difference_rule",
        "product_rule",
        "quotient_rule",
        "exponential_derivative",
        "sine_cosine_derivative",
        "tangent_secant_derivative",
        "cotangent_cosecant_derivative",
        "derivative_of_polynomial",
        "derivative_of_rational_function",
    ],

    "chain_rule_and_implicit": [
        "chain_rule",
        "chain_rule_multiple_layers",
        "chain_rule_with_trig",
        "chain_rule_with_exponential",
        "implicit_differentiation",
        "implicit_tangent_line",
        "derivative_of_inverse_trig",
        "derivative_of_logarithm",
        "horizontal_vertical_tangents_implicit",
    ],

    "parametric_equations": [
        "parametric_curves",  # alias
        "parametric_curve_graphing",
        "eliminating_parameter",
        "parametric_first_derivative",
        "parametric_second_derivative",
        "parametric_tangent_line",
        "horizontal_vertical_tangents_parametric",
        "parametric_motion_interpretation",
    ],

    "logarithmic_differentiation": [
        "log_properties_for_differentiation",
        "logarithmic_differentiation_technique",
        "variable_base_variable_exponent",
        "product_to_sum_simplification",
    ],

    "related_rates": [
        "related_rates_setup",
        "implicit_time_differentiation",
        "geometric_related_rates",     # ladders, shadows, cones, spheres
        "trigonometric_related_rates", # angles of elevation
        "rate_interpretation",
        "units_and_sign_conventions",
    ],

    "linear_approximation": [
        "linearization_at_a_point",
        "differentials",
        "error_approximation",
        "percent_error",
        "tangent_line_approximation",
    ],

    "extrema_and_shape": [
        "absolute_extrema",
        "local_extrema",
        "critical_points",
        "closed_interval_method",
        "fermats_theorem",
        "extreme_value_theorem",
        "mean_value_theorem",
        "rolles_theorem",
        "increasing_decreasing_test",
        "first_derivative_test",
        "concavity",
        "inflection_points",
        "second_derivative_test",
    ],

    "lhopitals_rule": [
        "indeterminate_zero_over_zero",
        "indeterminate_infinity_over_infinity",
        "indeterminate_zero_times_infinity",
        "indeterminate_infinity_minus_infinity",
        "indeterminate_power_forms",       # 0^0, 1^inf, inf^0
        "lhopital_application",
        "when_lhopital_fails",
    ],

    "curve_sketching": [
        "graph_analysis",  # alias
        "graph_interpretation",  # alias
        "domain_analysis",
        "symmetry_analysis",
        "asymptote_analysis",
        "intercepts",
        "monotonicity_analysis",
        "concavity_analysis",
        "full_curve_sketch",
    ],

    "optimization": [
        "optimization_setup",
        "objective_function",
        "constraint_equation",
        "closed_interval_optimization",
        "open_interval_optimization",
        "geometric_optimization",          # boxes, fences, cans
        "distance_optimization",
        "economic_optimization",           # cost, revenue, profit
        "second_derivative_verification",
    ],
}

# ---------------------------------------------------------------------------
# ORTHOGONAL DIMENSIONS  (recommended for AI agent benchmarking)
# ---------------------------------------------------------------------------
SKILL_TYPES = [
    "computational",      # pure symbolic/numeric calculation
    "conceptual",         # definitions, true/false, "which of these"
    "proof",              # show / prove / justify
    "application",        # word problems, modeling
    "multi_step",         # chains multiple techniques
    "graphical",          # read or produce a graph
]

DIFFICULTY = [
    "routine",            # worked-example level
    "standard",           # typical homework / quiz
    "challenging",        # exam hard problem / challenge
]

REPRESENTATION = [
    "symbolic",
    "numerical",
    "graphical",
    "tabular",
    "word_problem",
    "proof_writing",
]

COMMON_PITFALLS = [
    "sign_error_prone",
    "chain_rule_forgotten",
    "product_quotient_confusion",
    "domain_restriction_ignored",
    "one_sided_limit_required",
    "indeterminate_form_misidentified",
    "implicit_dy_dx_omitted",
    "units_required",
    "endpoint_check_required",
    "critical_point_vs_extremum_confusion",
    "constraint_substitution_error",
    "parameter_vs_variable_confusion",
]

# ---------------------------------------------------------------------------
# UNIFIED TAXONOMY (single import)
# ---------------------------------------------------------------------------
TAXONOMY = {
    "course": "UW Math 124 - Calculus I",
    "textbook": "Stewart, Calculus: Early Transcendentals, 9th Edition",
    "topics": TOPICS,
    "concepts": CONCEPTS,
    "skill_types": SKILL_TYPES,
    "difficulty": DIFFICULTY,
    "representation": REPRESENTATION,
    "common_pitfalls": COMMON_PITFALLS,
}


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS (for recommender, profile, etc.)
# ---------------------------------------------------------------------------

# Build reverse lookup: concept -> topic
_CONCEPT_TO_TOPIC = {}
for topic, concepts in CONCEPTS.items():
    for concept in concepts:
        _CONCEPT_TO_TOPIC[concept] = topic


def get_topic_for_concept(concept: str) -> str | None:
    """Map a concept to its parent topic."""
    return _CONCEPT_TO_TOPIC.get(concept)


def get_all_concepts(topic: str) -> list[str]:
    """Get all concepts under a topic."""
    return CONCEPTS.get(topic, [])


def is_valid_topic(topic: str) -> bool:
    """Check if topic is in the canonical list."""
    return topic in TOPICS


def is_valid_concept(concept: str) -> bool:
    """Check if concept exists."""
    return concept in _CONCEPT_TO_TOPIC


def normalize_to_topic(name: str) -> str:
    """
    Normalize any name (topic or concept) to a canonical topic.
    Returns original if not found.
    """
    # If it's already a topic, return it
    if name in TOPICS:
        return name
    # If it's a concept, return its parent topic
    if name in _CONCEPT_TO_TOPIC:
        return _CONCEPT_TO_TOPIC[name]
    # Not found, return original
    return name


def get_topic_display_name(topic: str) -> str:
    """Human-readable topic name."""
    return topic.replace("_", " ").title()


# Foundation topics (prerequisites, core skills)
FOUNDATION_TOPICS = [
    "limits_and_continuity",
    "derivative_definition",
    "derivative_rules",
]


if __name__ == "__main__":
    # Quick sanity check
    print(f"Course: {TAXONOMY['course']}")
    print(f"Topics: {len(TOPICS)}")
    total_concepts = sum(len(v) for v in CONCEPTS.values())
    print(f"Total concepts: {total_concepts}")
    for t in TOPICS:
        assert t in CONCEPTS, f"Missing concepts for topic: {t}"
        print(f"  {t}: {len(CONCEPTS[t])} concepts")
    print("All topics have concepts. ✓")

    # Test helpers
    print()
    print("Helper tests:")
    print(f"  chain_rule -> {normalize_to_topic('chain_rule')}")
    print(f"  optimization -> {normalize_to_topic('optimization')}")
    print(f"  squeeze_theorem -> {normalize_to_topic('squeeze_theorem')}")
