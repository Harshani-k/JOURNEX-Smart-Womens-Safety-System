package com.journex.safety.ui.screens.fakecall

import androidx.compose.animation.AnimatedVisibility
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
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Call
import androidx.compose.material.icons.filled.CallEnd
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.PhoneInTalk
import androidx.compose.material.icons.filled.Timer
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.journex.safety.ui.components.JournexTopAppBar
import com.journex.safety.ui.theme.EmergencyRed
import com.journex.safety.ui.theme.GuardianTeal
import com.journex.safety.ui.theme.LavenderBorder
import com.journex.safety.ui.theme.LavenderPrimary
import com.journex.safety.ui.theme.PurplePrimary
import kotlinx.coroutines.delay

@Composable
fun FakeCallScreen(
    onNavigateBack: () -> Unit
) {
    var callerName by remember { mutableStateOf("Dad (Urgent)") }
    var delaySeconds by remember { mutableIntStateOf(5) }
    var countdownActive by remember { mutableStateOf(false) }
    var incomingCallActive by remember { mutableStateOf(false) }

    LaunchedEffect(countdownActive, delaySeconds) {
        if (countdownActive && delaySeconds > 0) {
            delay(1000L)
            delaySeconds--
        } else if (countdownActive && delaySeconds == 0) {
            countdownActive = false
            incomingCallActive = true
        }
    }

    if (incomingCallActive) {
        // Fullscreen Realistic Incoming Call Simulator
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(Color(0xFF1A1A24)),
            contentAlignment = Alignment.Center
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(vertical = 60.dp, horizontal = 24.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.SpaceBetween
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Box(
                        modifier = Modifier
                            .size(110.dp)
                            .clip(CircleShape)
                            .background(Color(0xFF2C2C3A)),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = Icons.Default.Person,
                            contentDescription = "Caller",
                            tint = Color.White,
                            modifier = Modifier.size(60.dp)
                        )
                    }

                    Spacer(modifier = Modifier.height(20.dp))

                    Text(
                        text = callerName,
                        style = MaterialTheme.typography.headlineMedium,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )

                    Spacer(modifier = Modifier.height(6.dp))

                    Text(
                        text = "Incoming Call...",
                        style = MaterialTheme.typography.titleMedium,
                        color = Color(0xFFB0B0C0)
                    )
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    // Decline
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Button(
                            onClick = { incomingCallActive = false },
                            shape = CircleShape,
                            modifier = Modifier.size(72.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = EmergencyRed)
                        ) {
                            Icon(imageVector = Icons.Default.CallEnd, contentDescription = "Decline", tint = Color.White)
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        Text("Decline", color = Color.White)
                    }

                    // Accept
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Button(
                            onClick = { incomingCallActive = false },
                            shape = CircleShape,
                            modifier = Modifier.size(72.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = GuardianTeal)
                        ) {
                            Icon(imageVector = Icons.Default.Call, contentDescription = "Accept", tint = Color.White)
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        Text("Accept", color = Color.White)
                    }
                }
            }
        }
    } else {
        Scaffold(
            topBar = {
                JournexTopAppBar(
                    title = "Safe Exit / Fake Call",
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

                Text(
                    text = "Discreetly Excuse Yourself",
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = "Trigger a realistic incoming call to create an immediate, believable pretext to leave uncomfortable or threatening situations.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )

                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    border = CardDefaults.outlinedCardBorder().copy(
                        brush = androidx.compose.ui.graphics.SolidColor(LavenderBorder)
                    )
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text(
                            text = "Caller Identity",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.height(10.dp))
                        OutlinedTextField(
                            value = callerName,
                            onValueChange = { callerName = it },
                            label = { Text("Display Name (e.g. Dad, Warden)") },
                            modifier = Modifier.fillMaxWidth(),
                            shape = RoundedCornerShape(12.dp)
                        )
                    }
                }

                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surface),
                    border = CardDefaults.outlinedCardBorder().copy(
                        brush = androidx.compose.ui.graphics.SolidColor(LavenderBorder)
                    )
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text(
                            text = "Trigger Delay",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold
                        )
                        Spacer(modifier = Modifier.height(10.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                            listOf(5, 15, 30).forEach { sec ->
                                Surface(
                                    modifier = Modifier
                                        .weight(1f)
                                        .clip(RoundedCornerShape(12.dp)),
                                    color = if (delaySeconds == sec) LavenderPrimary else MaterialTheme.colorScheme.surfaceVariant
                                ) {
                                    Button(
                                        onClick = { delaySeconds = sec },
                                        colors = ButtonDefaults.buttonColors(
                                            containerColor = if (delaySeconds == sec) PurplePrimary else Color.Transparent,
                                            contentColor = if (delaySeconds == sec) Color.White else MaterialTheme.colorScheme.onSurface
                                        )
                                    ) {
                                        Text("${sec}s")
                                    }
                                }
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.weight(1f))

                Button(
                    onClick = {
                        countdownActive = true
                    },
                    enabled = !countdownActive,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(56.dp),
                    shape = RoundedCornerShape(16.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = PurplePrimary)
                ) {
                    Icon(imageVector = Icons.Default.PhoneInTalk, contentDescription = "Trigger")
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = if (countdownActive) "Calling in ${delaySeconds}s..." else "Trigger Fake Call Now",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                }

                Spacer(modifier = Modifier.height(16.dp))
            }
        }
    }
}
