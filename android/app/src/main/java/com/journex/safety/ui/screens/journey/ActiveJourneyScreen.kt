package com.journex.safety.ui.screens.journey

import android.app.Activity
import android.content.Intent
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Analytics
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.CloudDone
import androidx.compose.material.icons.filled.CloudUpload
import androidx.compose.material.icons.filled.GpsFixed
import androidx.compose.material.icons.filled.GpsNotFixed
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.Navigation
import androidx.compose.material.icons.filled.Phone
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Security
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material.icons.automirrored.filled.VolumeOff
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.journex.safety.JournexApp
import com.journex.safety.location.GpsLocationFix
import com.journex.safety.location.RealLocationManager
import com.journex.safety.service.JourneyTrackingService
import com.journex.safety.ui.components.JournexTopAppBar
import com.journex.safety.ui.components.SosEmergencyButton
import com.journex.safety.ui.theme.EmergencyRed
import com.journex.safety.ui.theme.EmergencyRedContainer
import com.journex.safety.ui.theme.EmergencyRedDark
import com.journex.safety.ui.theme.GuardianTeal
import com.journex.safety.ui.theme.GuardianTealContainer
import com.journex.safety.ui.theme.LavenderBorder
import com.journex.safety.ui.theme.LavenderPrimary
import com.journex.safety.ui.theme.LavenderSurface
import com.journex.safety.ui.theme.PurpleDark
import com.journex.safety.ui.theme.PurplePrimary
import com.journex.safety.ui.theme.WarningAmber
import com.journex.safety.ui.theme.WarningAmberContainer
import com.journex.safety.utils.PermissionUtils
import com.journex.safety.data.local.entity.CheckInRecordEntity
import com.journex.safety.data.local.entity.SafetyEventEntity
import com.journex.safety.data.remote.model.DelayStatusDto
import com.journex.safety.notification.CheckInNotificationManager
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

enum class TrackingState {
    TRACKING_ACTIVE,
    GPS_PERMISSION_REQUIRED,
    GPS_DISABLED,
    WAITING_FOR_LOCATION,
    SYNC_PENDING,
    TRACKING_STOPPED
}

@Composable
fun ActiveJourneyScreen(
    destination: String?,
    etaText: String?,
    isRealGps: Boolean = true,
    journeyId: Long = 1L,
    onNavigateBackToDashboard: () -> Unit,
    onEndJourney: () -> Unit,
    onTriggerSos: () -> Unit
) {
    val context = LocalContext.current
    val app = context.applicationContext as JournexApp

    var hasLocationPerm by remember { mutableStateOf(PermissionUtils.hasLocationPermission(context)) }
    var isGpsHardwareEnabled by remember { mutableStateOf(RealLocationManager.isLocationEnabled(context)) }

    val permissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestMultiplePermissions()
    ) { perms ->
        hasLocationPerm = perms.values.any { it }
    }

    val isServiceRunning by JourneyTrackingService.isServiceRunning.collectAsState()

    // Local room unsynced count
    val unsyncedCount by app.database.journeyLocationDao()
        .getUnsyncedCountFlow(journeyId)
        .collectAsState(initial = 0)

    // Local Location Manager for live screen coordinates
    val locationManager = remember { RealLocationManager(context) }
    var currentLiveFix by remember { mutableStateOf<GpsLocationFix?>(null) }

    DisposableEffect(hasLocationPerm, isServiceRunning) {
        if (hasLocationPerm && isServiceRunning) {
            locationManager.startUpdates { fix ->
                currentLiveFix = fix
            }
        }
        onDispose {
            locationManager.stopUpdates()
        }
    }

    // Determine current tracking state
    val trackingState = when {
        !hasLocationPerm -> TrackingState.GPS_PERMISSION_REQUIRED
        !isGpsHardwareEnabled -> TrackingState.GPS_DISABLED
        !isServiceRunning -> TrackingState.TRACKING_STOPPED
        currentLiveFix == null -> TrackingState.WAITING_FOR_LOCATION
        unsyncedCount > 0 -> TrackingState.SYNC_PENDING
        else -> TrackingState.TRACKING_ACTIVE
    }

    val scope = rememberCoroutineScope()
    val latestCheckIn by app.checkInRepository.getLatestCheckInFlow(journeyId).collectAsState(initial = null)
    val unsyncedCheckInCount by app.checkInRepository.getUnsyncedCountFlow(journeyId).collectAsState(initial = 0)
    val activeSafetyEvents by app.safetyEventRepository.getActiveEventsFlow(journeyId).collectAsState(initial = emptyList())
    val latestRiskAnalysis by app.riskAnalysisRepository.getLatestRiskFlow(journeyId).collectAsState(initial = null)
    var isEvaluatingRisk by remember { mutableStateOf(false) }

    val activeEmergency by app.emergencyRepository.getActiveEmergencyFlow().collectAsState(initial = null)
    val dispatches by app.emergencyRepository.getDispatchesForEventFlow(activeEmergency?.id ?: -1L).collectAsState(initial = emptyList())
    var showCancelEmergencyDialog by remember { mutableStateOf(false) }

    var delayStatus by remember { mutableStateOf<DelayStatusDto?>(null) }
    var countdownSeconds by remember { mutableStateOf(0L) }
    var riskLevel by remember { mutableStateOf("LOW (NORMAL)") }
    var showExitDialog by remember { mutableStateOf(false) }

    // Sync delivery status for active emergency
    LaunchedEffect(activeEmergency?.id) {
        val eventId = activeEmergency?.id
        val serverId = activeEmergency?.serverEventId
        if (eventId != null) {
            while (true) {
                app.emergencyRepository.fetchDeliveryStatus(eventId, serverId)
                delay(6000L)
            }
        }
    }

    // Initial check-in scheduling if none exists
    LaunchedEffect(journeyId) {
        if (latestCheckIn == null) {
            app.checkInRepository.scheduleNextCheckIn(context, journeyId, intervalMinutes = 15)
        }
        delayStatus = app.checkInRepository.fetchJourneyDelayStatus(journeyId)
        app.safetyEventRepository.fetchRemoteActiveEvents(journeyId)
        app.riskAnalysisRepository.fetchLatestRisk(journeyId)
    }

    // Live countdown loop and missed check-in detection
    LaunchedEffect(latestCheckIn) {
        val checkIn = latestCheckIn
        if (checkIn != null && (checkIn.status == "SCHEDULED" || checkIn.status == "REMINDED")) {
            while (true) {
                val now = System.currentTimeMillis()
                val rem = Math.max(0L, (checkIn.deadlineAt - now) / 1000L)
                countdownSeconds = rem
                if (rem == 0L) {
                    riskLevel = "MEDIUM (MISSED CHECK-IN TIMEOUT)"
                    break
                }
                delay(1000L)
            }
        } else if (checkIn != null && checkIn.status == "MISSED") {
            riskLevel = "MEDIUM (MISSED CHECK-IN TIMEOUT)"
            countdownSeconds = 0L
        } else {
            riskLevel = "LOW (NORMAL)"
            countdownSeconds = 0L
        }
    }

    Scaffold(
        topBar = {
            JournexTopAppBar(
                title = "Live Journey Tracking",
                canNavigateBack = true,
                onNavigateBack = { showExitDialog = true }
            )
        },
        containerColor = MaterialTheme.colorScheme.background
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = 20.dp)
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Spacer(modifier = Modifier.height(4.dp))

            // 1. Transparent GPS Mode & Status Header Banner
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(18.dp),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                border = CardDefaults.outlinedCardBorder().copy(
                    brush = androidx.compose.ui.graphics.SolidColor(LavenderBorder)
                )
            ) {
                Column(modifier = Modifier.padding(18.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Box(
                                modifier = Modifier
                                    .size(12.dp)
                                    .clip(CircleShape)
                                    .background(
                                        when (trackingState) {
                                            TrackingState.TRACKING_ACTIVE -> GuardianTeal
                                            TrackingState.WAITING_FOR_LOCATION -> PurplePrimary
                                            TrackingState.SYNC_PENDING -> GuardianTeal
                                            TrackingState.GPS_PERMISSION_REQUIRED, TrackingState.GPS_DISABLED -> WarningAmber
                                            TrackingState.TRACKING_STOPPED -> Color.Gray
                                        }
                                    )
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = if (isRealGps) "REAL GPS ACTIVE" else "DEMO SIMULATION",
                                style = MaterialTheme.typography.labelLarge,
                                color = if (isRealGps) GuardianTeal else WarningAmber,
                                fontWeight = FontWeight.Bold
                            )
                        }

                        Surface(
                            color = when (trackingState) {
                                TrackingState.TRACKING_ACTIVE -> GuardianTealContainer
                                TrackingState.WAITING_FOR_LOCATION -> LavenderPrimary
                                TrackingState.SYNC_PENDING -> GuardianTealContainer
                                TrackingState.GPS_PERMISSION_REQUIRED, TrackingState.GPS_DISABLED -> WarningAmberContainer
                                TrackingState.TRACKING_STOPPED -> MaterialTheme.colorScheme.surfaceVariant
                            },
                            shape = RoundedCornerShape(8.dp)
                        ) {
                            Text(
                                text = when (trackingState) {
                                    TrackingState.TRACKING_ACTIVE -> "TRACKING ACTIVE"
                                    TrackingState.WAITING_FOR_LOCATION -> "ACQUIRING FIX"
                                    TrackingState.SYNC_PENDING -> "SYNC PENDING"
                                    TrackingState.GPS_PERMISSION_REQUIRED -> "PERMISSION REQ"
                                    TrackingState.GPS_DISABLED -> "GPS DISABLED"
                                    TrackingState.TRACKING_STOPPED -> "STOPPED"
                                },
                                style = MaterialTheme.typography.bodySmall,
                                color = when (trackingState) {
                                    TrackingState.TRACKING_ACTIVE -> GuardianTeal
                                    TrackingState.WAITING_FOR_LOCATION -> PurpleDark
                                    TrackingState.SYNC_PENDING -> GuardianTeal
                                    TrackingState.GPS_PERMISSION_REQUIRED, TrackingState.GPS_DISABLED -> WarningAmber
                                    TrackingState.TRACKING_STOPPED -> Color.Gray
                                },
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp)
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    Text(
                        text = destination ?: "Central Campus",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "Estimated Arrival Window: ${etaText ?: "In 20 mins"}",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            // 2. Real GPS Hardware & Background Tracking Metrics Card
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(18.dp),
                colors = CardDefaults.cardColors(containerColor = LavenderSurface),
                border = CardDefaults.outlinedCardBorder().copy(
                    brush = androidx.compose.ui.graphics.SolidColor(PurplePrimary)
                )
            ) {
                Column(modifier = Modifier.padding(18.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = if (isServiceRunning) Icons.Default.GpsFixed else Icons.Default.GpsNotFixed,
                                contentDescription = "GPS Fix",
                                tint = PurplePrimary,
                                modifier = Modifier.size(22.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "Live Coordinates & Telemetry",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold,
                                color = PurpleDark
                            )
                        }

                        // Background Service Running Badge
                        if (isServiceRunning) {
                            Surface(
                                color = GuardianTealContainer,
                                shape = RoundedCornerShape(6.dp)
                            ) {
                                Text(
                                    text = "Foreground Service ON",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = GuardianTeal,
                                    fontWeight = FontWeight.Bold,
                                    modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                )
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(14.dp))

                    val loc = currentLiveFix
                    if (loc != null) {
                        val latStr = String.format(Locale.US, "%.5f° %s", Math.abs(loc.latitude), if (loc.latitude >= 0) "N" else "S")
                        val lngStr = String.format(Locale.US, "%.5f° %s", Math.abs(loc.longitude), if (loc.longitude >= 0) "E" else "W")

                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Column {
                                Text(text = "Latitude / Longitude", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                                Text(text = "$latStr, $lngStr", style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.Bold)
                            }
                            Column(horizontalAlignment = Alignment.End) {
                                Text(text = "GPS Accuracy", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                                Text(
                                    text = "± ${loc.accuracy.toInt()} m",
                                    style = MaterialTheme.typography.bodyMedium,
                                    fontWeight = FontWeight.Bold,
                                    color = if (loc.accuracy <= 20f) GuardianTeal else WarningAmber
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(10.dp))

                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Column {
                                Text(text = "Last GPS Update", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                                val timeFormat = SimpleDateFormat("HH:mm:ss", Locale.getDefault())
                                Text(text = timeFormat.format(Date(loc.timestamp)), style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.SemiBold)
                            }
                            Column(horizontalAlignment = Alignment.End) {
                                Text(text = "Speed / Heading", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                                val speedKmH = loc.speed?.let { it * 3.6f } ?: 0f
                                Text(text = "${String.format(Locale.US, "%.1f", speedKmH)} km/h", style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.SemiBold)
                            }
                        }
                    } else {
                        Text(
                            text = if (!hasLocationPerm) "Location permission required to stream real GPS coordinates."
                            else if (!isGpsHardwareEnabled) "Device GPS is disabled. Please enable location services in Settings."
                            else if (!isServiceRunning) "Foreground tracking service is currently stopped."
                            else "Acquiring satellite GPS fix... Stand near open sky or window.",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    // Backend Synchronization Status Badge
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = if (unsyncedCount == 0) Icons.Default.CloudDone else Icons.Default.CloudUpload,
                                contentDescription = "Sync",
                                tint = if (unsyncedCount == 0) GuardianTeal else WarningAmber,
                                modifier = Modifier.size(18.dp)
                            )
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(
                                text = if (unsyncedCount == 0) "Backend Storage Synced" else "Sync Pending ($unsyncedCount fixes stored locally)",
                                style = MaterialTheme.typography.bodySmall,
                                fontWeight = FontWeight.SemiBold,
                                color = if (unsyncedCount == 0) GuardianTeal else WarningAmber
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(14.dp))

                    // Start / Stop Foreground Tracking Controls
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        if (!isServiceRunning) {
                            Button(
                                onClick = {
                                    if (PermissionUtils.hasLocationPermission(context)) {
                                        JourneyTrackingService.startService(
                                            context = context,
                                            journeyId = journeyId,
                                            destination = destination ?: "Destination"
                                        )
                                    } else {
                                        permissionLauncher.launch(PermissionUtils.REQUIRED_LOCATION_PERMISSIONS)
                                    }
                                },
                                modifier = Modifier.weight(1f).height(46.dp),
                                shape = RoundedCornerShape(12.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = PurplePrimary)
                            ) {
                                Icon(imageVector = Icons.Default.PlayArrow, contentDescription = "Start GPS")
                                Spacer(modifier = Modifier.width(6.dp))
                                Text("Start Real GPS Tracking", fontWeight = FontWeight.Bold)
                            }
                        } else {
                            OutlinedButton(
                                onClick = {
                                    JourneyTrackingService.stopService(context)
                                },
                                modifier = Modifier.weight(1f).height(46.dp),
                                shape = RoundedCornerShape(12.dp)
                            ) {
                                Icon(imageVector = Icons.Default.Stop, contentDescription = "Stop GPS", tint = EmergencyRed)
                                Spacer(modifier = Modifier.width(6.dp))
                                Text("Stop GPS Tracking", color = EmergencyRed, fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }
            }

            // 2.5 Optional Journey Delay Warning Banner
            val delayInfo = delayStatus
            if (delayInfo != null && delayInfo.isDelayed) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(14.dp),
                    colors = CardDefaults.cardColors(containerColor = WarningAmberContainer),
                    border = CardDefaults.outlinedCardBorder().copy(
                        brush = androidx.compose.ui.graphics.SolidColor(WarningAmber)
                    )
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(14.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            imageVector = Icons.Default.Warning,
                            contentDescription = "Delay Alert",
                            tint = WarningAmber,
                            modifier = Modifier.size(24.dp)
                        )
                        Spacer(modifier = Modifier.width(10.dp))
                        Column {
                            Text(
                                text = "JOURNEY DELAY DETECTED",
                                style = MaterialTheme.typography.labelLarge,
                                fontWeight = FontWeight.Bold,
                                color = Color(0xFF7A4A00)
                            )
                            Text(
                                text = "Trip has exceeded expected arrival by ${delayInfo.minutesDelayed} mins. Check-in intervals adaptively shortened to 5 minutes.",
                                style = MaterialTheme.typography.bodySmall,
                                color = Color(0xFF5A3500)
                            )
                        }
                    }
                }
            }

            // 2.7 Route Deviation & Unexpected Stop Safety Events
            activeSafetyEvents.forEach { event ->
                val isDeviation = event.eventType == "ROUTE_DEVIATION"
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(14.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = if (isDeviation) WarningAmberContainer else LavenderSurface
                    ),
                    border = CardDefaults.outlinedCardBorder().copy(
                        brush = androidx.compose.ui.graphics.SolidColor(
                            if (isDeviation) WarningAmber else PurplePrimary
                        )
                    )
                ) {
                    Column(modifier = Modifier.padding(14.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(
                                    imageVector = if (isDeviation) Icons.Default.Navigation else Icons.Default.Warning,
                                    contentDescription = "Safety Alert",
                                    tint = if (isDeviation) WarningAmber else PurplePrimary,
                                    modifier = Modifier.size(22.dp)
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Text(
                                    text = if (isDeviation) "ROUTE DEVIATION DETECTED" else "UNEXPECTED STOP DETECTED",
                                    style = MaterialTheme.typography.titleSmall,
                                    fontWeight = FontWeight.Bold,
                                    color = if (isDeviation) Color(0xFF7A4A00) else PurpleDark
                                )
                            }

                            Surface(
                                color = if (event.status == "ACKNOWLEDGED") GuardianTealContainer else Color(0xFFFFEBEE),
                                shape = RoundedCornerShape(6.dp)
                            ) {
                                Text(
                                    text = event.status,
                                    style = MaterialTheme.typography.labelSmall,
                                    color = if (event.status == "ACKNOWLEDGED") GuardianTeal else EmergencyRed,
                                    fontWeight = FontWeight.Bold,
                                    modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(6.dp))

                        Text(
                            text = event.triggerReason,
                            style = MaterialTheme.typography.bodySmall,
                            color = Color(0xFF333333)
                        )

                        Spacer(modifier = Modifier.height(10.dp))

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            if (event.status != "ACKNOWLEDGED") {
                                OutlinedButton(
                                    onClick = {
                                        scope.launch {
                                            app.safetyEventRepository.acknowledgeEvent(journeyId, event.id)
                                        }
                                    },
                                    modifier = Modifier.weight(1f).height(40.dp),
                                    shape = RoundedCornerShape(8.dp)
                                ) {
                                    Text("Acknowledge", style = MaterialTheme.typography.labelMedium)
                                }
                            }

                            Button(
                                onClick = {
                                    scope.launch {
                                        app.safetyEventRepository.resolveEvent(
                                            journeyId = journeyId,
                                            localEventId = event.id,
                                            notes = if (isDeviation) "Taking alternate route" else "Expected pause / traffic"
                                        )
                                    }
                                },
                                modifier = Modifier.weight(1f).height(40.dp),
                                shape = RoundedCornerShape(8.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = GuardianTeal)
                            ) {
                                Icon(
                                    imageVector = Icons.Default.CheckCircle,
                                    contentDescription = "Safe",
                                    modifier = Modifier.size(16.dp)
                                )
                                Spacer(modifier = Modifier.width(4.dp))
                                Text("I'm OK / Expected", style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.Bold)
                            }
                        }
                    }
                }
            }

            // 3. Adaptive Safety Check-In Card
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(18.dp),
                colors = CardDefaults.cardColors(containerColor = LavenderSurface),
                border = CardDefaults.outlinedCardBorder().copy(
                    brush = androidx.compose.ui.graphics.SolidColor(PurplePrimary)
                )
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(18.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = Icons.Default.Security,
                                contentDescription = "Safety Check-In",
                                tint = PurplePrimary,
                                modifier = Modifier.size(22.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "Adaptive Safety Check-In",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold,
                                color = PurpleDark
                            )
                        }

                        val chkStatus = latestCheckIn?.status ?: "PENDING"
                        Surface(
                            color = when (chkStatus) {
                                "CONFIRMED_SAFE" -> GuardianTealContainer
                                "MISSED" -> Color(0xFFFFEBEE)
                                else -> LavenderPrimary
                            },
                            shape = RoundedCornerShape(6.dp)
                        ) {
                            Text(
                                text = when (chkStatus) {
                                    "CONFIRMED_SAFE" -> "CONFIRMED SAFE"
                                    "MISSED" -> "CHECK-IN MISSED"
                                    else -> "SCHEDULED"
                                },
                                style = MaterialTheme.typography.labelSmall,
                                color = when (chkStatus) {
                                    "CONFIRMED_SAFE" -> GuardianTeal
                                    "MISSED" -> EmergencyRed
                                    else -> PurpleDark
                                },
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp)
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    val curCheckIn = latestCheckIn
                    if (curCheckIn != null) {
                        val timeFmt = SimpleDateFormat("HH:mm", Locale.getDefault())
                        val schedTimeStr = timeFmt.format(Date(curCheckIn.scheduledAt))

                        when (curCheckIn.status) {
                            "CONFIRMED_SAFE" -> {
                                val respTimeStr = curCheckIn.respondedAt?.let { timeFmt.format(Date(it)) } ?: schedTimeStr
                                Text(
                                    text = "Safety confirmed at $respTimeStr. Guardians notified.",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = GuardianTeal,
                                    fontWeight = FontWeight.SemiBold
                                )
                                Spacer(modifier = Modifier.height(10.dp))
                                Button(
                                    onClick = {
                                        scope.launch {
                                            app.checkInRepository.scheduleNextCheckIn(context, journeyId, intervalMinutes = 15)
                                        }
                                    },
                                    modifier = Modifier.fillMaxWidth().height(46.dp),
                                    shape = RoundedCornerShape(12.dp),
                                    colors = ButtonDefaults.buttonColors(containerColor = PurplePrimary)
                                ) {
                                    Text("Schedule Next Routine Check-In", fontWeight = FontWeight.Bold)
                                }
                            }
                            "MISSED" -> {
                                Text(
                                    text = "Deadline expired without confirmation. Please check in immediately.",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = EmergencyRed,
                                    fontWeight = FontWeight.SemiBold
                                )
                                Spacer(modifier = Modifier.height(10.dp))
                                Button(
                                    onClick = {
                                        scope.launch {
                                            app.checkInRepository.confirmSafety(journeyId, curCheckIn.id)
                                            app.checkInRepository.scheduleNextCheckIn(context, journeyId, intervalMinutes = 15)
                                        }
                                    },
                                    modifier = Modifier.fillMaxWidth().height(48.dp),
                                    shape = RoundedCornerShape(12.dp),
                                    colors = ButtonDefaults.buttonColors(containerColor = GuardianTeal)
                                ) {
                                    Icon(imageVector = Icons.Default.CheckCircle, contentDescription = "Confirm Safe")
                                    Spacer(modifier = Modifier.width(6.dp))
                                    Text("I Am Safe (Re-confirm)", fontWeight = FontWeight.Bold)
                                }
                            }
                            else -> {
                                val mins = countdownSeconds / 60
                                val secs = countdownSeconds % 60
                                val countdownFmt = String.format(Locale.US, "%02d:%02d", mins, secs)

                                Text(
                                    text = "Routine check-in scheduled around $schedTimeStr",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                                Text(
                                    text = "Countdown to deadline: $countdownFmt remaining",
                                    style = MaterialTheme.typography.bodyLarge,
                                    fontWeight = FontWeight.Bold,
                                    color = if (countdownSeconds <= 60L) EmergencyRed else PurpleDark
                                )

                                Spacer(modifier = Modifier.height(12.dp))

                                Button(
                                    onClick = {
                                        scope.launch {
                                            app.checkInRepository.confirmSafety(journeyId, curCheckIn.id)
                                            app.checkInRepository.scheduleNextCheckIn(context, journeyId, intervalMinutes = 15)
                                        }
                                    },
                                    modifier = Modifier.fillMaxWidth().height(50.dp),
                                    shape = RoundedCornerShape(14.dp),
                                    colors = ButtonDefaults.buttonColors(containerColor = GuardianTeal)
                                ) {
                                    Icon(imageVector = Icons.Default.CheckCircle, contentDescription = "Confirm Safe")
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text(
                                        text = "I Am Safe (Confirm)",
                                        style = MaterialTheme.typography.titleMedium,
                                        fontWeight = FontWeight.Bold,
                                        color = Color.White
                                    )
                                }
                            }
                        }

                        Spacer(modifier = Modifier.height(10.dp))

                        // Offline sync badge
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = if (curCheckIn.syncStatus == "PENDING") "Local Queue (Sync Pending)" else "Synced with JOURNEX Cloud",
                                style = MaterialTheme.typography.labelSmall,
                                color = if (curCheckIn.syncStatus == "PENDING") WarningAmber else GuardianTeal
                            )
                            if (unsyncedCheckInCount > 0) {
                                Text(
                                    text = "$unsyncedCheckInCount pending action(s)",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                    } else {
                        Text(
                            text = "Initializing next adaptive safety check-in...",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }

            // 4. AI/ML-Based Risk Analysis (Random Forest)
            val currentRisk = latestRiskAnalysis
            val riskCat = currentRisk?.riskCategory ?: "LOW"
            val riskScore = currentRisk?.riskScore ?: 0.05f
            val isInsufficient = currentRisk == null || currentRisk.isInsufficientData

            val categoryColor = when (riskCat) {
                "LOW" -> GuardianTeal
                "MODERATE" -> WarningAmber
                "HIGH" -> Color(0xFFE65100)
                "CRITICAL" -> EmergencyRed
                else -> GuardianTeal
            }
            val categoryContainerColor = when (riskCat) {
                "LOW" -> GuardianTealContainer
                "MODERATE" -> WarningAmberContainer
                "HIGH" -> Color(0xFFFFE0B2)
                "CRITICAL" -> Color(0xFFFFCDD2)
                else -> GuardianTealContainer
            }

            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(18.dp),
                colors = CardDefaults.cardColors(containerColor = LavenderSurface),
                border = CardDefaults.outlinedCardBorder().copy(
                    brush = androidx.compose.ui.graphics.SolidColor(
                        if (riskCat in listOf("HIGH", "CRITICAL")) categoryColor else PurplePrimary
                    )
                )
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(18.dp)
                ) {
                    // Header row
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Icon(
                                imageVector = Icons.Default.Analytics,
                                contentDescription = "AI Risk",
                                tint = PurplePrimary,
                                modifier = Modifier.size(24.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Column {
                                Text(
                                    text = "AI Journey Risk Assessment",
                                    style = MaterialTheme.typography.titleMedium,
                                    fontWeight = FontWeight.Bold,
                                    color = PurpleDark
                                )
                                Text(
                                    text = "Model: ${currentRisk?.modelVersion ?: "1.0.0-rf"} (Random Forest)",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }

                        Surface(
                            color = categoryContainerColor,
                            shape = RoundedCornerShape(8.dp)
                        ) {
                            Text(
                                text = "$riskCat RISK",
                                style = MaterialTheme.typography.labelMedium,
                                fontWeight = FontWeight.Bold,
                                color = categoryColor,
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(14.dp))

                    // Score bar & percentage
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "Calculated Risk Score",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Text(
                            text = "${(riskScore * 100).toInt()}% (${String.format(Locale.US, "%.2f", riskScore)})",
                            style = MaterialTheme.typography.bodyMedium,
                            fontWeight = FontWeight.Bold,
                            color = categoryColor
                        )
                    }

                    Spacer(modifier = Modifier.height(6.dp))

                    LinearProgressIndicator(
                        progress = { riskScore.coerceIn(0f, 1f) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(8.dp)
                            .clip(RoundedCornerShape(4.dp)),
                        color = categoryColor,
                        trackColor = LavenderBorder
                    )

                    Spacer(modifier = Modifier.height(14.dp))

                    // Contributing Factors Section
                    Text(
                        text = "Key Contributing Factors",
                        style = MaterialTheme.typography.labelLarge,
                        fontWeight = FontWeight.Bold,
                        color = PurpleDark
                    )

                    Spacer(modifier = Modifier.height(6.dp))

                    if (isInsufficient) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .background(LavenderPrimary.copy(alpha = 0.2f), RoundedCornerShape(8.dp))
                                .padding(10.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                imageVector = Icons.Default.Info,
                                contentDescription = "Info",
                                tint = PurplePrimary,
                                modifier = Modifier.size(20.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "Collecting journey telemetry... Risk analysis updates as GPS fixes and check-in responses arrive.",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    } else {
                        val factors = currentRisk?.contributingFactorsJson?.let {
                            app.riskAnalysisRepository.parseContributingFactors(it)
                        } ?: emptyList()

                        if (factors.isEmpty()) {
                            Text(
                                text = "• Normal travel progress. No anomalous risk indicators detected.",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        } else {
                            factors.forEach { factor ->
                                val impactColor = when (factor.impact) {
                                    "CRITICAL" -> EmergencyRed
                                    "HIGH" -> Color(0xFFE65100)
                                    "MODERATE" -> WarningAmber
                                    "POSITIVE" -> GuardianTeal
                                    else -> MaterialTheme.colorScheme.onSurfaceVariant
                                }

                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(vertical = 3.dp),
                                    verticalAlignment = Alignment.Top
                                ) {
                                    Text(
                                        text = "•",
                                        fontWeight = FontWeight.Bold,
                                        color = impactColor,
                                        modifier = Modifier.padding(end = 6.dp)
                                    )
                                    Column {
                                        Row(verticalAlignment = Alignment.CenterVertically) {
                                            Text(
                                                text = factor.factor,
                                                style = MaterialTheme.typography.bodySmall,
                                                fontWeight = FontWeight.Bold,
                                                color = PurpleDark
                                            )
                                            Spacer(modifier = Modifier.width(6.dp))
                                            Surface(
                                                color = impactColor.copy(alpha = 0.15f),
                                                shape = RoundedCornerShape(4.dp)
                                            ) {
                                                Text(
                                                    text = factor.impact,
                                                    style = MaterialTheme.typography.labelSmall,
                                                    fontWeight = FontWeight.Bold,
                                                    color = impactColor,
                                                    modifier = Modifier.padding(horizontal = 4.dp, vertical = 1.dp)
                                                )
                                            }
                                        }
                                        Text(
                                            text = factor.description,
                                            style = MaterialTheme.typography.bodySmall,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant
                                        )
                                    }
                                }
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(12.dp))

                    // Re-Evaluate Button
                    OutlinedButton(
                        onClick = {
                            if (!isEvaluatingRisk) {
                                isEvaluatingRisk = true
                                scope.launch {
                                    app.riskAnalysisRepository.requestRiskAnalysis(journeyId, forceRecompute = true)
                                    isEvaluatingRisk = false
                                }
                            }
                        },
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(42.dp),
                        shape = RoundedCornerShape(10.dp),
                        enabled = !isEvaluatingRisk
                    ) {
                        Icon(
                            imageVector = Icons.Default.Refresh,
                            contentDescription = "Re-Evaluate",
                            tint = PurplePrimary,
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = if (isEvaluatingRisk) "Evaluating Risk Model..." else "Re-Evaluate Risk",
                            style = MaterialTheme.typography.labelMedium,
                            fontWeight = FontWeight.Bold,
                            color = PurplePrimary
                        )
                    }

                    Spacer(modifier = Modifier.height(8.dp))

                    // Safety & Transparency Disclaimer
                    Text(
                        text = "Disclaimer: Algorithmic risk evaluation based on journey telemetry. Does not replace personal safety judgment or predict crime.",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f),
                        fontSize = 10.sp,
                        lineHeight = 13.sp
                    )
                }
            }

            // 5. Active Emergency & Multi-Level Escalation Monitor Card
            if (activeEmergency != null) {
                val emergency = activeEmergency!!
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(18.dp),
                    colors = CardDefaults.cardColors(containerColor = EmergencyRedContainer),
                    border = CardDefaults.outlinedCardBorder().copy(
                        brush = androidx.compose.ui.graphics.SolidColor(EmergencyRed)
                    )
                ) {
                    Column(modifier = Modifier.padding(18.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Icon(
                                    imageVector = Icons.Default.Warning,
                                    contentDescription = "Active Emergency",
                                    tint = EmergencyRed,
                                    modifier = Modifier.size(24.dp)
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Text(
                                    text = "EMERGENCY ACTIVE",
                                    style = MaterialTheme.typography.titleMedium,
                                    fontWeight = FontWeight.ExtraBold,
                                    color = EmergencyRedDark
                                )
                            }
                            Surface(
                                color = EmergencyRed,
                                shape = RoundedCornerShape(6.dp)
                            ) {
                                Text(
                                    text = "LEVEL ${emergency.currentEscalationLevel} OF ${emergency.maxEscalationLevel}",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = Color.White,
                                    fontWeight = FontWeight.Bold,
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp)
                                )
                            }
                        }

                        Spacer(modifier = Modifier.height(10.dp))

                        Text(
                            text = "Trigger Type: ${emergency.triggerType.replace('_', ' ')}",
                            style = MaterialTheme.typography.bodyMedium,
                            fontWeight = FontWeight.Bold,
                            color = EmergencyRedDark
                        )

                        if (emergency.latitude != null && emergency.longitude != null) {
                            Text(
                                text = "Dispatched Location: ${String.format(Locale.US, "%.5f", emergency.latitude)}, ${String.format(Locale.US, "%.5f", emergency.longitude)}",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }

                        Spacer(modifier = Modifier.height(10.dp))

                        Text(
                            text = "Guardian Notification Status:",
                            style = MaterialTheme.typography.labelMedium,
                            fontWeight = FontWeight.Bold,
                            color = PurpleDark
                        )
                        Spacer(modifier = Modifier.height(6.dp))

                        if (dispatches.isEmpty()) {
                            Text(
                                text = "• Dispatches recorded in emergency queue (SMS pending)",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        } else {
                            dispatches.forEach { dispatch ->
                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(vertical = 3.dp),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Column {
                                        Text(
                                            text = "${dispatch.contactName} (${dispatch.contactPhone})",
                                            style = MaterialTheme.typography.bodySmall,
                                            fontWeight = FontWeight.SemiBold
                                        )
                                        Text(
                                            text = "Escalation Level ${dispatch.escalationLevel} • ${dispatch.channel}",
                                            style = MaterialTheme.typography.labelSmall,
                                            color = MaterialTheme.colorScheme.onSurfaceVariant
                                        )
                                    }
                                    Surface(
                                        color = if (dispatch.status == "DELIVERED") GuardianTealContainer else WarningAmberContainer,
                                        shape = RoundedCornerShape(4.dp)
                                    ) {
                                        Text(
                                            text = dispatch.status,
                                            style = MaterialTheme.typography.labelSmall,
                                            fontWeight = FontWeight.Bold,
                                            color = if (dispatch.status == "DELIVERED") GuardianTeal else Color(0xFFB78103),
                                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                        )
                                    }
                                }
                            }
                        }

                        Spacer(modifier = Modifier.height(14.dp))

                        // Action Buttons: I Am Safe, Escalate, Call Guardian
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Button(
                                onClick = { showCancelEmergencyDialog = true },
                                modifier = Modifier.weight(1f).height(44.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = GuardianTeal),
                                shape = RoundedCornerShape(10.dp)
                            ) {
                                Icon(Icons.Default.CheckCircle, contentDescription = null, modifier = Modifier.size(16.dp))
                                Spacer(modifier = Modifier.width(4.dp))
                                Text("I Am Safe", fontWeight = FontWeight.Bold, fontSize = 12.sp)
                            }

                            if (emergency.currentEscalationLevel < emergency.maxEscalationLevel) {
                                OutlinedButton(
                                    onClick = {
                                        scope.launch {
                                            app.emergencyRepository.escalateEmergency(emergency.id, emergency.serverEventId)
                                        }
                                    },
                                    modifier = Modifier.weight(1f).height(44.dp),
                                    shape = RoundedCornerShape(10.dp)
                                ) {
                                    Text("Escalate Level", fontWeight = FontWeight.Bold, fontSize = 11.sp, color = EmergencyRedDark)
                                }
                            }

                            if (dispatches.isNotEmpty()) {
                                val primaryPhone = dispatches.first().contactPhone
                                OutlinedButton(
                                    onClick = {
                                        val intent = Intent(Intent.ACTION_DIAL, Uri.parse("tel:$primaryPhone"))
                                        context.startActivity(intent)
                                    },
                                    modifier = Modifier.weight(1f).height(44.dp),
                                    shape = RoundedCornerShape(10.dp)
                                ) {
                                    Icon(Icons.Default.Phone, contentDescription = null, modifier = Modifier.size(16.dp), tint = PurpleDark)
                                    Spacer(modifier = Modifier.width(4.dp))
                                    Text("Call", fontWeight = FontWeight.Bold, fontSize = 12.sp, color = PurpleDark)
                                }
                            }
                        }
                    }
                }
            }

            // 6. SOS Emergency Button (5-second countdown with instant touch response)
            SosEmergencyButton(
                onEmergencyTriggered = {
                    scope.launch {
                        app.emergencyRepository.triggerEmergencySos(
                            journeyId = journeyId,
                            triggerType = "MANUAL_SOS",
                            latitude = currentLiveFix?.latitude,
                            longitude = currentLiveFix?.longitude,
                            accuracy = currentLiveFix?.accuracy
                        )
                    }
                    onTriggerSos()
                }
            )

            // 7. Discreet Silent Safety Alert
            OutlinedButton(
                onClick = {
                    scope.launch {
                        app.emergencyRepository.triggerEmergencySos(
                            journeyId = journeyId,
                            triggerType = "SILENT_ALERT",
                            latitude = currentLiveFix?.latitude,
                            longitude = currentLiveFix?.longitude,
                            accuracy = currentLiveFix?.accuracy
                        )
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(44.dp),
                shape = RoundedCornerShape(12.dp)
            ) {
                Icon(
                    imageVector = Icons.AutoMirrored.Filled.VolumeOff,
                    contentDescription = "Silent Alert",
                    tint = PurplePrimary,
                    modifier = Modifier.size(18.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "Discreet Silent Alert (No Sirens)",
                    style = MaterialTheme.typography.labelMedium,
                    fontWeight = FontWeight.Bold,
                    color = PurplePrimary
                )
            }

            // 8. Arrived Safely End Journey Button
            Button(
                onClick = {
                    JourneyTrackingService.stopService(context)
                    onEndJourney()
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.surfaceVariant)
            ) {
                Text(
                    text = "End Journey (Arrived Safely)",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            Spacer(modifier = Modifier.height(16.dp))
        }
    }

    if (showCancelEmergencyDialog && activeEmergency != null) {
        val emId = activeEmergency!!.id
        val srvId = activeEmergency!!.serverEventId
        AlertDialog(
            onDismissRequest = { showCancelEmergencyDialog = false },
            icon = {
                Icon(
                    imageVector = Icons.Default.CheckCircle,
                    contentDescription = "Confirm Safe",
                    tint = GuardianTeal,
                    modifier = Modifier.size(36.dp)
                )
            },
            title = { Text("Confirm You Are Safe") },
            text = { Text("This will cancel the active emergency alert and send safe confirmation notices to all contacted guardians.") },
            confirmButton = {
                Button(
                    onClick = {
                        showCancelEmergencyDialog = false
                        scope.launch {
                            app.emergencyRepository.cancelEmergency(
                                eventId = emId,
                                serverEventId = srvId,
                                cancellationReason = "Traveler confirmed safe via app"
                            )
                        }
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = GuardianTeal)
                ) {
                    Text("Confirm Safe", color = Color.White, fontWeight = FontWeight.Bold)
                }
            },
            dismissButton = {
                TextButton(onClick = { showCancelEmergencyDialog = false }) {
                    Text("Keep Alert Active")
                }
            }
        )
    }

    if (showExitDialog) {
        AlertDialog(
            onDismissRequest = { showExitDialog = false },
            title = { Text("Leave Live Monitoring Screen?") },
            text = { Text("Your journey monitoring and foreground GPS service will continue in the background. Return to Dashboard?") },
            confirmButton = {
                TextButton(
                    onClick = {
                        showExitDialog = false
                        onNavigateBackToDashboard()
                    }
                ) {
                    Text("Return to Dashboard", fontWeight = FontWeight.Bold, color = PurplePrimary)
                }
            },
            dismissButton = {
                TextButton(onClick = { showExitDialog = false }) {
                    Text("Stay on Tracking")
                }
            }
        )
    }
}
