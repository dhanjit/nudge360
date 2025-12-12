"""
Context Gating System
Ensures triggers fire only when user is in appropriate context
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
from enum import Enum
import math


class ActivityState(Enum):
    STATIONARY = "stationary"
    WALKING = "walking"
    RUNNING = "running"
    CYCLING = "cycling"
    DRIVING = "driving"
    UNKNOWN = "unknown"


class FocusMode(Enum):
    NONE = "none"
    WORK = "work"
    PERSONAL = "personal"
    SLEEP = "sleep"
    FITNESS = "fitness"
    DRIVING_FOCUS = "driving"
    CUSTOM = "custom"


@dataclass
class Location:
    """Geographic location"""
    latitude: float
    longitude: float
    accuracy_meters: float
    timestamp: float


@dataclass
class Geofence:
    """Circular geofence definition"""
    fence_id: str
    name: str
    center: Location
    radius_meters: float
    habit_ids: List[str]  # Which habits are eligible here
    
    def contains(self, location: Location) -> bool:
        """Check if location is within geofence"""
        distance = self._haversine_distance(
            self.center.latitude,
            self.center.longitude,
            location.latitude,
            location.longitude
        )
        return distance <= self.radius_meters
    
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in meters"""
        R = 6371000  # Earth's radius in meters
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_phi / 2) ** 2 +
             math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c


@dataclass
class UserContext:
    """Complete context snapshot"""
    location: Location
    activity: ActivityState
    focus_mode: FocusMode
    screen_on: bool
    battery_level: float
    in_call: bool
    connected_to_wifi: bool
    time_of_day: int  # Hour (0-23)
    day_of_week: int  # 0=Monday, 6=Sunday
    
    def is_interruptible(self) -> bool:
        """Check if user can be interrupted right now"""
        # Never interrupt if:
        # 1. Driving
        # 2. In a call
        # 3. Sleep focus mode
        # 4. Screen off for >30 min (likely sleeping/away)
        
        if self.activity == ActivityState.DRIVING:
            return False
        
        if self.in_call:
            return False
        
        if self.focus_mode == FocusMode.SLEEP:
            return False
        
        return True
    
    def get_attention_level(self) -> str:
        """Estimate user's available attention"""
        if not self.screen_on:
            return "minimal"  # Queue for later or use ambient cue
        
        if self.focus_mode in [FocusMode.WORK, FocusMode.DRIVING_FOCUS]:
            return "low"  # Use subtle, minimal presentation
        
        if self.activity in [ActivityState.WALKING, ActivityState.RUNNING]:
            return "moderate"  # Can see notifications but not interact deeply
        
        if self.activity == ActivityState.STATIONARY and self.screen_on:
            return "high"  # Full attention available
        
        return "moderate"


@dataclass
class ContextRule:
    """Rules for when a habit can be triggered"""
    habit_id: str
    
    # Location rules
    required_geofences: List[str]  # Must be in one of these
    blocked_geofences: List[str]  # Must NOT be in any of these
    
    # Activity rules
    allowed_activities: List[ActivityState]
    blocked_activities: List[ActivityState]
    
    # Focus mode rules
    allowed_focus_modes: List[FocusMode]
    blocked_focus_modes: List[FocusMode]
    
    # Time rules
    allowed_hours: List[int]  # e.g., [7, 8, 9, ..., 22]
    blocked_days: List[int]  # Days of week to skip
    
    # Device state rules
    require_screen_on: bool
    require_wifi: bool
    min_battery_level: float
    
    def is_satisfied(self, context: UserContext, active_geofences: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Check if all rules are satisfied
        
        Returns:
            (satisfied, reason_if_not)
        """
        # Location check
        if self.required_geofences:
            if not any(gf in active_geofences for gf in self.required_geofences):
                return False, f"Not in required location: {self.required_geofences}"
        
        if self.blocked_geofences:
            if any(gf in active_geofences for gf in self.blocked_geofences):
                return False, f"In blocked location: {self.blocked_geofences}"
        
        # Activity check
        if self.allowed_activities:
            if context.activity not in self.allowed_activities:
                return False, f"Activity {context.activity.value} not allowed"
        
        if self.blocked_activities:
            if context.activity in self.blocked_activities:
                return False, f"Activity {context.activity.value} is blocked"
        
        # Focus mode check
        if self.allowed_focus_modes:
            if context.focus_mode not in self.allowed_focus_modes:
                return False, f"Focus mode {context.focus_mode.value} not allowed"
        
        if self.blocked_focus_modes:
            if context.focus_mode in self.blocked_focus_modes:
                return False, f"Focus mode {context.focus_mode.value} is blocked"
        
        # Time check
        if self.allowed_hours:
            if context.time_of_day not in self.allowed_hours:
                return False, f"Hour {context.time_of_day} not in allowed window"
        
        if self.blocked_days:
            if context.day_of_week in self.blocked_days:
                return False, f"Day {context.day_of_week} is blocked"
        
        # Device state checks
        if self.require_screen_on and not context.screen_on:
            return False, "Screen is off"
        
        if self.require_wifi and not context.connected_to_wifi:
            return False, "Not connected to WiFi"
        
        if context.battery_level < self.min_battery_level:
            return False, f"Battery too low: {context.battery_level}%"
        
        # All checks passed
        return True, None


class ContextGate:
    """
    Main context evaluation system
    Decides whether a trigger should fire based on current context
    """
    
    def __init__(self):
        self.geofences: List[Geofence] = []
        self.rules: Dict[str, ContextRule] = {}  # habit_id -> rules
    
    def register_geofence(self, geofence: Geofence):
        """Add a geofence to the system"""
        self.geofences.append(geofence)
    
    def register_rule(self, rule: ContextRule):
        """Add context rules for a habit"""
        self.rules[rule.habit_id] = rule
    
    def get_active_geofences(self, location: Location) -> List[str]:
        """Get list of geofence IDs that contain the current location"""
        active = []
        for fence in self.geofences:
            if fence.contains(location):
                active.append(fence.fence_id)
        return active
    
    def can_trigger(self, habit_id: str, context: UserContext) -> Tuple[bool, Optional[str], Dict]:
        """
        Comprehensive check if habit can be triggered
        
        Returns:
            (can_trigger, reason_if_not, metadata)
        """
        # First, check if user is interruptible at all
        if not context.is_interruptible():
            return False, "User not interruptible (driving/call/sleep)", {}
        
        # Get active geofences
        active_geofences = self.get_active_geofences(context.location)
        
        # Check habit-specific rules
        if habit_id in self.rules:
            rule = self.rules[habit_id]
            satisfied, reason = rule.is_satisfied(context, active_geofences)
            
            if not satisfied:
                return False, reason, {}
        
        # Gather metadata for presentation
        metadata = {
            "attention_level": context.get_attention_level(),
            "active_geofences": active_geofences,
            "activity": context.activity.value,
            "focus_mode": context.focus_mode.value,
            "presentation_style": self._recommend_presentation_style(context)
        }
        
        return True, None, metadata
    
    def _recommend_presentation_style(self, context: UserContext) -> str:
        """Recommend how aggressive the nudge should be"""
        attention = context.get_attention_level()
        
        if attention == "minimal":
            return "ambient"  # Subtle visual cue only
        elif attention == "low":
            return "minimal"  # Icon + short text
        elif attention == "moderate":
            return "standard"  # Normal widget
        else:  # high
            return "rich"  # Can include more detail
    
    def get_eligible_habits(self, context: UserContext) -> List[Tuple[str, Dict]]:
        """
        Get all habits that can be triggered in current context
        
        Returns:
            List of (habit_id, metadata) tuples
        """
        eligible = []
        
        for habit_id in self.rules.keys():
            can_trigger, _, metadata = self.can_trigger(habit_id, context)
            if can_trigger:
                eligible.append((habit_id, metadata))
        
        return eligible


# Preset context rule templates
class ContextRuleTemplates:
    """Common rule patterns for different habit types"""
    
    @staticmethod
    def home_based_habit(habit_id: str, geofence_id: str) -> ContextRule:
        """Template for habits done at home (meditation, reading, etc.)"""
        return ContextRule(
            habit_id=habit_id,
            required_geofences=[geofence_id],
            blocked_geofences=[],
            allowed_activities=[ActivityState.STATIONARY, ActivityState.WALKING],
            blocked_activities=[ActivityState.DRIVING],
            allowed_focus_modes=list(FocusMode),
            blocked_focus_modes=[FocusMode.SLEEP, FocusMode.DRIVING_FOCUS],
            allowed_hours=list(range(7, 23)),  # 7 AM to 11 PM
            blocked_days=[],
            require_screen_on=False,
            require_wifi=False,
            min_battery_level=15.0
        )
    
    @staticmethod
    def gym_based_habit(habit_id: str, geofence_id: str) -> ContextRule:
        """Template for gym habits"""
        return ContextRule(
            habit_id=habit_id,
            required_geofences=[geofence_id],
            blocked_geofences=[],
            allowed_activities=[ActivityState.STATIONARY, ActivityState.WALKING],
            blocked_activities=[],
            allowed_focus_modes=[FocusMode.NONE, FocusMode.FITNESS],
            blocked_focus_modes=[FocusMode.WORK, FocusMode.SLEEP],
            allowed_hours=list(range(5, 23)),  # 5 AM to 11 PM
            blocked_days=[],
            require_screen_on=False,
            require_wifi=False,
            min_battery_level=20.0
        )
    
    @staticmethod
    def work_desk_habit(habit_id: str, geofence_id: str) -> ContextRule:
        """Template for work-related habits (posture check, hydration, etc.)"""
        return ContextRule(
            habit_id=habit_id,
            required_geofences=[geofence_id],
            blocked_geofences=[],
            allowed_activities=[ActivityState.STATIONARY],
            blocked_activities=[ActivityState.DRIVING],
            allowed_focus_modes=[FocusMode.NONE, FocusMode.WORK],
            blocked_focus_modes=[FocusMode.SLEEP],
            allowed_hours=list(range(8, 18)),  # Work hours
            blocked_days=[5, 6],  # Skip weekends (Saturday=5, Sunday=6)
            require_screen_on=True,  # Likely at desk with screen on
            require_wifi=False,
            min_battery_level=10.0
        )
    
    @staticmethod
    def any_location_habit(habit_id: str) -> ContextRule:
        """Template for habits that can happen anywhere (gratitude, etc.)"""
        return ContextRule(
            habit_id=habit_id,
            required_geofences=[],
            blocked_geofences=[],
            allowed_activities=[ActivityState.STATIONARY, ActivityState.WALKING],
            blocked_activities=[ActivityState.DRIVING],
            allowed_focus_modes=list(FocusMode),
            blocked_focus_modes=[FocusMode.SLEEP, FocusMode.DRIVING_FOCUS],
            allowed_hours=list(range(7, 23)),
            blocked_days=[],
            require_screen_on=False,
            require_wifi=False,
            min_battery_level=15.0
        )


# Example usage
if __name__ == "__main__":
    import time
    
    print("🔐 Context Gating System Demo\n")
    
    # Create context gate
    gate = ContextGate()
    
    # Define geofences
    home = Geofence(
        fence_id="home",
        name="Home",
        center=Location(37.7749, -122.4194, 10.0, time.time()),
        radius_meters=100,
        habit_ids=["meditation", "reading", "yoga"]
    )
    
    gym = Geofence(
        fence_id="gym",
        name="Gym",
        center=Location(37.7849, -122.4094, 10.0, time.time()),
        radius_meters=50,
        habit_ids=["workout"]
    )
    
    office = Geofence(
        fence_id="office",
        name="Office",
        center=Location(37.7949, -122.3994, 10.0, time.time()),
        radius_meters=75,
        habit_ids=["posture_check", "hydration"]
    )
    
    gate.register_geofence(home)
    gate.register_geofence(gym)
    gate.register_geofence(office)
    
    # Register rules for habits
    meditation_rule = ContextRuleTemplates.home_based_habit("meditation", "home")
    gate.register_rule(meditation_rule)
    
    workout_rule = ContextRuleTemplates.gym_based_habit("workout", "gym")
    gate.register_rule(workout_rule)
    
    posture_rule = ContextRuleTemplates.work_desk_habit("posture_check", "office")
    gate.register_rule(posture_rule)
    
    # Test different contexts
    print("Testing different user contexts:\n")
    
    test_contexts = [
        (
            "At home, stationary, screen on",
            UserContext(
                location=Location(37.7749, -122.4194, 10.0, time.time()),  # At home
                activity=ActivityState.STATIONARY,
                focus_mode=FocusMode.NONE,
                screen_on=True,
                battery_level=75.0,
                in_call=False,
                connected_to_wifi=True,
                time_of_day=10,
                day_of_week=2  # Wednesday
            )
        ),
        (
            "At gym, walking",
            UserContext(
                location=Location(37.7849, -122.4094, 10.0, time.time()),  # At gym
                activity=ActivityState.WALKING,
                focus_mode=FocusMode.FITNESS,
                screen_on=False,
                battery_level=60.0,
                in_call=False,
                connected_to_wifi=False,
                time_of_day=18,
                day_of_week=3
            )
        ),
        (
            "Driving (should block all)",
            UserContext(
                location=Location(37.7949, -122.3994, 10.0, time.time()),
                activity=ActivityState.DRIVING,
                focus_mode=FocusMode.DRIVING_FOCUS,
                screen_on=True,
                battery_level=80.0,
                in_call=False,
                connected_to_wifi=False,
                time_of_day=8,
                day_of_week=1
            )
        ),
        (
            "At office, working",
            UserContext(
                location=Location(37.7949, -122.3994, 10.0, time.time()),  # At office
                activity=ActivityState.STATIONARY,
                focus_mode=FocusMode.WORK,
                screen_on=True,
                battery_level=55.0,
                in_call=False,
                connected_to_wifi=True,
                time_of_day=14,
                day_of_week=2
            )
        )
    ]
    
    for description, context in test_contexts:
        print(f"📍 {description}")
        print(f"   Location: ({context.location.latitude:.4f}, {context.location.longitude:.4f})")
        print(f"   Activity: {context.activity.value}")
        print(f"   Interruptible: {'✅ Yes' if context.is_interruptible() else '❌ No'}")
        print(f"   Attention Level: {context.get_attention_level()}")
        
        # Check each habit
        for habit_id in gate.rules.keys():
            can_trigger, reason, metadata = gate.can_trigger(habit_id, context)
            
            if can_trigger:
                print(f"   ✅ {habit_id}: Can trigger")
                print(f"      Style: {metadata['presentation_style']}")
            else:
                print(f"   ❌ {habit_id}: Blocked - {reason}")
        
        print()
    
    # Show eligible habits for a good context
    print("🎯 Eligible habits at home (10 AM):\n")
    home_context = test_contexts[0][1]
    eligible = gate.get_eligible_habits(home_context)
    
    for habit_id, metadata in eligible:
        print(f"   • {habit_id}")
        print(f"     Attention: {metadata['attention_level']}")
        print(f"     Style: {metadata['presentation_style']}")
    
    print("\n✅ Context gating system operational")
