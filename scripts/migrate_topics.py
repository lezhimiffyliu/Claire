#!/usr/bin/env python3
"""
Migrate problem JSON files to use canonical taxonomy topics.
"""

import json
from pathlib import Path

# Topic mappings: old_name -> new_canonical_name

MAPPING_124 = {
    "curve_sketching": "curve_analysis",
    "derivatives": "derivative_rules",
    "differentiation": "derivative_rules",
    "graph_analysis": "curve_analysis",
    "graph_interpretation": "curve_analysis",
    "implicit_differentiation": "implicit_differentiation",
    "limits": "limits",
    "linear_approximation": "linear_approximation",
    "optimization": "optimization",
    "related_rates": "related_rates",
    "parametric": "parametric_equations",
    "parametric_equations": "parametric_equations",
    "parametric_curves": "parametric_equations",
    "continuity": "continuity",
    "derivative_definition": "derivative_definition",
    "lhopitals_rule": "lhopitals_rule",
}

MAPPING_125 = {
    "area_and_center_of_mass": "applications_of_integration",
    "comparison_test": "improper_integrals",
    "definite_integrals_from_graph": "fundamental_theorem_of_calculus",
    "differential_equations_logistic": "differential_equations",
    "differential_equations_separable": "differential_equations",
    "indefinite_integrals": "antiderivatives_and_riemann_sums",
    "kinematics_work_integral": "work",
    "volume_of_revolution": "volumes",
    "work_coulombs_law": "work",
    "u_substitution": "substitution",
    "integration_by_parts": "integration_by_parts",
    "trig_substitution": "trigonometric_substitution",
    "trigonometric_substitution": "trigonometric_substitution",
    "partial_fractions": "partial_fractions",
    "improper_integrals": "improper_integrals",
    "area_between_curves": "area_between_curves",
    "arc_length": "arc_length",
    "volumes": "volumes",
    "work": "work",
}

MAPPING_126 = {
    "center_of_mass_double_integrals": "applications_of_double_integrals",
    "multiple_choice_vectors_spheres": "vectors_and_geometry",
    "optimization_constrained": "multivariable_optimization",
    "surfaces_vector_curves": "vector_valued_functions",
    "tangent_planes_linearization": "tangent_planes_and_differentials",
    "taylor_polynomials_taylor_series": "taylor_polynomials_and_series",
    "taylor_series": "taylor_polynomials_and_series",
    "triple_integrals_polar_coordinates": "double_integrals",  # UW 126 doesn't cover triple integrals per taxonomy
    "double_integrals": "double_integrals",
    "polar_coordinates": "polar_coordinates",
    "partial_derivatives": "partial_derivatives",
    "lagrange_multipliers": "multivariable_optimization",
    "vectors_and_geometry": "vectors_and_geometry",
    "lines_and_planes": "lines_and_planes",
    "quadric_surfaces": "quadric_surfaces",
    "vector_valued_functions": "vector_valued_functions",
    "motion_in_space": "motion_in_space",
    "multivariable_functions": "multivariable_functions",
    "multivariable_optimization": "multivariable_optimization",
    "applications_of_double_integrals": "applications_of_double_integrals",
}


def migrate_file(filepath: Path, mapping: dict) -> int:
    """Migrate topics in a JSON file. Returns count of changes."""
    with open(filepath, 'r', encoding='utf-8') as f:
        problems = json.load(f)

    changes = 0
    for p in problems:
        old_topic = p.get("topic", "")
        if old_topic in mapping:
            new_topic = mapping[old_topic]
            if old_topic != new_topic:
                print(f"  {old_topic} → {new_topic}")
                p["topic"] = new_topic
                changes += 1
        elif old_topic:
            print(f"  ⚠️  Unknown topic: {old_topic}")

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(problems, f, indent=2, ensure_ascii=False)

    return changes


def main():
    base_dir = Path(__file__).parent.parent
    problems_dir = base_dir / "problems"
    uw_data_dir = base_dir / "uw_data"

    print("=== Migrating Math 124 ===")
    for f in problems_dir.glob("math124_*.json"):
        print(f"\n{f.name}:")
        changes = migrate_file(f, MAPPING_124)
        print(f"  {changes} topics updated")

    print("\n=== Migrating Math 125 ===")
    for f in list(problems_dir.glob("math125_*.json")) + list(uw_data_dir.glob("math125_*.json")):
        print(f"\n{f.name}:")
        changes = migrate_file(f, MAPPING_125)
        print(f"  {changes} topics updated")

    print("\n=== Migrating Math 126 ===")
    for f in list(problems_dir.glob("math126_*.json")) + list(uw_data_dir.glob("math126_*.json")):
        print(f"\n{f.name}:")
        changes = migrate_file(f, MAPPING_126)
        print(f"  {changes} topics updated")

    print("\n✅ Migration complete")


if __name__ == "__main__":
    main()
