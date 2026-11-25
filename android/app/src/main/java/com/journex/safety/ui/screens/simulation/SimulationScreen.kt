package com.journex.safety.ui.screens.simulation

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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.journex.safety.ui.components.JournexTopAppBar
import com.journex.safety.ui.theme.EmergencyRed
import com.journex.safety.ui.theme.GuardianTeal
import com.journex.safety.ui.theme.GuardianTealContainer
import com.journex.safety.ui.theme.LavenderBorder
import com.journex.safety.ui.theme.LavenderSurface
import com.journex.safety.ui.theme.PurplePrimary
import com.journex.safety.ui.theme.WarningAmber
import com.journex.safety.ui.theme.WarningAmberContainer
import kotlinx.coroutines.launch

@Composable
fun SimulationScreen(
    onNavigateBack: () -> Unit
) {
    var simulatedDeviationMeters by remember { mutableStateOf(0) }
    var simulatedMissedCheckIns by remember { mutableStateOf(0) }
    var simulatedRiskLevel by remember { mutableStateOf("LOW (SCORE: 0.12)") }
    var simulatedEscalationTier by remember { mutableStateOf("Tier 0 (Normal Monitoring)") }

    val snackbarHostState = remember { SnackbarHostState() }
    val scope = rememberCoroutineScope()

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        topBar = {
            JournexTopAppBar(
                title = "Demo Simulation Mode",
                canNavigateBack = true,
                onNavigateBack = onNavigateBack
            )
        },
        containerColor = MaterialTheme.colorScheme.background
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = 20.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Spacer(modifier = Modifier.height(4.dp))

            Surface(
                color = WarningAmberContainer,
                shape = RoundedCornerShape(12.dp)
            ) {
                Text(
                    text = "VIVA EVALUATION HARNESS: Test 18 features indoors without physical travel.",
                    style = MaterialTheme.typography.bodySmall,
                    color = WarningAmber,
                    fontWeight = FontWeight.Bold,
                    modifier = Modifier.padding(12.dp)
                )
            }

            // Real-Time Output Display
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(18.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                border = CardDefaults.outlinedCardBorder().copy(
                    brush = androidx.compose.ui.graphics.SolidColor(LavenderBorder)
                )
            ) {
                Column(
                    modifier = Modifier.padding(18.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Text(
                        text = "Real-Time ML Inference Output",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("Simulated Deviation:", color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Text("${simulatedDeviationMeters}m", fontWeight = FontWeight.Bold)
                    }
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("Missed Check-Ins:", color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Text("$simulatedMissedCheckIns", fontWeight = FontWeight.Bold)
                    }
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("Predicted Risk Level:", color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Text(
                            text = simulatedRiskLevel,
                            fontWeight = FontWeight.Bold,
                            color = if (simulatedRiskLevel.contains("LOW")) GuardianTeal else if (simulatedRiskLevel.contains("MEDIUM")) WarningAmber else EmergencyRed
                        )
                    }
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("Active Alert Tier:", color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Text(simulatedEscalationTier, fontWeight = FontWeight.Bold)
                    }
                }
            }

            // Anomaly Trigger 1: Simulate Route Deviation
            Button(
                onClick = {
                    simulatedDeviationMeters = 650
                    simulatedRiskLevel = "MEDIUM (SCORE: 0.68)"
                    simulatedEscalationTier = "Tier 1 (Soft Alert Active)"
                    scope.launch {
                        snackbarHostState.showSnackbar("Injected 650m route deviation: Risk escalated to MEDIUM.")
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.buttonColors(containerColor = PurplePrimary)
            ) {
                Icon(imageVector = Icons.Default.Warning, contentDescription = "Deviation")
                Spacer(modifier = Modifier.width(8.dp))
                Text("Simulate 650m Route Deviation", fontWeight = FontWeight.Bold, color = Color.White)
            }

            // Anomaly Trigger 2: Simulate Missed Check-In Timeout
            Button(
                onClick = {
                    simulatedMissedCheckIns = 2
                    simulatedDeviationMeters = 900
                    simulatedRiskLevel = "HIGH (SCORE: 0.94)"
                    simulatedEscalationTier = "Tier 2 (Guardian SMS & Location Dispatched)"
                    scope.launch {
                        snackbarHostState.showSnackbar("Injected 2 Missed Check-Ins: Risk escalated to HIGH. Guardian SMS triggered!")
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.buttonColors(containerColor = EmergencyRed)
            ) {
                Icon(imageVector = Icons.Default.Warning, contentDescription = "Timeout")
                Spacer(modifier = Modifier.width(8.dp))
                Text("Simulate Missed Check-In + High Risk", fontWeight = FontWeight.Bold, color = Color.White)
            }

            // Reset Simulation State
            OutlinedButton(
                onClick = {
                    simulatedDeviationMeters = 0
                    simulatedMissedCheckIns = 0
                    simulatedRiskLevel = "LOW (SCORE: 0.12)"
                    simulatedEscalationTier = "Tier 0 (Normal Monitoring)"
                    scope.launch {
                        snackbarHostState.showSnackbar("Simulation reset to Normal state.")
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(50.dp),
                shape = RoundedCornerShape(14.dp)
            ) {
                Icon(imageVector = Icons.Default.Refresh, contentDescription = "Reset")
                Spacer(modifier = Modifier.width(8.dp))
                Text("Reset Simulation Engine", fontWeight = FontWeight.SemiBold)
            }
        }
    }
}
