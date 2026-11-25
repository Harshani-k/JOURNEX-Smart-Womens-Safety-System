package com.journex.safety.navigation

/**
 * Official Navigation Routes for JOURNEX.
 */
sealed class NavRoutes(val route: String) {
    object Welcome : NavRoutes("welcome")
    object Dashboard : NavRoutes("dashboard")
    object JourneySetup : NavRoutes("journey_setup")
    object ActiveJourney : NavRoutes("active_journey")
    object Contacts : NavRoutes("contacts")
    object SafePlaces : NavRoutes("safe_places")
    object IncidentJournal : NavRoutes("incident_journal")
    object FakeCall : NavRoutes("fake_call")
    object Profile : NavRoutes("profile")
    object Privacy : NavRoutes("privacy")
    object Simulation : NavRoutes("simulation")
    object History : NavRoutes("history")
}
