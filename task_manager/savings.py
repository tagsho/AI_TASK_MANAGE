"""Savings and calorie tracking utilities for the restraint app prototype."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Dict, Iterable, List, Optional, Sequence
import math


@dataclass(frozen=True)
class CategoryPreset:
    """Represents a purchasable item that users might resist buying."""

    name: str
    price: float
    calories: float

    def feedback(self) -> tuple[float, float]:
        """Return the savings (yen) and calorie reduction for a single restraint."""

        return self.price, self.calories


@dataclass(frozen=True)
class RestraintRecord:
    """Single restraint action recorded by the tracker."""

    category: CategoryPreset
    timestamp: datetime

    @property
    def saved_amount(self) -> float:
        return self.category.price

    @property
    def calories_reduced(self) -> float:
        return self.category.calories


@dataclass(frozen=True)
class InstantFeedback:
    """Information returned after a restraint has been logged."""

    saved_amount: float
    calories_reduced: float
    total_saved: float
    total_calories: float


@dataclass(frozen=True)
class DailySummary:
    """Aggregated savings and calories for a single day."""

    date: date
    saved_amount: float
    calories_reduced: float


@dataclass(frozen=True)
class RewardGoal:
    """User defined goal that converts savings into a reward."""

    name: str
    target_amount: float


@dataclass(frozen=True)
class RewardProgress:
    """Progress information for a configured reward goal."""

    goal: RewardGoal
    current_amount: float
    remaining_amount: float
    estimated_actions: Optional[int]


class SavingsDietTracker:
    """Core domain service for the savings x diet prototype."""

    DEFAULT_CATEGORIES: Sequence[CategoryPreset] = (
        CategoryPreset("お菓子", 150.0, 200.0),
        CategoryPreset("ジュース", 120.0, 150.0),
        CategoryPreset("スイーツ", 400.0, 350.0),
    )

    def __init__(self, categories: Optional[Iterable[CategoryPreset]] = None) -> None:
        presets = categories if categories is not None else self.DEFAULT_CATEGORIES
        self._categories: Dict[str, CategoryPreset] = {preset.name: preset for preset in presets}
        if not self._categories:
            raise ValueError("カテゴリが1つ以上必要です。")
        self._records: List[RestraintRecord] = []
        self._reward_goal: Optional[RewardGoal] = None

    @property
    def categories(self) -> Dict[str, CategoryPreset]:
        """Return a mapping of available preset categories."""

        return dict(self._categories)

    def add_category(self, preset: CategoryPreset) -> None:
        """Register an additional preset category."""

        self._categories[preset.name] = preset

    def register_restraint(
        self,
        category_name: str,
        *,
        when: Optional[datetime | date | str] = None,
    ) -> InstantFeedback:
        """Register that a user resisted a purchase for the given category."""

        if category_name not in self._categories:
            raise ValueError(f"カテゴリ '{category_name}' は登録されていません。")
        category = self._categories[category_name]
        timestamp = self._normalise_timestamp(when)
        record = RestraintRecord(category=category, timestamp=timestamp)
        self._records.append(record)

        total_saved, total_calories = self._totals()
        saved, calories = category.feedback()
        return InstantFeedback(
            saved_amount=saved,
            calories_reduced=calories,
            total_saved=total_saved,
            total_calories=total_calories,
        )

    def _normalise_timestamp(
        self, when: Optional[datetime | date | str]
    ) -> datetime:
        if when is None:
            return datetime.now(timezone.utc)
        if isinstance(when, datetime):
            return when if when.tzinfo is not None else when.replace(tzinfo=timezone.utc)
        if isinstance(when, date):
            return datetime.combine(when, datetime.min.time(), tzinfo=timezone.utc)
        if isinstance(when, str):
            try:
                parsed = datetime.fromisoformat(when)
            except ValueError as exc:
                raise ValueError("when は ISO 8601 形式で指定してください。") from exc
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        raise TypeError("when には datetime, date, str, None のいずれかを指定してください。")

    def _totals(self) -> tuple[float, float]:
        total_saved = sum(record.saved_amount for record in self._records)
        total_calories = sum(record.calories_reduced for record in self._records)
        return total_saved, total_calories

    def totals(self) -> InstantFeedback:
        """Return the cumulative savings and calories."""

        total_saved, total_calories = self._totals()
        return InstantFeedback(
            saved_amount=0.0,
            calories_reduced=0.0,
            total_saved=total_saved,
            total_calories=total_calories,
        )

    def monthly_breakdown(self, year: int, month: int) -> List[DailySummary]:
        """Aggregate savings and calories per day for the requested month."""

        aggregates: Dict[date, DailySummary] = {}
        for record in self._records:
            record_date = record.timestamp.astimezone(timezone.utc).date()
            if record_date.year != year or record_date.month != month:
                continue
            if record_date not in aggregates:
                aggregates[record_date] = DailySummary(
                    date=record_date, saved_amount=0.0, calories_reduced=0.0
                )
            summary = aggregates[record_date]
            aggregates[record_date] = DailySummary(
                date=summary.date,
                saved_amount=summary.saved_amount + record.saved_amount,
                calories_reduced=summary.calories_reduced + record.calories_reduced,
            )
        return [aggregates[key] for key in sorted(aggregates)]

    def set_reward_goal(
        self,
        name: str,
        target_amount: float,
        *,
        reference_category: Optional[str] = None,
    ) -> RewardProgress:
        if target_amount <= 0:
            raise ValueError("目標金額は正の数値で指定してください。")
        self._reward_goal = RewardGoal(name=name, target_amount=target_amount)
        return self.reward_progress(reference_category=reference_category)

    def reward_progress(
        self, *, reference_category: Optional[str] = None
    ) -> RewardProgress:
        if self._reward_goal is None:
            raise ValueError("ご褒美目標が設定されていません。")
        current_saved, _ = self._totals()
        remaining = max(self._reward_goal.target_amount - current_saved, 0.0)
        estimated_actions: Optional[int]

        per_action_value: Optional[float] = None
        if reference_category is not None:
            if reference_category not in self._categories:
                raise ValueError(f"カテゴリ '{reference_category}' は登録されていません。")
            per_action_value = self._categories[reference_category].price
        elif self._records:
            per_action_value = (
                sum(record.saved_amount for record in self._records) / len(self._records)
            )

        if per_action_value and per_action_value > 0:
            estimated_actions = math.ceil(remaining / per_action_value) if remaining else 0
        else:
            estimated_actions = None

        return RewardProgress(
            goal=self._reward_goal,
            current_amount=current_saved,
            remaining_amount=remaining,
            estimated_actions=estimated_actions,
        )

    @property
    def reward_goal(self) -> Optional[RewardGoal]:
        return self._reward_goal
