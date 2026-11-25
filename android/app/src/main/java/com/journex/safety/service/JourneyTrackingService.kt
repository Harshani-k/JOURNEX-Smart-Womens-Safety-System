package com.journex.safety.service

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.journex.safety.MainActivity
import com.journex.safety.R
import com.journex.safety.data.local.JournexDatabase
import com.journex.safety.data.local.entity.JourneyLocationEntity
import com.journex.safety.data.repository.LocationSyncRepository
import com.journex.safety.location.RealLocationManager
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class JourneyTrackingService : Service() {

    private val serviceScope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private lateinit var locationManager: RealLocationManager
    private lateinit var syncRepository: LocationSyncRepository

    private var currentJourneyId: Long = -1L
    private var currentDestination: String = "Destination"
    private var authToken: String? = null

    companion object {
        const val CHANNEL_ID = "journex_journey_tracking_channel"
        const val NOTIFICATION_ID = 2001

        const val ACTION_START_TRACKING = "com.journex.safety.action.START_TRACKING"
        const val ACTION_STOP_TRACKING = "com.journex.safety.action.STOP_TRACKING"

        const val EXTRA_JOURNEY_ID = "extra_journey_id"
        const val EXTRA_DESTINATION = "extra_destination"
        const val EXTRA_AUTH_TOKEN = "extra_auth_token"

        private val _isServiceRunning = MutableStateFlow(false)
        val isServiceRunning: StateFlow<Boolean> = _isServiceRunning.asStateFlow()

        private val _lastFixTime = MutableStateFlow<Long?>(null)
        val lastFixTime: StateFlow<Long?> = _lastFixTime.asStateFlow()

        fun startService(context: Context, journeyId: Long, destination: String, token: String? = null) {
            val intent = Intent(context, JourneyTrackingService::class.java).apply {
                action = ACTION_START_TRACKING
                putExtra(EXTRA_JOURNEY_ID, journeyId)
                putExtra(EXTRA_DESTINATION, destination)
                putExtra(EXTRA_AUTH_TOKEN, token)
            }
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }

        fun stopService(context: Context) {
            val intent = Intent(context, JourneyTrackingService::class.java).apply {
                action = ACTION_STOP_TRACKING
            }
            context.startService(intent)
        }
    }

    override fun onCreate() {
        super.onCreate()
        locationManager = RealLocationManager(this)
        val db = JournexDatabase.getDatabase(this)
        syncRepository = LocationSyncRepository(db.journeyLocationDao())
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_START_TRACKING -> {
                val journeyId = intent.getLongExtra(EXTRA_JOURNEY_ID, -1L)
                val destination = intent.getStringExtra(EXTRA_DESTINATION) ?: "Destination"
                val token = intent.getStringExtra(EXTRA_AUTH_TOKEN)
                startTracking(journeyId, destination, token)
            }
            ACTION_STOP_TRACKING -> {
                stopTracking()
            }
        }
        return START_STICKY
    }

    private fun startTracking(journeyId: Long, destination: String, token: String?) {
        currentJourneyId = journeyId
        currentDestination = destination
        authToken = token

        val notification = buildNotification("Monitoring journey to $destination (GPS active)")
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(NOTIFICATION_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_LOCATION)
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }

        _isServiceRunning.value = true

        locationManager.startUpdates { fix ->
            _lastFixTime.value = fix.timestamp
            serviceScope.launch {
                val db = JournexDatabase.getDatabase(this@JourneyTrackingService)
                val entity = JourneyLocationEntity(
                    journeyId = currentJourneyId,
                    latitude = fix.latitude,
                    longitude = fix.longitude,
                    accuracy = fix.accuracy,
                    altitude = fix.altitude,
                    speed = fix.speed,
                    bearing = fix.bearing,
                    recordedAt = fix.timestamp,
                    syncStatus = "PENDING"
                )
                db.journeyLocationDao().insertLocation(entity)

                // Trigger network synchronization if token is available
                authToken?.let { bearer ->
                    syncRepository.syncPendingLocations(currentJourneyId, bearer)
                }

                // Update notification text
                val timeStr = SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(Date(fix.timestamp))
                val updateNote = buildNotification("Live GPS Active: ±${fix.accuracy.toInt()}m at $timeStr")
                val nm = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
                nm.notify(NOTIFICATION_ID, updateNote)
            }
        }
    }

    private fun stopTracking() {
        locationManager.stopUpdates()
        _isServiceRunning.value = false
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            stopForeground(STOP_FOREGROUND_REMOVE)
        } else {
            @Suppress("DEPRECATION")
            stopForeground(true)
        }
        stopSelf()
    }

    private fun buildNotification(contentText: String): Notification {
        val launchIntent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_SINGLE_TOP
        }
        val pendingLaunch = PendingIntent.getActivity(
            this,
            0,
            launchIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val stopIntent = Intent(this, JourneyTrackingService::class.java).apply {
            action = ACTION_STOP_TRACKING
        }
        val pendingStop = PendingIntent.getService(
            this,
            1,
            stopIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("JOURNEX Safety Monitoring")
            .setContentText(contentText)
            .setSmallIcon(R.drawable.ic_launcher)
            .setContentIntent(pendingLaunch)
            .addAction(R.drawable.ic_launcher, "Stop Tracking", pendingStop)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "JOURNEX Journey Tracking",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Foreground service notification for active journey location tracking"
                setShowBadge(false)
            }
            val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            manager.createNotificationChannel(channel)
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        locationManager.stopUpdates()
        _isServiceRunning.value = false
        serviceScope.cancel()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
