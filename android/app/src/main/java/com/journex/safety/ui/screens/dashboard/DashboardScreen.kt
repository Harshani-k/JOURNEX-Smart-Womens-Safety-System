package com.journex.safety.ui.screens.dashboard

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Book
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.LocalHospital
import androidx.compose.material.icons.filled.Lock
import androidx.compose.material.icons.filled.People
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.PhoneInTalk
import androidx.compose.material.icons.filled.PlayCircle
import androidx.compose.material.icons.filled.Security
import androidx.compose.material.icons.filled.Shield
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.journex.safety.ui.components.JourneyStatusCard
import com.journex.safety.ui.components.JournexTopAppBar
import com.journex.safety.ui.components.PriorityActionCard
import com.journex.safety.ui.components.SosEmergencyButton
import com.journex.safety.ui.theme.GuardianTeal
import com.journex.safety.ui.theme.GuardianTealContainer
import com.journex.safety.ui.theme.LavenderPrimary
import com.journex.safety.ui.theme.LavenderSurface
import com.journex.safety.ui.theme.PurpleDark
import com.journex.safety.ui.theme.PurplePrimary
import com.journex.safety.ui.theme.WarningAmber

@Composable
fun DashboardScreen(
    viewModel: DashboardViewModel,
    onNavigateToJourneySetup: () -> Unit,
    onNavigateToActiveJourney: () -> Unit,
    onNavigateToContacts: () -> Unit,
    onNavigateToSafePlaces: () -> Unit,
    onNavigateToJournal: () -> Unit,
    onNavigateToFakeCall: () -> Unit,
    onNavigateToHistory: () -> Unit,
    onNavigateToProfile: () -> Unit,
    onNavigateToPrivacy: () -> Unit,
    onNavigateToSimulation: () -> Unit
) {
    val uiState by viewModel.uiState.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    LaunchedEffect(uiState.snackbarMessage) {
        uiState.snackbarMessage?.let { message ->
            snackbarHostState.showSnackbar(message)
            viewModel.clearSnackbarMessage()
        }
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        topBar = {
            JournexTopAppBar(
                title = "JOURNEX",
                canNavigateBack = false,
                actions = {
                    IconButton(onClick = onNavigateToPrivacy) {
                        Icon(
                            imageVector = Icons.Default.Lock,
                            contentDescription = "Privacy Controls",
                            tint = PurplePrimary
                        )
                    }
                    IconButton(onClick = onNavigateToProfile) {
                        Box(
                            modifier = Modifier
                                .size(34.dp)
                                .clip(CircleShape)
                                .background(LavenderPrimary),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                imageVector = Icons.Default.Person,
                                contentDescription = "Profile",
                                tint = PurpleDark,
                                modifier = Modifier.size(20.dp)
                            )
                        }
                    }
                }
            )
        },
        containerColor = MaterialTheme.colorScheme.background
    ) { paddingValues ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = 20.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Welcome Greeting Header
            item {
                Spacer(modifier = Modifier.height(4.dp))
                Column {
                    Text(
                        text = "Hello, Traveler",
                        style = MaterialTheme.typography.headlineMedium,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.onBackground
                    )
                    Text(
                        text = "Your journey is protected by adaptive safety check-ins",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            // Priority 1: Journey Status Hero Card (Start Journey is inside this card)
            item {
                JourneyStatusCard(
                    isJourneyActive = uiState.isJourneyActive,
                    destinationName = uiState.activeDestination,
                    etaText = uiState.estimatedArrivalText,
                    onStartJourneyClick = onNavigateToJourneySetup,
                    onViewActiveJourneyClick = onNavigateToActiveJourney
                )
            }

            // Priority 3: Accessible SOS Emergency Panic Trigger
            item {
                SosEmergencyButton(
                    onEmergencyTriggered = {
                        viewModel.triggerEmergencySos()
                    }
                )
            }

            // Section Header: Core Safety Tools
            item {
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Core Safety Tools",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onBackground
                )
            }

            // Priority 4: Trusted Contacts
            item {
                PriorityActionCard(
                    title = "Trusted Emergency Contacts",
                    subtitle = "${uiState.trustedContactsCount} guardians verified & connected",
                    icon = Icons.Default.People,
                    iconTint = PurplePrimary,
                    iconContainerColor = LavenderSurface,
                    badgeText = "${uiState.trustedContactsCount} Active",
                    onClick = onNavigateToContacts
                )
            }

            // Priority 5: Safe Places Directory
            item {
                PriorityActionCard(
                    title = "Safe Places Directory",
                    subtitle = "Nearby 24/7 verified police, hospitals & transit hubs",
                    icon = Icons.Default.LocalHospital,
                    iconTint = GuardianTeal,
                    iconContainerColor = GuardianTealContainer,
                    badgeText = "${uiState.safePlacesNearbyCount} Nearby",
                    onClick = onNavigateToSafePlaces
                )
            }

            // Priority 6: Safety Incident Journal
            item {
                PriorityActionCard(
                    title = "Safety Incident Journal",
                    subtitle = "Privately log incidents, plate numbers & travel notes",
                    icon = Icons.Default.Book,
                    iconTint = Color(0xFF6A1B9A),
                    iconContainerColor = LavenderPrimary.copy(alpha = 0.5f),
                    badgeText = "${uiState.journalEntriesCount} Logs",
                    onClick = onNavigateToJournal
                )
            }

            // Section Header: Utility & Verification Tools
            item {
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = "Travel Utilities & Demonstration",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onBackground
                )
            }

            // Feature 14: Safe Exit / Fake Call
            item {
                PriorityActionCard(
                    title = "Safe Exit / Fake Call",
                    subtitle = "Simulate an urgent incoming call to excuse yourself",
                    icon = Icons.Default.PhoneInTalk,
                    iconTint = Color(0xFF1565C0),
                    iconContainerColor = Color(0xFFE3F2FD),
                    onClick = onNavigateToFakeCall
                )
            }

            // Feature 13: Journey History & Safety Records
            item {
                PriorityActionCard(
                    title = "Journey History & Records",
                    subtitle = "Review past trips, routes and check-in adherence",
                    icon = Icons.Default.History,
                    iconTint = Color(0xFF455A64),
                    iconContainerColor = Color(0xFFECEFF1),
                    onClick = onNavigateToHistory
                )
            }

            // Feature 18: Demo Simulation Mode (for Evaluators / Viva)
            item {
                PriorityActionCard(
                    title = "Demo Simulation Mode",
                    subtitle = "Simulate deviations, missed check-ins & ML risk scoring",
                    icon = Icons.Default.PlayCircle,
                    iconTint = WarningAmber,
                    iconContainerColor = Color(0xFFFFF3E0),
                    badgeText = "VIVA TEST",
                    onClick = onNavigateToSimulation
                )
            }

            item {
                Spacer(modifier = Modifier.height(16.dp))
            }
        }
    }
}
