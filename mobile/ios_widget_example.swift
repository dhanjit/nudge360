// iOS Widget Implementation - HabitNudgeWidget
// SwiftUI + WidgetKit for polymorphic home screen widgets

import WidgetKit
import SwiftUI
import CoreLocation

// MARK: - Widget Configuration

struct HabitNudgeWidget: Widget {
    let kind: String = "HabitNudgeWidget"
    
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: kind, provider: Provider()) { entry in
            HabitNudgeEntryView(entry: entry)
        }
        .configurationDisplayName("Habit Nudge")
        .description("Context-aware habit reminders that adapt to you")
        .supportedFamilies([.systemSmall, .systemMedium])
    }
}

// MARK: - Timeline Provider

struct Provider: TimelineProvider {
    func placeholder(in context: Context) -> NudgeEntry {
        NudgeEntry(
            date: Date(),
            variant: WidgetVariant.placeholder()
        )
    }

    func getSnapshot(in context: Context, completion: @escaping (NudgeEntry) -> ()) {
        let entry = NudgeEntry(
            date: Date(),
            variant: fetchCurrentVariant()
        )
        completion(entry)
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<Entry>) -> ()) {
        // Check with orchestrator if trigger should fire
        let shouldTrigger = NudgeOrchestrator.shared.shouldTriggerNow(for: "meditation")
        
        if shouldTrigger {
            let variant = NudgeOrchestrator.shared.getNextVariant(for: "meditation")
            let entry = NudgeEntry(date: Date(), variant: variant)
            
            // Refresh after 5 minutes (or when next trigger scheduled)
            let nextUpdate = Calendar.current.date(byAdding: .minute, value: 5, to: Date())!
            let timeline = Timeline(entries: [entry], policy: .after(nextUpdate))
            completion(timeline)
        } else {
            // No trigger scheduled, check back in 15 minutes
            let nextCheck = Calendar.current.date(byAdding: .minute, value: 15, to: Date())!
            let entry = NudgeEntry(date: Date(), variant: nil)
            let timeline = Timeline(entries: [entry], policy: .after(nextCheck))
            completion(timeline)
        }
    }
    
    private func fetchCurrentVariant() -> WidgetVariant {
        // In production, fetch from backend/local storage
        // For now, return a sample variant
        return WidgetVariant.sample()
    }
}

// MARK: - Data Models

struct NudgeEntry: TimelineEntry {
    let date: Date
    let variant: WidgetVariant?
}

struct WidgetVariant {
    let id: String
    let habitId: String
    let emoji: String
    let message: String
    let colorPrimary: Color
    let colorSecondary: Color
    let layoutStyle: LayoutStyle
    let animation: AnimationType
    let fontName: String
    
    enum LayoutStyle: String {
        case minimal, card, banner, badge, ambient
    }
    
    enum AnimationType: String {
        case breathe, fade, slide, glow, none
    }
    
    static func placeholder() -> WidgetVariant {
        return WidgetVariant(
            id: "placeholder",
            habitId: "meditation",
            emoji: "🧘",
            message: "Still point available",
            colorPrimary: Color(hex: "#4A90E2"),
            colorSecondary: Color(hex: "#7B68EE"),
            layoutStyle: .minimal,
            animation: .breathe,
            fontName: "SF Pro Rounded"
        )
    }
    
    static func sample() -> WidgetVariant {
        let samples = [
            WidgetVariant(
                id: "v1",
                habitId: "meditation",
                emoji: "🧘",
                message: "Still point available",
                colorPrimary: Color(hex: "#4A90E2"),
                colorSecondary: Color(hex: "#7B68EE"),
                layoutStyle: .minimal,
                animation: .breathe,
                fontName: "SF Pro Rounded"
            ),
            WidgetVariant(
                id: "v2",
                habitId: "meditation",
                emoji: "🌊",
                message: "Anchor moment ready",
                colorPrimary: Color(hex: "#FF6B6B"),
                colorSecondary: Color(hex: "#FFA500"),
                layoutStyle: .card,
                animation: .fade,
                fontName: "Georgia"
            ),
            WidgetVariant(
                id: "v3",
                habitId: "meditation",
                emoji: "🍃",
                message: "Breath space open",
                colorPrimary: Color(hex: "#2ECC71"),
                colorSecondary: Color(hex: "#27AE60"),
                layoutStyle: .banner,
                animation: .slide,
                fontName: "Helvetica Neue"
            )
        ]
        return samples.randomElement()!
    }
}

// MARK: - Widget View

struct HabitNudgeEntryView: View {
    var entry: Provider.Entry
    @Environment(\.widgetFamily) var family
    
    var body: some View {
        if let variant = entry.variant {
            ZStack {
                // Polymorphic gradient background
                LinearGradient(
                    gradient: Gradient(colors: [variant.colorPrimary, variant.colorSecondary]),
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()
                
                // Content based on layout style
                switch variant.layoutStyle {
                case .minimal:
                    MinimalLayout(variant: variant, family: family)
                case .card:
                    CardLayout(variant: variant, family: family)
                case .banner:
                    BannerLayout(variant: variant, family: family)
                case .badge:
                    BadgeLayout(variant: variant, family: family)
                case .ambient:
                    AmbientLayout(variant: variant, family: family)
                }
            }
            .widgetURL(URL(string: "habitnudge://open/\(variant.habitId)"))
            .modifier(AnimationModifier(type: variant.animation))
        } else {
            // Empty state - no active trigger
            EmptyWidgetView()
        }
    }
}

// MARK: - Layout Styles

struct MinimalLayout: View {
    let variant: WidgetVariant
    let family: WidgetFamily
    
    var body: some View {
        VStack(spacing: 8) {
            Text(variant.emoji)
                .font(.system(size: family == .systemSmall ? 40 : 50))
            
            Text(variant.message)
                .font(.custom(variant.fontName, size: family == .systemSmall ? 14 : 16))
                .foregroundColor(.white)
                .multilineTextAlignment(.center)
                .lineLimit(2)
        }
        .padding()
    }
}

struct CardLayout: View {
    let variant: WidgetVariant
    let family: WidgetFamily
    
    var body: some View {
        VStack(spacing: 12) {
            HStack {
                Text(variant.emoji)
                    .font(.system(size: 36))
                Spacer()
                Image(systemName: "chevron.right")
                    .foregroundColor(.white.opacity(0.7))
            }
            
            Spacer()
            
            Text(variant.message)
                .font(.custom(variant.fontName, size: 18))
                .foregroundColor(.white)
                .fontWeight(.medium)
        }
        .padding()
    }
}

struct BannerLayout: View {
    let variant: WidgetVariant
    let family: WidgetFamily
    
    var body: some View {
        HStack(spacing: 16) {
            Text(variant.emoji)
                .font(.system(size: 44))
            
            VStack(alignment: .leading, spacing: 4) {
                Text(variant.message)
                    .font(.custom(variant.fontName, size: 16))
                    .foregroundColor(.white)
                    .fontWeight(.semibold)
                
                Text("Tap to begin")
                    .font(.caption)
                    .foregroundColor(.white.opacity(0.8))
            }
            
            Spacer()
        }
        .padding()
    }
}

struct BadgeLayout: View {
    let variant: WidgetVariant
    let family: WidgetFamily
    
    var body: some View {
        ZStack {
            Circle()
                .fill(Color.white.opacity(0.2))
                .frame(width: 100, height: 100)
            
            VStack(spacing: 6) {
                Text(variant.emoji)
                    .font(.system(size: 40))
                
                Text(variant.message)
                    .font(.custom(variant.fontName, size: 12))
                    .foregroundColor(.white)
                    .multilineTextAlignment(.center)
                    .lineLimit(2)
                    .frame(width: 90)
            }
        }
    }
}

struct AmbientLayout: View {
    let variant: WidgetVariant
    let family: WidgetFamily
    
    var body: some View {
        // Subtle, low-contrast design for focus mode
        VStack {
            Spacer()
            HStack {
                Text(variant.emoji)
                    .font(.system(size: 24))
                    .opacity(0.6)
                Text(variant.message)
                    .font(.custom(variant.fontName, size: 12))
                    .foregroundColor(.white.opacity(0.5))
            }
            .padding()
        }
    }
}

struct EmptyWidgetView: View {
    var body: some View {
        ZStack {
            Color.gray.opacity(0.2)
            
            VStack {
                Image(systemName: "moon.zzz")
                    .font(.system(size: 30))
                    .foregroundColor(.gray)
                Text("Resting")
                    .font(.caption)
                    .foregroundColor(.gray)
            }
        }
    }
}

// MARK: - Animation Modifier

struct AnimationModifier: ViewModifier {
    let type: WidgetVariant.AnimationType
    @State private var isAnimating = false
    
    func body(content: Content) -> some View {
        switch type {
        case .breathe:
            content
                .scaleEffect(isAnimating ? 1.05 : 1.0)
                .animation(
                    Animation.easeInOut(duration: 3.0)
                        .repeatForever(autoreverses: true),
                    value: isAnimating
                )
                .onAppear { isAnimating = true }
            
        case .fade:
            content
                .opacity(isAnimating ? 0.8 : 1.0)
                .animation(
                    Animation.easeInOut(duration: 2.0)
                        .repeatForever(autoreverses: true),
                    value: isAnimating
                )
                .onAppear { isAnimating = true }
            
        case .glow:
            content
                .shadow(color: .white.opacity(isAnimating ? 0.8 : 0.3), radius: 10)
                .animation(
                    Animation.easeInOut(duration: 2.5)
                        .repeatForever(autoreverses: true),
                    value: isAnimating
                )
                .onAppear { isAnimating = true }
            
        default:
            content
        }
    }
}

// MARK: - Orchestrator Integration

class NudgeOrchestrator {
    static let shared = NudgeOrchestrator()
    
    private init() {}
    
    func shouldTriggerNow(for habitId: String) -> Bool {
        // Check with backend or local trigger engine
        // This would involve:
        // 1. Check scheduled trigger time
        // 2. Validate context (location, activity, focus mode)
        // 3. Check cooldown period
        
        // For demo, return random
        return Bool.random()
    }
    
    func getNextVariant(for habitId: String) -> WidgetVariant {
        // Fetch from variant pool, avoiding recent repeats
        return WidgetVariant.sample()
    }
}

// MARK: - Color Extension

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3: // RGB (12-bit)
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6: // RGB (24-bit)
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8: // ARGB (32-bit)
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (1, 1, 1, 0)
        }

        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue:  Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}

// MARK: - Geofencing Setup (App Delegate)

/*
In your main app's AppDelegate or SwiftUI App:

import CoreLocation

class AppDelegate: NSObject, UIApplicationDelegate, CLLocationManagerDelegate {
    let locationManager = CLLocationManager()
    
    func application(_ application: UIApplication, 
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey : Any]? = nil) -> Bool {
        
        // Request location permissions
        locationManager.delegate = self
        locationManager.requestAlwaysAuthorization()
        
        // Setup geofences
        setupGeofences()
        
        return true
    }
    
    func setupGeofences() {
        // Home geofence
        let homeCoordinate = CLLocationCoordinate2D(latitude: 37.7749, longitude: -122.4194)
        let homeRegion = CLCircularRegion(center: homeCoordinate, 
                                          radius: 100, 
                                          identifier: "home")
        homeRegion.notifyOnEntry = true
        homeRegion.notifyOnExit = true
        
        locationManager.startMonitoring(for: homeRegion)
    }
    
    func locationManager(_ manager: CLLocationManager, 
                        didEnterRegion region: CLRegion) {
        // User entered a geofence
        print("Entered region: \(region.identifier)")
        
        // Notify backend
        NotificationCenter.default.post(
            name: .geofenceEntered,
            object: region.identifier
        )
        
        // Refresh widget to check for eligible triggers
        WidgetCenter.shared.reloadTimelines(ofKind: "HabitNudgeWidget")
    }
    
    func locationManager(_ manager: CLLocationManager, 
                        didExitRegion region: CLRegion) {
        print("Exited region: \(region.identifier)")
    }
}

extension Notification.Name {
    static let geofenceEntered = Notification.Name("geofenceEntered")
    static let geofenceExited = Notification.Name("geofenceExited")
}
*/

// MARK: - Usage in SwiftUI App

/*
@main
struct HabitNudgeApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
*/
