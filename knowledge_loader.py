"""
Knowledge Loader - Preload common concepts and questions
"""

from typing import Dict, List


class KnowledgeLoader:
    """Load and manage knowledge base"""

    def __init__(self):
        self.concepts = self._load_default_concepts()
        self.examples = self._load_examples()

    def _load_default_concepts(self) -> Dict[str, Dict]:
        """Load default concepts"""
        return {
            "derivative": {
                "name": "Derivative",
                "definition": "The derivative measures how a function changes as its input changes.",
                "analogy": "Like speedometer showing instantaneous speed",
                "formula": "f'(x) = lim_{h→0} [f(x+h) - f(x)]/h",
                "examples": ["d/dx(x²) = 2x", "d/dx(sin x) = cos x"],
            },
            "integral": {
                "name": "Integral",
                "definition": "The integral finds the accumulation of quantities, like area under a curve.",
                "analogy": "Like adding up tiny pieces to find total area",
                "formula": "∫f(x)dx = F(x) + C",
                "examples": ["∫2x dx = x² + C", "∫cos x dx = sin x + C"],
            },
            "limit": {
                "name": "Limit",
                "definition": "A limit describes the value a function approaches as the input approaches some value.",
                "analogy": "Like seeing where you're headed without arriving",
                "formula": "lim_{x→a} f(x) = L",
                "examples": ["lim_{x→0} sin(x)/x = 1", "lim_{x→∞} 1/x = 0"],
            },
        }

    def _load_examples(self) -> Dict[str, List[str]]:
        """Load example questions"""
        return {
            "beginner": [
                "What is a derivative?",
                "Find the derivative of x^2",
                "What is the integral of 2x?",
                "Explain limits simply",
            ],
            "intermediate": [
                "Use the chain rule to find derivative of sin(x^2)",
                "Calculate ∫ x·e^x dx",
                "Find lim_{x→0} (1-cos x)/x^2",
                "Explain the fundamental theorem of calculus",
            ],
            "advanced": [
                "Solve the differential equation dy/dx = y",
                "Find the Taylor series for e^x",
                "Calculate ∫_0^∞ e^{-x^2} dx",
                "Explain the concept of a limit using epsilon-delta definition",
            ],
        }

    def get_concept(self, concept_name: str) -> Dict:
        """Get concept information"""
        return self.concepts.get(concept_name.lower())

    def get_examples(self, level: str = "beginner") -> List[str]:
        """Get example questions"""
        return self.examples.get(level, [])
