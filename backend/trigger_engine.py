"""
Stochastic Trigger Engine
Implements Variable Interval (VI) scheduling to prevent habituation
"""

import random
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict
from enum import Enum


class TriggerState(Enum):
    PENDING = "pending"
    FIRED = "fired"
    DISMISSED = "dismissed"
    COMPLETED = "completed"
    SNOOZED = "snoozed"


@dataclass
class TriggerConfig:
    """Configuration for a habit's trigger pattern"""
    habit_id: str
    mean_interval_minutes: int  # Average time between triggers
    std_dev_minutes: int  # Variability to prevent pattern detection
    min_cooldown_minutes: int  # Minimum gap to prevent annoyance
    max_daily_triggers: int  # Daily limit
    active_hours_start: int = 7  # e.g., 7 AM
    active_hours_end: int = 22  # e.g., 10 PM


@dataclass
class TriggerEvent:
    """Record of a trigger event"""
    trigger_id: str
    habit_id: str
    scheduled_time: datetime
    actual_fire_time: Optional[datetime]
    state: TriggerState
    context: Dict
    variant_id: str
    user_response_time: Optional[float] = None  # Seconds to action


class StochasticTriggerEngine:
    """
    Generates unpredictable trigger schedules using Variable Interval (VI)
    reinforcement scheduling to maintain novelty and prevent habituation.
    """
    
    def __init__(self, config: TriggerConfig):
        self.config = config
        self.trigger_history: List[TriggerEvent] = []
        self.last_trigger_time: Optional[datetime] = None
        self.daily_trigger_count = 0
        self.last_reset_date = datetime.now().date()
    
    def calculate_next_trigger(self, current_time: Optional[datetime] = None) -> datetime:
        """
        Calculate the next trigger time using VI schedule with multiple safeguards:
        1. Normal distribution around mean interval
        2. Minimum cooldown enforcement
        3. Daily limit check
        4. Active hours boundary
        5. Temporal jitter to prevent hourly patterns
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Reset daily counter if new day
        if current_time.date() > self.last_reset_date:
            self.daily_trigger_count = 0
            self.last_reset_date = current_time.date()
        
        # Check daily limit
        if self.daily_trigger_count >= self.config.max_daily_triggers:
            # Schedule for tomorrow's start
            next_day = current_time + timedelta(days=1)
            return next_day.replace(
                hour=self.config.active_hours_start,
                minute=random.randint(0, 59),
                second=0
            )
        
        # Generate interval using normal distribution
        base_interval = max(
            self.config.min_cooldown_minutes,
            random.normalvariate(
                self.config.mean_interval_minutes,
                self.config.std_dev_minutes
            )
        )
        
        # Calculate base next time
        if self.last_trigger_time:
            next_time = self.last_trigger_time + timedelta(minutes=base_interval)
        else:
            next_time = current_time + timedelta(minutes=base_interval)
        
        # Add temporal jitter (±15 minutes) to prevent hourly patterns
        jitter_minutes = random.uniform(-15, 15)
        next_time += timedelta(minutes=jitter_minutes)
        
        # Ensure within active hours
        next_time = self._constrain_to_active_hours(next_time)
        
        return next_time
    
    def _constrain_to_active_hours(self, target_time: datetime) -> datetime:
        """Ensure trigger falls within configured active hours"""
        if target_time.hour < self.config.active_hours_start:
            # Too early, move to start of active window
            return target_time.replace(
                hour=self.config.active_hours_start,
                minute=random.randint(0, 59)
            )
        elif target_time.hour >= self.config.active_hours_end:
            # Too late, move to tomorrow's start
            next_day = target_time + timedelta(days=1)
            return next_day.replace(
                hour=self.config.active_hours_start,
                minute=random.randint(0, 59)
            )
        return target_time
    
    def should_trigger_now(
        self,
        current_time: Optional[datetime] = None,
        scheduled_time: Optional[datetime] = None
    ) -> bool:
        """
        Check if trigger should fire now.
        Uses a window approach: trigger is valid for ±10 minutes around scheduled time
        """
        if current_time is None:
            current_time = datetime.now()
        
        if scheduled_time is None:
            return False
        
        # Check if within trigger window (±10 minutes)
        time_diff = abs((current_time - scheduled_time).total_seconds())
        return time_diff <= 600  # 10 minutes in seconds
    
    def record_trigger(
        self,
        trigger_event: TriggerEvent,
        update_last_trigger: bool = True
    ):
        """Record trigger event and update state"""
        self.trigger_history.append(trigger_event)
        
        if update_last_trigger and trigger_event.state == TriggerState.FIRED:
            self.last_trigger_time = trigger_event.actual_fire_time
            self.daily_trigger_count += 1
    
    def get_engagement_metrics(self, window_days: int = 7) -> Dict:
        """Calculate engagement metrics for recent history"""
        cutoff_date = datetime.now() - timedelta(days=window_days)
        recent_triggers = [
            t for t in self.trigger_history
            if t.actual_fire_time and t.actual_fire_time >= cutoff_date
        ]
        
        if not recent_triggers:
            return {
                "total_triggers": 0,
                "engagement_rate": 0.0,
                "dismissal_rate": 0.0,
                "avg_response_time": None
            }
        
        total = len(recent_triggers)
        completed = sum(1 for t in recent_triggers if t.state == TriggerState.COMPLETED)
        dismissed = sum(1 for t in recent_triggers if t.state == TriggerState.DISMISSED)
        
        response_times = [
            t.user_response_time for t in recent_triggers
            if t.user_response_time is not None
        ]
        
        return {
            "total_triggers": total,
            "engagement_rate": completed / total if total > 0 else 0.0,
            "dismissal_rate": dismissed / total if total > 0 else 0.0,
            "avg_response_time": sum(response_times) / len(response_times) if response_times else None,
            "completion_count": completed
        }
    
    def detect_fatigue(self, threshold: float = 0.25) -> bool:
        """
        Detect nudge fatigue by analyzing dismissal rate.
        Returns True if user is showing signs of annoyance.
        """
        metrics = self.get_engagement_metrics(window_days=7)
        
        # Fatigue indicators:
        # 1. High dismissal rate (>25%)
        # 2. Low engagement rate (<30%)
        # 3. Minimum sample size met (at least 10 triggers)
        
        if metrics["total_triggers"] < 10:
            return False  # Not enough data
        
        return (
            metrics["dismissal_rate"] > threshold or
            metrics["engagement_rate"] < 0.30
        )
    
    def adjust_for_fatigue(self):
        """Automatically reduce frequency if fatigue detected"""
        if self.detect_fatigue():
            # Increase interval by 40%
            self.config.mean_interval_minutes = int(
                self.config.mean_interval_minutes * 1.4
            )
            # Reduce daily max by 2
            self.config.max_daily_triggers = max(
                2,
                self.config.max_daily_triggers - 2
            )
            print(f"⚠️ Fatigue detected. Adjusted intervals to {self.config.mean_interval_minutes}min")
    
    def export_state(self) -> Dict:
        """Export engine state for persistence"""
        return {
            "config": asdict(self.config),
            "last_trigger_time": self.last_trigger_time.isoformat() if self.last_trigger_time else None,
            "daily_trigger_count": self.daily_trigger_count,
            "last_reset_date": self.last_reset_date.isoformat(),
            "trigger_history": [
                {
                    **asdict(t),
                    "scheduled_time": t.scheduled_time.isoformat(),
                    "actual_fire_time": t.actual_fire_time.isoformat() if t.actual_fire_time else None,
                    "state": t.state.value
                }
                for t in self.trigger_history[-100:]  # Keep last 100 events
            ]
        }
    
    @classmethod
    def load_state(cls, state_dict: Dict) -> 'StochasticTriggerEngine':
        """Load engine state from persistence"""
        config = TriggerConfig(**state_dict["config"])
        engine = cls(config)
        
        if state_dict["last_trigger_time"]:
            engine.last_trigger_time = datetime.fromisoformat(state_dict["last_trigger_time"])
        
        engine.daily_trigger_count = state_dict["daily_trigger_count"]
        engine.last_reset_date = datetime.fromisoformat(state_dict["last_reset_date"]).date()
        
        # Reconstruct trigger history
        for event_dict in state_dict["trigger_history"]:
            event = TriggerEvent(
                trigger_id=event_dict["trigger_id"],
                habit_id=event_dict["habit_id"],
                scheduled_time=datetime.fromisoformat(event_dict["scheduled_time"]),
                actual_fire_time=datetime.fromisoformat(event_dict["actual_fire_time"]) if event_dict["actual_fire_time"] else None,
                state=TriggerState(event_dict["state"]),
                context=event_dict["context"],
                variant_id=event_dict["variant_id"],
                user_response_time=event_dict.get("user_response_time")
            )
            engine.trigger_history.append(event)
        
        return engine


# Example usage and testing
if __name__ == "__main__":
    # Create a meditation habit trigger
    meditation_config = TriggerConfig(
        habit_id="meditation_001",
        mean_interval_minutes=180,  # ~3 hours average
        std_dev_minutes=45,
        min_cooldown_minutes=60,  # At least 1 hour between
        max_daily_triggers=4,  # Max 4 times per day
        active_hours_start=7,
        active_hours_end=22
    )
    
    engine = StochasticTriggerEngine(meditation_config)
    
    # Simulate trigger schedule for next 7 days
    print("📅 Simulated Trigger Schedule (Next 7 Days)\n")
    
    current_time = datetime.now()
    scheduled_triggers = []
    
    for _ in range(20):  # Generate 20 triggers
        next_trigger = engine.calculate_next_trigger(current_time)
        scheduled_triggers.append(next_trigger)
        
        # Simulate trigger firing
        trigger_event = TriggerEvent(
            trigger_id=f"trigger_{len(scheduled_triggers)}",
            habit_id=meditation_config.habit_id,
            scheduled_time=next_trigger,
            actual_fire_time=next_trigger,
            state=TriggerState.FIRED,
            context={"location": "home", "focus_mode": False},
            variant_id=f"variant_{random.randint(1, 5)}"
        )
        
        engine.record_trigger(trigger_event)
        current_time = next_trigger
        
        # Simulate user response (70% engagement for this example)
        if random.random() < 0.7:
            trigger_event.state = TriggerState.COMPLETED
            trigger_event.user_response_time = random.uniform(30, 300)  # 30s to 5min
        else:
            trigger_event.state = TriggerState.DISMISSED
    
    # Display schedule
    for i, trigger_time in enumerate(scheduled_triggers[:10], 1):
        day_name = trigger_time.strftime("%A")
        time_str = trigger_time.strftime("%I:%M %p")
        print(f"{i:2d}. {day_name:9s} at {time_str}")
    
    # Show metrics
    print("\n📊 Engagement Metrics\n")
    metrics = engine.get_engagement_metrics()
    print(f"Total Triggers:    {metrics['total_triggers']}")
    print(f"Engagement Rate:   {metrics['engagement_rate']:.1%}")
    print(f"Dismissal Rate:    {metrics['dismissal_rate']:.1%}")
    if metrics['avg_response_time']:
        print(f"Avg Response Time: {metrics['avg_response_time']:.0f} seconds")
    
    # Check for fatigue
    print(f"\nFatigue Detected:  {'⚠️ Yes' if engine.detect_fatigue() else '✅ No'}")
    
    # Export state for persistence
    state = engine.export_state()
    with open('engine_state.json', 'w') as f:
        json.dump(state, f, indent=2)
    
    print("\n💾 State exported to engine_state.json")
