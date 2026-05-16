"""
Concept Alias Mapping Layer

Maps problem.concepts (various naming conventions) to canonical taxonomy subtopics.
Taxonomy SECTIONS.concepts remain the canonical source of truth.

Usage:
    from taxonomy.concept_aliases import normalize_concept, normalize_concepts

    canonical = normalize_concept("cross_product")  # -> "cross_product_computation"
    canonical_list = normalize_concepts(["cross_product", "dot_product"])
"""

# Alias map: problem concept -> canonical taxonomy subtopic
# If a concept is not in this map, it passes through unchanged
CONCEPT_ALIASES = {
    # Cross product variants
    "cross_product": "cross_product_computation",
    "area_of_parallelogram": "area_of_parallelogram_via_cross_product",
    "volume": "volume_of_parallelepiped",

    # Tangent planes variants
    "tangent_planes": "tangent_plane_equation",
    "linearization": "linear_approximation_multivariable",

    # Partial derivatives variants
    "partial_derivatives": "partial_derivative_definition",
    "derivatives": "partial_derivative_definition",

    # Optimization variants
    "critical_points": "critical_points_multivariable",
    "extrema": "local_extrema_multivariable",
    "saddle_points": "second_derivative_test_multivariable",
    "optimization": "optimization_with_constraints",
    "constrained_optimization": "optimization_with_constraints",

    # Double integrals variants
    "double_integrals": "double_integrals_over_general_regions",
    "multiple_integrals": "double_integrals_over_general_regions",

    # Polar variants
    "polar_coordinates": "polar_coordinate_conversion",

    # Vector variants
    "vectors": "vector_operations",
    "unit_vectors": "magnitude_and_direction",
    "projections": "vector_projection",

    # Lines and planes variants
    "lines": "parametric_equations_of_lines",
    "planes": "equations_of_planes",
    "lines_and_planes": "equations_of_planes",
    "parallel_planes": "parallel_and_perpendicular_conditions",
    "perpendicular_conditions": "parallel_and_perpendicular_conditions",
    "intersection": "line_plane_intersection",
    "distance": "three_dimensional_coordinate_system",
    "distance_formula": "three_dimensional_coordinate_system",

    # Quadric surfaces variants
    "quadric_surfaces": "surface_identification",
    "surfaces": "surface_identification",
    "paraboloid": "elliptic_paraboloid",
    "paraboloids": "elliptic_paraboloid",
    "cylinder": "cylinders",
    "spheres": "three_dimensional_coordinate_system",

    # Vector valued functions variants
    "vector_valued_functions": "vector_functions_definition",
    "parametrization": "parametrization_of_curves",

    # Motion in space variants
    "motion_in_space": "velocity_vector",
    "osculating_plane": "normal_plane",

    # Taylor variants
    "taylor_series": "taylor_series_definition",
    "taylor_polynomials": "higher_order_taylor_polynomial",
    "taylor_polynomials_and_series": "taylor_series_definition",
    "taylor_polynomial_construction": "higher_order_taylor_polynomial",
    "series": "taylor_series_definition",
    "convergence_of_series": "taylor_series_definition",
    "error_bounds": "error_estimation_taylor",

    # Applications variants
    "applications_of_double_integrals": "mass_from_density_2d",
    "center_of_mass": "center_of_mass_2d",
    "density": "mass_from_density_2d",
    "lamina": "mass_from_density_2d",

    # Multivariable functions variants
    "multivariable_optimization": "critical_points_multivariable",
    "directional_derivatives": "partial_derivative_definition",

    # Other
    "three_dimensional_geometry": "three_dimensional_coordinate_system",
    "skew_lines": "parametric_equations_of_lines",
}


def normalize_concept(concept: str) -> str:
    """
    Normalize a single concept to its canonical taxonomy subtopic.
    Returns the alias if found, otherwise returns the original concept.
    """
    return CONCEPT_ALIASES.get(concept, concept)


def normalize_concepts(concepts: list) -> list:
    """
    Normalize a list of concepts to canonical taxonomy subtopics.
    Preserves order, removes duplicates after normalization.
    """
    if not concepts:
        return []

    seen = set()
    result = []
    for c in concepts:
        normalized = normalize_concept(c)
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def debug_matching_report():
    """
    Print a debug report showing:
    - Unmatched problem concepts (concepts that don't normalize to any taxonomy subtopic)
    - Match counts per section
    - Sample problem IDs per section
    """
    import json
    import os
    from taxonomy.math126 import SECTIONS, SUBTOPIC_METADATA

    # Load all Math 126 problems
    problems_dir = os.path.join(os.path.dirname(__file__), '..', 'problems')
    all_problems = []
    for f in os.listdir(problems_dir):
        if f.startswith('math126') and f.endswith('.json'):
            with open(os.path.join(problems_dir, f)) as fp:
                all_problems.extend(json.load(fp))

    taxonomy_subtopics = set(SUBTOPIC_METADATA.keys())

    # Track unmatched concepts
    unmatched = set()
    for p in all_problems:
        for c in p.get('concepts', []):
            normalized = normalize_concept(c)
            if normalized not in taxonomy_subtopics:
                unmatched.add(f"{c} -> {normalized}")

    print("=" * 60)
    print("CONCEPT MATCHING DEBUG REPORT")
    print("=" * 60)

    print(f"\nTotal problems: {len(all_problems)}")
    print(f"Taxonomy subtopics: {len(taxonomy_subtopics)}")

    print(f"\n--- UNMATCHED CONCEPTS ({len(unmatched)}) ---")
    for u in sorted(unmatched):
        print(f"  {u}")

    print(f"\n--- SECTION MATCHING ---")
    for section in SECTIONS:
        sec_concepts = set(section.get('concepts', []))
        matching = []
        for p in all_problems:
            normalized = normalize_concepts(p.get('concepts', []))
            if any(c in sec_concepts for c in normalized):
                matching.append(p['id'])

        status = "OK" if matching else "EMPTY"
        sample = matching[:3] if matching else []
        print(f"  {section['id']:15} {section['display_name']:40} {len(matching):3} problems [{status}]")
        if sample:
            print(f"                  Sample: {sample}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    debug_matching_report()
