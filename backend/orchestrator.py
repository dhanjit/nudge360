"""
Nudge Orchestrator
Integrates trigger engine, context gate, and widget system
"""

import json
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict

from trigger_engine import StochasticTriggerEngine, TriggerConfig, TriggerEvent, TriggerState
from widget_variants import WidgetVariantGenerator, AdaptiveMessageGenerator
from context_gate import ContextGate, UserContext, Geofence, ContextRule, ContextRuleTemplates


@dataclass
class NudgeDecision:
    """Result of orchestrator decision-making"""
    should_trigger: bool
    habit_id: Optional[str]
    variant: Optional[Dict]
    presentation_style: Optional[str]
    target_device: Optional[str]
    reason: Optional[str]  # Why was this decision made (or not)
    scheduled_time: Optional[datetime]
    context_snapshot: Optional[Dict]


class DeviceType:
    PHONE = "phone"
    DESKTOP = "desktop"
    WATCH = "watch"
    TABLET = "tablet"


class NudgeOrchestrator:
    """
    Central brain of the 360° Nudging Framework
    
    Responsibilities:
    1. Coordinate trigger timing (Stochastic Engine)
    2. Validate context eligibility (Context Gate)
    3. Select visual presentation (Widget Variants)
    4. Route to appropriate device
    5. Record outcomes for learning
    """
    
    def __init__(self):
        self.trigger_engines: Dict[str, StochasticTriggerEngine] = {}
        self.variant_generators: Dict[str, WidgetVariantGenerator] = {}
        self.context_gate = ContextGate()
        self.message_generator = AdaptiveMessageGenerator()
        
        # Track recent variants to avoid immediate repeats
        self.recent_variants: Dict[str, List[str]] = {}  # habit_id -> list of variant_ids
        self.variant_history_size = 5
        
        # Device state (would come from real-time sync in production)
        self.active_devices: List[str] = [DeviceType.PHONE]
    
    def register_habit(
        self,
        habit_id: str,
        category: str,
        trigger_config: TriggerConfig,
        context_rule: ContextRule
    ):
        """Register a new habit with all subsystems"""
        # Initialize trigger engine for this habit
        self.trigger_engines[habit_id] = StochasticTriggerEngine(trigger_config)
        
        # Initialize variant generator
        self.variant_generators[habit_id] = WidgetVariantGenerator(habit_id, category)
        self.variant_generators[habit_id].generate_variant_pool(count=10)
        
        # Register context rules
        self.context_gate.register_rule(context_rule)
        
        # Initialize variant history tracker
        self.recent_variants[habit_id] = []
        
        print(f"✅ Registered habit: {habit_id}")
    
    def evaluate_trigger(
        self,
        habit_id: str,
        current_context: UserContext,
        current_time: Optional[datetime] = None
    ) -> NudgeDecision:
        """
        Main decision function: Should we trigger this habit now?
        
        Decision Flow:
        1. Check if scheduled time window is active
        2. Validate context eligibility
        3. Select variant and presentation style
        4. Choose target device
        5. Record decision
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Get trigger engine for this habit
        engine = self.trigger_engines.get(habit_id)
        if not engine:
            return NudgeDecision(
                should_trigger=False,
                habit_id=habit_id,
                variant=None,
                presentation_style=None,
                target_device=None,
                reason="Habit not registered",
                scheduled_time=None,
                context_snapshot=None
            )
        
        # Check if we're in a trigger window
        # (In production, this would check against a scheduled trigger)
        if not engine.should_trigger_now(current_time):
            next_trigger = engine.calculate_next_trigger(current_time)
            return NudgeDecision(
                should_trigger=False,
                habit_id=habit_id,
                variant=None,
                presentation_style=None,
                target_device=None,
                reason=f"Not in trigger window (next: {next_trigger.strftime('%I:%M %p')})",
                scheduled_time=next_trigger,
                context_snapshot=None
            )
        
        # Validate context
        can_trigger, context_reason, context_metadata = self.context_gate.can_trigger(
            habit_id,
            current_context
        )
        
        if not can_trigger:
            return NudgeDecision(
                should_trigger=False,
                habit_id=habit_id,
                variant=None,
                presentation_style=None,
                target_device=None,
                reason=f"Context not eligible: {context_reason}",
                scheduled_time=None,
                context_snapshot=self._serialize_context(current_context)
            )
        
        # Select variant
        variant_generator = self.variant_generators[habit_id]
        
        # Get contextual variant (considering time, mood, etc.)
        context_dict = {
            "hour": current_context.time_of_day,
            "focus_mode": current_context.focus_mode != current_context.focus_mode.NONE,
            "screen_on": current_context.screen_on
        }
        
        variant = variant_generator.get_contextual_variant(context_dict)
        
        # Avoid recent variants
        if variant.variant_id in self.recent_variants[habit_id]:
            # Try to get a different one
            variant = variant_generator.select_random_variant(
                exclude_recent=self.recent_variants[habit_id]
            )
        
        # Update recent variants
        self.recent_variants[habit_id].append(variant.variant_id)
        if len(self.recent_variants[habit_id]) > self.variant_history_size:
            self.recent_variants[habit_id].pop(0)
        
        # Enhance message with context
        enhanced_message = self.message_generator.enhance_with_context(
            variant.message,
            context_dict
        )
        variant_dict = variant.to_dict()
        variant_dict['message'] = enhanced_message
        
        # Select presentation style based on attention level
        presentation_style = context_metadata.get('presentation_style', 'standard')
        
        # Select target device
        target_device = self._select_target_device(current_context)
        
        # Success! Create trigger event
        trigger_event = TriggerEvent(
            trigger_id=f"trigger_{habit_id}_{int(current_time.timestamp())}",
            habit_id=habit_id,
            scheduled_time=current_time,
            actual_fire_time=current_time,
            state=TriggerState.FIRED,
            context=self._serialize_context(current_context),
            variant_id=variant.variant_id
        )
        
        engine.record_trigger(trigger_event)
        
        return NudgeDecision(
            should_trigger=True,
            habit_id=habit_id,
            variant=variant_dict,
            presentation_style=presentation_style,
            target_device=target_device,
            reason="All checks passed",
            scheduled_time=current_time,
            context_snapshot=self._serialize_context(current_context)
        )
    
    def evaluate_all_habits(self, current_context: UserContext) -> List[NudgeDecision]:
        """
        Check all registered habits and return triggerable ones
        
        Useful for batch evaluation (e.g., when device wakes up)
        """
        decisions = []
        
        for habit_id in self.trigger_engines.keys():
            decision = self.evaluate_trigger(habit_id, current_context)
            decisions.append(decision)
        
        return decisions
    
    def record_user_response(
        self,
        habit_id: str,
        trigger_id: str,
        action: str,  # "completed", "dismissed", "snoozed"
        response_time_seconds: Optional[float] = None
    ):
        """
        Record how user responded to a trigger
        
        This data is used for:
        1. Engagement metrics
        2. Fatigue detection
        3. Adaptive learning (future enhancement)
        """
        engine = self.trigger_engines.get(habit_id)
        if not engine:
            return
        
        # Find the trigger event
        for event in engine.trigger_history:
            if event.trigger_id == trigger_id:
                if action == "completed":
                    event.state = TriggerState.COMPLETED
                elif action == "dismissed":
                    event.state = TriggerState.DISMISSED
                elif action == "snoozed":
                    event.state = TriggerState.SNOOZED
                
                event.user_response_time = response_time_seconds
                break
        
        # Check for fatigue and auto-adjust
        engine.adjust_for_fatigue()
    
    def get_dashboard_metrics(self, habit_id: Optional[str] = None) -> Dict:
        """
        Generate user-facing metrics dashboard
        
        Shows engagement, streaks, optimal times, etc.
        """
        if habit_id:
            engine = self.trigger_engines.get(habit_id)
            if not engine:
                return {}
            
            metrics = engine.get_engagement_metrics(window_days=7)
            
            return {
                "habit_id": habit_id,
                "last_7_days": metrics,
                "fatigue_detected": engine.detect_fatigue(),
                "current_streak": self._calculate_streak(engine),
                "total_completions": sum(
                    1 for e in engine.trigger_history
                    if e.state == TriggerState.COMPLETED
                )
            }
        else:
            # Aggregate across all habits
            all_metrics = {}
            for hid in self.trigger_engines.keys():
                all_metrics[hid] = self.get_dashboard_metrics(hid)
            
            return all_metrics
    
    def _select_target_device(self, context: UserContext) -> str:
        """
        Choose which device should display the nudge
        
        Priority:
        1. Device currently in use (screen on)
        2. Context-appropriate device (desk = desktop, walking = watch)
        3. Fallback to phone
        """
        # Simulate device selection logic
        # In production, this would check real device states
        
        if context.screen_on:
            # User is actively using a device
            if context.activity.value == "stationary" and context.connected_to_wifi:
                return DeviceType.DESKTOP if DeviceType.DESKTOP in self.active_devices else DeviceType.PHONE
            else:
                return DeviceType.PHONE
        
        if context.activity.value in ["walking", "running"]:
            return DeviceType.WATCH if DeviceType.WATCH in self.active_devices else DeviceType.PHONE
        
        return DeviceType.PHONE
    
    def _serialize_context(self, context: UserContext) -> Dict:
        """Convert context to serializable dict"""
        return {
            "location": {
                "lat": context.location.latitude,
                "lon": context.location.longitude,
                "accuracy": context.location.accuracy_meters
            },
            "activity": context.activity.value,
            "focus_mode": context.focus_mode.value,
            "screen_on": context.screen_on,
            "battery": context.battery_level,
            "time": context.time_of_day,
            "day": context.day_of_week
        }
    
    def _calculate_streak(self, engine: StochasticTriggerEngine) -> int:
        """Calculate current completion streak (consecutive days)"""
        # Sort completions by date
        completions = [
            e for e in engine.trigger_history
            if e.state == TriggerState.COMPLETED and e.actual_fire_time
        ]
        
        if not completions:
            return 0
        
        completions.sort(key=lambda x: x.actual_fire_time, reverse=True)
        
        # Count consecutive days
        streak = 0
        current_date = datetime.now().date()
        
        for completion in completions:
            completion_date = completion.actual_fire_time.date()
            
            if completion_date == current_date:
                streak += 1
                current_date -= timedelta(days=1)
            elif completion_date == current_date - timedelta(days=1):
                streak += 1
                current_date = completion_date - timedelta(days=1)
            else:
                break
        
        return streak
    
    def export_state(self) -> Dict:
        """Export complete system state for persistence"""
        return {
            "trigger_engines": {
                habit_id: engine.export_state()
                for habit_id, engine in self.trigger_engines.items()
            },
            "recent_variants": self.recent_variants,
            "active_devices": self.active_devices
        }
    
    def save_state(self, filepath: str):
        """Save state to file"""
        state = self.export_state()
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)


# Example: Complete system setup and simulation
if __name__ == "__main__":
    import time
    
    print("🎯 360° Nudging Framework - Full System Demo\n")
    print("=" * 60)
    
    # Initialize orchestrator
    orchestrator = NudgeOrchestrator()
    
    # Setup geofences
    from context_gate import Location
    
    home_fence = Geofence(
        fence_id="home",
        name="Home",
        center=Location(37.7749, -122.4194, 10.0, time.time()),
        radius_meters=100,
        habit_ids=["meditation"]
    )
    orchestrator.context_gate.register_geofence(home_fence)
    
    # Register meditation habit
    meditation_config = TriggerConfig(
        habit_id="meditation",
        mean_interval_minutes=180,
        std_dev_minutes=45,
        min_cooldown_minutes=60,
        max_daily_triggers=4,
        active_hours_start=7,
        active_hours_end=22
    )
    
    meditation_rule = ContextRuleTemplates.home_based_habit("meditation", "home")
    
    orchestrator.register_habit(
        habit_id="meditation",
        category="meditation",
        trigger_config=meditation_config,
        context_rule=meditation_rule
    )
    
    print("\n" + "=" * 60)
    print("Simulating user behavior over 24 hours...\n")
    
    # Simulate a day
    from context_gate import Location, ActivityState, FocusMode
    
    simulation_time = datetime.now().replace(hour=8, minute=0)
    
    for hour in range(8, 23):  # 8 AM to 11 PM
        # Create context for this hour
        context = UserContext(
            location=Location(37.7749, -122.4194, 10.0, time.time()),  # At home
            activity=ActivityState.STATIONARY if hour < 17 else ActivityState.STATIONARY,
            focus_mode=FocusMode.WORK if 9 <= hour < 17 else FocusMode.NONE,
            screen_on=True,
            battery_level=90 - (hour - 8) * 5,
            in_call=False,
            connected_to_wifi=True,
            time_of_day=hour,
            day_of_week=2  # Wednesday
        )
        
        # Check if trigger should fire
        decision = orchestrator.evaluate_trigger("meditation", context, simulation_time)
        
        if decision.should_trigger:
            print(f"⏰ {simulation_time.strftime('%I:%M %p')} - TRIGGER FIRED")
            print(f"   Variant: {decision.variant['emoji']} {decision.variant['message']}")
            print(f"   Style: {decision.presentation_style}")
            print(f"   Device: {decision.target_device}")
            print(f"   Layout: {decision.variant['layout']}")
            print(f"   Colors: {decision.variant['colors']['gradient']}")
            
            # Simulate user response (70% completion rate)
            if random.random() < 0.7:
                print("   ✅ User completed")
                orchestrator.record_user_response(
                    "meditation",
                    f"trigger_meditation_{int(simulation_time.timestamp())}",
                    "completed",
                    response_time_seconds=random.uniform(30, 180)
                )
            else:
                print("   ❌ User dismissed")
                orchestrator.record_user_response(
                    "meditation",
                    f"trigger_meditation_{int(simulation_time.timestamp())}",
                    "dismissed"
                )
            print()
        
        simulation_time += timedelta(hours=1)
    
    # Show metrics
    print("=" * 60)
    print("\n📊 Session Metrics:\n")
    
    metrics = orchestrator.get_dashboard_metrics("meditation")
    
    print(f"Total Triggers: {metrics['last_7_days']['total_triggers']}")
    print(f"Engagement Rate: {metrics['last_7_days']['engagement_rate']:.1%}")
    print(f"Dismissal Rate: {metrics['last_7_days']['dismissal_rate']:.1%}")
    print(f"Completions: {metrics['last_7_days'].get('completion_count', 0)}")
    if metrics['last_7_days'].get('avg_response_time'):
        print(f"Avg Response: {metrics['last_7_days']['avg_response_time']:.0f}s")
    print(f"Fatigue: {'⚠️ Detected' if metrics['fatigue_detected'] else '✅ Normal'}")
    print(f"Streak: {metrics['current_streak']} days")
    
    # Save state
    orchestrator.save_state('orchestrator_state.json')
    print("\n💾 System state saved")
    
    print("\n" + "=" * 60)
    print("✅ Full system demonstration complete!")
