# 360° Nudging Framework - Visual System Overview

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER'S DAY BEGINS                             │
│                      (8:00 AM)                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  CONTEXT MONITORING (Continuous)                                 │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │
│  │  Location     │  │  Activity     │  │  Device State │       │
│  │  GPS: Home    │  │  Stationary   │  │  Screen: ON   │       │
│  │  Geofence: ✓  │  │  Walking      │  │  Battery: 85% │       │
│  └───────────────┘  └───────────────┘  └───────────────┘       │
│                                                                   │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │
│  │  Focus Mode   │  │  Time of Day  │  │  WiFi         │       │
│  │  None         │  │  10:23 AM     │  │  Connected    │       │
│  └───────────────┘  └───────────────┘  └───────────────┘       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  TRIGGER ENGINE (Variable Interval)                              │
│                                                                   │
│  Last Trigger: 7:45 AM                                           │
│  Mean Interval: 180 minutes (±45 min std dev)                   │
│  Next Window: 10:15 AM - 10:45 AM  ← [ACTIVE NOW]              │
│  Jitter Applied: +8 minutes                                      │
│                                                                   │
│  Decision: ✅ TRIGGER SCHEDULED                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  CONTEXT GATE (Eligibility Check)                                │
│                                                                   │
│  Habit: Meditation                                               │
│                                                                   │
│  ✓ Location: Home (required: ✓)                                 │
│  ✓ Activity: Stationary (allowed: ✓)                            │
│  ✓ Not Driving (blocked: ✗)                                     │
│  ✓ Not In Call (blocked: ✗)                                     │
│  ✓ Focus Mode: None (allowed: ✓)                                │
│  ✓ Time: 10:23 AM (window: 7AM-11PM ✓)                         │
│  ✓ Battery: 85% (min: 15% ✓)                                    │
│                                                                   │
│  Decision: ✅ CONTEXT ELIGIBLE                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  VARIANT SELECTOR (Polymorphic Presentation)                     │
│                                                                   │
│  Available Variants: 10                                          │
│  Recent History: [v1, v4, v7, v2, v9]  ← Exclude these         │
│                                                                   │
│  Contextual Factors:                                             │
│  • Time: Morning (10 AM) → Prefer energetic colors             │
│  • Screen: ON → Can use rich layout                            │
│  • Focus: None → Full animations OK                            │
│                                                                   │
│  Selected: Variant #3                                            │
│  ┌────────────────────────────────────┐                         │
│  │ Emoji: 🍃                          │                         │
│  │ Message: "Breath space open 🌅"   │                         │
│  │ Layout: Banner                     │                         │
│  │ Colors: #2ECC71 → #27AE60         │                         │
│  │ Font: Roboto                       │                         │
│  │ Animation: Slide-in                │                         │
│  └────────────────────────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  DEVICE ROUTER (Multi-Device Selection)                          │
│                                                                   │
│  Available Devices:                                              │
│  • Phone: Active (screen on, last used 2 min ago) ✓            │
│  • Desktop: Idle (screen on, last used 45 min ago)             │
│  • Watch: Inactive                                               │
│                                                                   │
│  Context Analysis:                                               │
│  • User is stationary + at home                                 │
│  • Phone screen is active                                        │
│  • WiFi connected (likely at desk)                              │
│                                                                   │
│  Decision: Target = PHONE                                        │
│  Presentation Style: RICH (high attention available)             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  WIDGET DISPLAY (Phone Home Screen)                              │
│  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓  │
│  ┃                                                           ┃  │
│  ┃   ╔═══════════════════════════════════════════════════╗  ┃  │
│  ┃   ║  🍃                 Breath space open 🌅          ║  ┃  │
│  ┃   ║                                                   ║  ┃  │
│  ┃   ║  [Green gradient background: #2ECC71 → #27AE60]  ║  ┃  │
│  ┃   ║                                                   ║  ┃  │
│  ┃   ║  [Slide-in animation: gentle right-to-left]      ║  ┃  │
│  ┃   ╚═══════════════════════════════════════════════════╝  ┃  │
│  ┃                                                           ┃  │
│  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛  │
│                                                                   │
│  User Perception:                                                │
│  • Non-imperative tone: "space open" (not "meditate now!")     │
│  • Contextually relevant: At home, not busy                     │
│  • Visually novel: New colors/layout vs. last 5 triggers       │
│  • Low pressure: Can tap or ignore                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  USER RESPONSE                                                    │
│                                                                   │
│  Option A: USER COMPLETES HABIT (70% probability)               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. User taps widget (t=0s)                                  │ │
│  │ 2. Opens meditation app (t=5s)                              │ │
│  │ 3. Completes 10-minute session (t=605s)                     │ │
│  │ 4. System records: COMPLETED, response_time=605s            │ │
│  │ 5. Increment streak counter: 7 → 8 days 🔥                 │ │
│  │ 6. Update engagement metrics: 73% → 74%                     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Option B: USER DISMISSES (30% probability)                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. User sees widget but is busy (t=30s)                     │ │
│  │ 2. Swipes to dismiss (t=35s)                                │ │
│  │ 3. System records: DISMISSED, response_time=35s             │ │
│  │ 4. Update dismissal rate: 25% → 26%                         │ │
│  │ 5. Check fatigue: 26% > 25% threshold                       │ │
│  │ 6. Auto-adjust: Increase interval by 40% (180 → 252 min)   │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  LEARNING & ADAPTATION                                            │
│                                                                   │
│  Engagement History (Last 7 Days):                               │
│  ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┐                   │
│  │ Mon │ Tue │ Wed │ Thu │ Fri │ Sat │ Sun │                   │
│  ├─────┼─────┼─────┼─────┼─────┼─────┼─────┤                   │
│  │ 3/4 │ 2/3 │ 4/4 │ 3/5 │ 2/3 │ 3/4 │ 4/4 │  ← Completed/Sent│
│  └─────┴─────┴─────┴─────┴─────┴─────┴─────┘                   │
│                                                                   │
│  Metrics:                                                         │
│  • Total Triggers: 27                                            │
│  • Completed: 21 (78%)  ← Excellent!                            │
│  • Dismissed: 6 (22%)                                            │
│  • Avg Response Time: 387 seconds                                │
│  • Current Streak: 8 days 🔥                                    │
│                                                                   │
│  Insights:                                                        │
│  • Best times: 9-11 AM (85% completion)                         │
│  • Worst times: 7-8 PM (45% completion) → Adjust schedule      │
│  • Most effective variant: #3 (green gradient) → Use more       │
│  • No fatigue detected → Keep current frequency                 │
│                                                                   │
│  Next Actions:                                                    │
│  • Schedule next trigger: 1:15 PM (±15 min window)             │
│  • Exclude variants: [v1, v4, v7, v2, v9, v3]                  │
│  • Prepare contextual message based on afternoon timing         │
└─────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════
                    KEY DIFFERENTIATORS
═══════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────┐
│  VS. TRADITIONAL REMINDER SYSTEMS                                 │
└─────────────────────────────────────────────────────────────────┘

❌ STATIC REMINDERS                 ✅ 360° FRAMEWORK
┌──────────────────────┐           ┌──────────────────────┐
│ Fixed time: 9:00 AM  │           │ VI Schedule: 8:47 AM │
│ Same visual always   │           │ Variant #3 of 10     │
│ "Meditate now!"      │           │ "Breath space open"  │
│ Fires while driving  │           │ Context-gated ✓      │
│ Dismissal rate: 45%  │           │ Dismissal rate: 22%  │
│ Habit fails in 8 days│           │ Sustained for months │
└──────────────────────┘           └──────────────────────┘


═══════════════════════════════════════════════════════════════════
                    PSYCHOLOGICAL MECHANISMS
═══════════════════════════════════════════════════════════════════

1. HABITUATION BYPASS
   ┌────────────────────────────────────────────────┐
   │ Unpredictable timing + Polymorphic visuals     │
   │ → Visual cortex cannot adapt                   │
   │ → Sustained attention over time                │
   └────────────────────────────────────────────────┘

2. REACTANCE REDUCTION
   ┌────────────────────────────────────────────────┐
   │ Non-imperative language + Contextual framing   │
   │ → User maintains autonomy                      │
   │ → Invitation, not command                      │
   └────────────────────────────────────────────────┘

3. CONTEXT ALIGNMENT
   ┌────────────────────────────────────────────────┐
   │ Geofencing + Activity + Focus mode             │
   │ → Trigger only when appropriate                │
   │ → Builds trust in system                       │
   └────────────────────────────────────────────────┘

4. VARIABLE REINFORCEMENT
   ┌────────────────────────────────────────────────┐
   │ VI schedule (Skinner's most powerful schedule) │
   │ → Maintains engagement without extinction      │
   │ → Habit becomes self-sustaining                │
   └────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════
                    IMPLEMENTATION CHECKLIST
═══════════════════════════════════════════════════════════════════

PHASE 1: BACKEND (2 weeks)
☐ Deploy trigger engine to cloud
☐ Set up Firebase/Supabase database
☐ Create user authentication
☐ Implement variant generator
☐ Build context gate API

PHASE 2: MOBILE (4-6 weeks)
☐ Create iOS widget with WidgetKit
☐ Implement geofencing (CoreLocation)
☐ Integrate focus mode detection
☐ Build background refresh system
☐ Connect to backend API

PHASE 3: TESTING (2-4 weeks)
☐ Beta test with 10 internal users
☐ Iterate based on feedback
☐ Expand to 50-100 beta users
☐ Run A/B test vs. control group
☐ Validate metrics (60% engagement target)

PHASE 4: SCALE (Ongoing)
☐ Add Android support
☐ Build desktop companions
☐ Implement adaptive learning
☐ Enable habit chaining
☐ Launch publicly


═══════════════════════════════════════════════════════════════════
                    SUCCESS METRICS
═══════════════════════════════════════════════════════════════════

TARGET AFTER 30 DAYS:
┌───────────────────────┬──────────┬──────────┬────────────┐
│ Metric                │ Static   │ 360°     │ Target     │
├───────────────────────┼──────────┼──────────┼────────────┤
│ Daily Engagement      │ 15%      │ 60%+     │ ✓ 4x       │
│ 30-Day Retention      │ 8%       │ 40%+     │ ✓ 5x       │
│ Habit Completion      │ 12%      │ 55%+     │ ✓ 4.5x     │
│ User Annoyance        │ 45%      │ <15%     │ ✓ -30pp    │
│ Streak Length (avg)   │ 2.3 days │ 12+ days │ ✓ 5x       │
└───────────────────────┴──────────┴──────────┴────────────┘

VALIDATION: Chi-squared test, p < 0.05, n=1000 (500 control, 500 test)


═══════════════════════════════════════════════════════════════════
           READY TO BUILD? START HERE:
           
           1. cd backend && python3 trigger_engine.py
           2. Read 360_nudging_framework.md
           3. Copy mobile/ios_widget_example.swift
           4. Deploy and test!
═══════════════════════════════════════════════════════════════════
```
