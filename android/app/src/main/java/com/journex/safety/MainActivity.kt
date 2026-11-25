package com.journex.safety

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.journex.safety.navigation.NavRoutes
import com.journex.safety.service.JourneyTrackingService
import com.journex.safety.utils.PermissionUtils
import com.journex.safety.ui.screens.contacts.ContactsScreen
import com.journex.safety.ui.screens.contacts.ContactsViewModel
import com.journex.safety.ui.screens.dashboard.DashboardScreen
import com.journex.safety.ui.screens.dashboard.DashboardViewModel
import com.journex.safety.ui.screens.fakecall.FakeCallScreen
import com.journex.safety.ui.screens.history.HistoryScreen
import com.journex.safety.ui.screens.history.HistoryViewModel
import com.journex.safety.ui.screens.journal.IncidentJournalScreen
import com.journex.safety.ui.screens.journal.JournalViewModel
import com.journex.safety.ui.screens.journey.ActiveJourneyScreen
import com.journex.safety.ui.screens.journey.JourneySetupScreen
import com.journex.safety.ui.screens.privacy.PrivacyScreen
import com.journex.safety.ui.screens.profile.ProfileScreen
import com.journex.safety.ui.screens.profile.ProfileViewModel
import com.journex.safety.ui.screens.safeplaces.SafePlacesScreen
import com.journex.safety.ui.screens.simulation.SimulationScreen
import com.journex.safety.ui.screens.welcome.WelcomeScreen
import com.journex.safety.ui.theme.JournexTheme

class MainActivity : ComponentActivity() {

    private val app by lazy { application as JournexApp }

    private val dashboardViewModel: DashboardViewModel by viewModels {
        DashboardViewModel.provideFactory(app.repository, app.emergencyRepository)
    }

    private val contactsViewModel: ContactsViewModel by viewModels {
        ContactsViewModel.provideFactory(app.repository)
    }

    private val profileViewModel: ProfileViewModel by viewModels {
        ProfileViewModel.provideFactory(app.repository)
    }

    private val journalViewModel: JournalViewModel by viewModels {
        JournalViewModel.provideFactory(app.repository)
    }

    private val historyViewModel: HistoryViewModel by viewModels {
        HistoryViewModel.provideFactory(app.repository)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            JournexTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    val navController = rememberNavController()
                    val dashboardState by dashboardViewModel.uiState.collectAsState()

                    NavHost(
                        navController = navController,
                        startDestination = NavRoutes.Welcome.route
                    ) {
                        // 1. Welcome Screen
                        composable(NavRoutes.Welcome.route) {
                            WelcomeScreen(
                                onGetStartedClick = {
                                    navController.navigate(NavRoutes.Dashboard.route) {
                                        popUpTo(NavRoutes.Welcome.route) { inclusive = true }
                                    }
                                }
                            )
                        }

                        // 2. Dashboard
                        composable(NavRoutes.Dashboard.route) {
                            DashboardScreen(
                                viewModel = dashboardViewModel,
                                onNavigateToJourneySetup = {
                                    navController.navigate(NavRoutes.JourneySetup.route)
                                },
                                onNavigateToActiveJourney = {
                                    navController.navigate(NavRoutes.ActiveJourney.route)
                                },
                                onNavigateToContacts = {
                                    navController.navigate(NavRoutes.Contacts.route)
                                },
                                onNavigateToSafePlaces = {
                                    navController.navigate(NavRoutes.SafePlaces.route)
                                },
                                onNavigateToJournal = {
                                    navController.navigate(NavRoutes.IncidentJournal.route)
                                },
                                onNavigateToFakeCall = {
                                    navController.navigate(NavRoutes.FakeCall.route)
                                },
                                onNavigateToHistory = {
                                    navController.navigate(NavRoutes.History.route)
                                },
                                onNavigateToProfile = {
                                    navController.navigate(NavRoutes.Profile.route)
                                },
                                onNavigateToPrivacy = {
                                    navController.navigate(NavRoutes.Privacy.route)
                                },
                                onNavigateToSimulation = {
                                    navController.navigate(NavRoutes.Simulation.route)
                                }
                            )
                        }

                        // 3. Journey Setup Screen
                        composable(NavRoutes.JourneySetup.route) {
                            JourneySetupScreen(
                                onNavigateBack = { navController.popBackStack() },
                                onStartMonitoring = { destination, etaMinutes, isRealGps ->
                                    dashboardViewModel.startJourney(destination, etaMinutes, isRealGps)
                                    if (isRealGps && PermissionUtils.hasLocationPermission(this@MainActivity)) {
                                        JourneyTrackingService.startService(
                                            context = this@MainActivity,
                                            journeyId = 1L,
                                            destination = destination
                                        )
                                    }
                                    navController.navigate(NavRoutes.ActiveJourney.route) {
                                        popUpTo(NavRoutes.Dashboard.route)
                                    }
                                }
                            )
                        }

                        // 4. Active Journey Live Monitoring & Check-In Screen
                        composable(NavRoutes.ActiveJourney.route) {
                            ActiveJourneyScreen(
                                destination = dashboardState.activeDestination,
                                etaText = dashboardState.estimatedArrivalText,
                                isRealGps = dashboardState.isRealGpsActive,
                                journeyId = 1L,
                                onNavigateBackToDashboard = {
                                    navController.navigate(NavRoutes.Dashboard.route) {
                                        popUpTo(NavRoutes.Dashboard.route) { inclusive = true }
                                    }
                                },
                                onEndJourney = {
                                    JourneyTrackingService.stopService(this@MainActivity)
                                    dashboardViewModel.endJourney()
                                    navController.navigate(NavRoutes.Dashboard.route) {
                                        popUpTo(NavRoutes.Dashboard.route) { inclusive = true }
                                    }
                                },
                                onTriggerSos = {
                                    dashboardViewModel.triggerEmergencySos()
                                }
                            )
                        }

                        // 5. Trusted Contacts Screen (Room backed)
                        composable(NavRoutes.Contacts.route) {
                            ContactsScreen(
                                viewModel = contactsViewModel,
                                onNavigateBack = { navController.popBackStack() }
                            )
                        }

                        // 6. Safe Places Directory Screen
                        composable(NavRoutes.SafePlaces.route) {
                            SafePlacesScreen(
                                onNavigateBack = { navController.popBackStack() }
                            )
                        }

                        // 7. Safety Incident Journal Screen (KeyStore Encrypted Room backed)
                        composable(NavRoutes.IncidentJournal.route) {
                            IncidentJournalScreen(
                                viewModel = journalViewModel,
                                onNavigateBack = { navController.popBackStack() }
                            )
                        }

                        // 8. Safe Exit / Fake Call Screen
                        composable(NavRoutes.FakeCall.route) {
                            FakeCallScreen(
                                onNavigateBack = { navController.popBackStack() }
                            )
                        }

                        // 9. Personal Safety Profile Screen (Room backed)
                        composable(NavRoutes.Profile.route) {
                            ProfileScreen(
                                viewModel = profileViewModel,
                                onNavigateBack = { navController.popBackStack() }
                            )
                        }

                        // 10. Privacy Controls Screen
                        composable(NavRoutes.Privacy.route) {
                            PrivacyScreen(
                                repository = app.repository,
                                onNavigateBack = { navController.popBackStack() }
                            )
                        }

                        // 11. Demo Simulation Mode Screen
                        composable(NavRoutes.Simulation.route) {
                            SimulationScreen(
                                onNavigateBack = { navController.popBackStack() }
                            )
                        }

                        // 12. Journey History & Records Screen (Room backed)
                        composable(NavRoutes.History.route) {
                            HistoryScreen(
                                viewModel = historyViewModel,
                                onNavigateBack = { navController.popBackStack() }
                            )
                        }
                    }
                }
            }
        }
    }
}
