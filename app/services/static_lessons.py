"""Static lesson templates for demo deployments."""

from app.models.agents import ContentBlock
from app.models.api import LessonResponse, LessonSection
from app.services.markdown_renderer import render_blocks_to_markdown

_SECTION_MINUTES = {
    "beginner": {"concept": 5, "example": 6, "exercise": 4},
    "intermediate": {"concept": 4, "example": 7, "exercise": 4},
}
_LEVEL_GUIDANCE = {
    "beginner": {
        "concept": "Beginner focus: define terms plainly and keep the first example concrete.",
        "exercise": "Beginner focus: keep the dataset tiny and explain each step.",
    },
    "intermediate": {
        "concept": "Intermediate focus: highlight tradeoffs and note a common pitfall.",
        "exercise": "Intermediate focus: add one constraint or edge case.",
    },
}

_STATIC_TEMPLATES: dict[str, dict[str, str]] = {
    "statistical tests comparing population means": {
        "concept": (
            "Compare two means by matching the test to the question and assumptions.\n\n"
            "- Use a t-test for two groups, ANOVA for three or more.\n"
            "- Check normality and variance equality.\n"
            "- Report effect size alongside the p-value."
        ),
        "example": (
            "We run an independent samples t-test and interpret the result."
        ),
        "python": (
            "from scipy import stats\n\n"
            "group_a = [12, 10, 13, 11, 9]\n"
            "group_b = [8, 7, 9, 6, 7]\n\n"
            "t_stat, p_value = stats.ttest_ind(group_a, group_b, equal_var=False)\n"
            "print(f\"t={t_stat:.2f}, p={p_value:.3f}\")"
        ),
        "exercise": (
            "Pick two groups in a dataset you know. Run a t-test, then write one sentence "
            "explaining the practical meaning of the result."
        ),
    },
    "pandas groupby performance": {
        "concept": (
            "Speed up groupby by reducing work and avoiding slow Python loops.\n\n"
            "- Filter early and keep only needed columns.\n"
            "- Prefer built-in aggregations over custom functions.\n"
            "- Use categorical types for low-cardinality keys."
        ),
        "example": (
            "We aggregate sales by region using built-in operations."
        ),
        "python": (
            "import pandas as pd\n\n"
            "df = pd.DataFrame({\n"
            "    \"region\": [\"north\", \"south\", \"north\", \"east\"],\n"
            "    \"sales\": [10, 7, 14, 3],\n"
            "})\n\n"
            "result = df.groupby(\"region\", sort=False)[\"sales\"].sum()\n"
            "print(result)"
        ),
        "exercise": (
            "Take a dataset with a categorical key. Try one groupby with a custom function, "
            "then replace it with a built-in aggregation and compare runtime."
        ),
    },
    "supervised versus unsupervised modeling": {
        "concept": (
            "Supervised learning uses labeled outcomes, unsupervised learning finds patterns.\n\n"
            "- Supervised: predict a target (classification, regression).\n"
            "- Unsupervised: discover structure (clustering, dimensionality reduction).\n"
            "- Choose based on whether labels exist and the decision you need to make."
        ),
        "example": (
            "We fit a classifier and contrast it with clustering on the same features."
        ),
        "python": (
            "from sklearn.datasets import load_iris\n"
            "from sklearn.cluster import KMeans\n"
            "from sklearn.linear_model import LogisticRegression\n\n"
            "data = load_iris()\n"
            "X, y = data.data, data.target\n\n"
            "clf = LogisticRegression(max_iter=200).fit(X, y)\n"
            "clusters = KMeans(n_clusters=3, n_init=10).fit_predict(X)\n"
            "print(\"classifier accuracy\", clf.score(X, y))\n"
            "print(\"cluster labels\", clusters[:5])"
        ),
        "exercise": (
            "List three problems you would solve with supervised learning and three you "
            "would solve with unsupervised learning."
        ),
    },
    "rolling vs expanding windows in pandas": {
        "concept": (
            "Rolling windows look at a fixed-size slice; expanding windows grow over time.\n\n"
            "- Rolling: good for local trends and volatility.\n"
            "- Expanding: good for cumulative baselines.\n"
            "- Choose window size based on the signal you want to smooth."
        ),
        "example": (
            "We compare rolling and expanding means over a simple series."
        ),
        "python": (
            "import pandas as pd\n\n"
            "s = pd.Series([2, 4, 6, 8, 10, 12])\n"
            "rolling_mean = s.rolling(window=3).mean()\n"
            "expanding_mean = s.expanding().mean()\n"
            "print(rolling_mean)\n"
            "print(expanding_mean)"
        ),
        "exercise": (
            "Pick a time series and compute a rolling mean with two different windows. "
            "Describe how the choice changes the pattern."
        ),
    },
}


def _generic_template(topic: str) -> dict[str, str]:
    return {
        "concept": (
            f"Focus on the core idea of {topic} and why it matters.\n\n"
            "- Define the key term in one sentence.\n"
            "- Name a common use case.\n"
            "- Note one tradeoff or pitfall."
        ),
        "example": (
            f"Walk through a small example that applies {topic} to a realistic scenario."
        ),
        "python": (
            "# Replace with your own data and steps.\n"
            "data = [1, 2, 3, 4]\n"
            "result = [value * 2 for value in data]\n"
            "print(result)"
        ),
        "exercise": (
            f"Write a short example that applies {topic} to a dataset you care about. "
            "Summarize the result in two sentences."
        ),
    }


def _with_level_guidance(content: str, level: str, section: str) -> str:
    guidance = _LEVEL_GUIDANCE.get(level, {}).get(section)
    if not guidance:
        return content
    return f"{content}\n\n{guidance}"


def build_static_lesson(topic: str, level: str) -> LessonResponse:
    """Return a deterministic, static lesson response."""
    normalized = topic.strip().lower()
    template = _STATIC_TEMPLATES.get(normalized) or _generic_template(topic)
    concept_text = _with_level_guidance(template["concept"], level, "concept")
    exercise_text = _with_level_guidance(template["exercise"], level, "exercise")
    minutes = _SECTION_MINUTES.get(level, _SECTION_MINUTES["beginner"])

    sections = [
        LessonSection(
            id="concept",
            title="Core idea",
            minutes=minutes["concept"],
            content_markdown=render_blocks_to_markdown(
                [ContentBlock(type="text", content=concept_text)]
            ),
        ),
        LessonSection(
            id="example",
            title="Worked example",
            minutes=minutes["example"],
            content_markdown=render_blocks_to_markdown(
                [
                    ContentBlock(type="text", content=template["example"]),
                    ContentBlock(type="python", content=template["python"]),
                ]
            ),
        ),
        LessonSection(
            id="exercise",
            title="Try it yourself",
            minutes=minutes["exercise"],
            content_markdown=render_blocks_to_markdown(
                [ContentBlock(type="exercise", content=exercise_text)]
            ),
        ),
    ]

    return LessonResponse(
        objective=f"Learn {topic} at a {level} level in 15 minutes.",
        total_minutes=15,
        sections=sections,
    )
