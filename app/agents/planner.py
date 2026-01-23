"""Planner agent responsible for lesson structure."""

from typing import List

from app.models.agents import PlannedSection
    
class PlannerAgent:
    """Generates a deterministic lesson plan."""
    def plan(self, topic: str, level: str) -> List[PlannedSection]:
        """Return a section outline based on topic and level."""
        if level == "intermediate":
            minutes = {"concept": 4, "example": 7, "exercise": 4}
        else:
            minutes = {"concept": 5, "example": 6, "exercise": 4}
        return [
            PlannedSection(
                id="concept",
                title="Core concept",
                minutes=minutes["concept"],
            ),
            PlannedSection(
                id="example",
                title="Worked example",
                minutes=minutes["example"],
            ),
            PlannedSection(
                id="exercise",
                title="Practice exercise",
                minutes=minutes["exercise"],
            ),
        ]
        
