package com.journex.safety.notification

import android.app.AlarmManager
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import android.util.Log
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.journex.safety.MainActivity
import com.journex.safety.R
import com.journex.safety.receiver.CheckInActionReceiver
import com.journex.safety.receiver.CheckInAlarmReceiver

object CheckInNotificationManager {

    private const val TAG = "CheckInNotifManager"
    const val CHANNEL_ID = "journex_checkin_channel"
    const val NOTIFICATION_ID = 3001

    fun createNotificationChannel(context: Context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val name = "JOURNEX Safety Check-In"
            val descriptionText = "Urgent reminders for scheduled safety check-ins"
            val importance = NotificationManager.IMPORTANCE_HIGH
            val channel = NotificationChannel(CHANNEL_ID, name, importance).apply {
                description = descriptionText
                enableVibration(true)
                setShowBadge(true)
            }
            val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            notificationManager.createNotificationChannel(channel)
        }
    }

    fun showCheckInReminder(
        context: Context,
        journeyId: Long,
        checkInId: Long,
        secondsRemaining: Int = 180
    ) {
        createNotificationChannel(context)

        // 1. Deep link to Active Journey Screen
        val openIntent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            putExtra("EXTRA_NAVIGATE_TO", "active_journey")
            putExtra("EXTRA_JOURNEY_ID", journeyId)
        }
        val openPendingIntent = PendingIntent.getActivity(
            context,
            101,
            openIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        // 2. Quick "I AM SAFE" action from notification shade
        val safeIntent = Intent(context, CheckInActionReceiver::class.java).apply {
            action = "com.journex.safety.action.CONFIRM_SAFE"
            putExtra("EXTRA_JOURNEY_ID", journeyId)
            putExtra("EXTRA_CHECKIN_ID", checkInId)
        }
        val safePendingIntent = PendingIntent.getBroadcast(
            context,
            102,
            safeIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_launcher)
            .setContentTitle("JOURNEX Safety Check-In")
            .setContentText("Please verify your safety. ${secondsRemaining}s remaining.")
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setAutoCancel(true)
            .setContentIntent(openPendingIntent)
            .addAction(R.drawable.ic_launcher, "I AM SAFE", safePendingIntent)
            .build()

        try {
            NotificationManagerCompat.from(context).notify(NOTIFICATION_ID, notification)
            Log.i(TAG, "Posted safety check-in reminder notification.")
        } catch (e: SecurityException) {
            Log.w(TAG, "Notification permission missing: ${e.message}")
        }
    }

    fun cancelNotification(context: Context) {
        NotificationManagerCompat.from(context).cancel(NOTIFICATION_ID)
    }

    fun scheduleCheckInAlarm(context: Context, journeyId: Long, checkInId: Long, triggerAtMillis: Long) {
        val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as? AlarmManager ?: return
        val intent = Intent(context, CheckInAlarmReceiver::class.java).apply {
            putExtra("EXTRA_JOURNEY_ID", journeyId)
            putExtra("EXTRA_CHECKIN_ID", checkInId)
        }
        val pendingIntent = PendingIntent.getBroadcast(
            context,
            201,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                alarmManager.setAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, triggerAtMillis, pendingIntent)
            } else {
                alarmManager.set(AlarmManager.RTC_WAKEUP, triggerAtMillis, pendingIntent)
            }
            Log.i(TAG, "Scheduled check-in alarm for journeyId=$journeyId at $triggerAtMillis")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to schedule alarm: ${e.message}")
        }
    }

    fun cancelCheckInAlarm(context: Context) {
        val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as? AlarmManager ?: return
        val intent = Intent(context, CheckInAlarmReceiver::class.java)
        val pendingIntent = PendingIntent.getBroadcast(
            context,
            201,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        alarmManager.cancel(pendingIntent)
    }

    const val SAFETY_EVENT_NOTIFICATION_ID = 3002

    fun showRouteDeviationAlert(context: Context, journeyId: Long, eventId: Long, deviationMeters: Double) {
        createNotificationChannel(context)
        val openIntent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            putExtra("EXTRA_NAVIGATE_TO", "active_journey")
            putExtra("EXTRA_JOURNEY_ID", journeyId)
        }
        val openPendingIntent = PendingIntent.getActivity(
            context,
            103,
            openIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_launcher)
            .setContentTitle("JOURNEX: Route Deviation Detected")
            .setContentText("You are ${deviationMeters.toInt()}m away from planned corridor. Tap to verify or acknowledge.")
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setAutoCancel(true)
            .setContentIntent(openPendingIntent)
            .build()

        try {
            NotificationManagerCompat.from(context).notify(SAFETY_EVENT_NOTIFICATION_ID, notification)
            Log.i(TAG, "Posted Route Deviation notification.")
        } catch (e: SecurityException) {
            Log.w(TAG, "Notification permission missing: ${e.message}")
        }
    }

    fun showUnexpectedStopAlert(context: Context, journeyId: Long, eventId: Long, durationMins: Int) {
        createNotificationChannel(context)
        val openIntent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            putExtra("EXTRA_NAVIGATE_TO", "active_journey")
            putExtra("EXTRA_JOURNEY_ID", journeyId)
        }
        val openPendingIntent = PendingIntent.getActivity(
            context,
            104,
            openIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(context, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_launcher)
            .setContentTitle("JOURNEX: Unexpected Stop Alert")
            .setContentText("Vehicle stationary for $durationMins mins without progress. Tap to verify your safety.")
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setAutoCancel(true)
            .setContentIntent(openPendingIntent)
            .build()

        try {
            NotificationManagerCompat.from(context).notify(SAFETY_EVENT_NOTIFICATION_ID, notification)
            Log.i(TAG, "Posted Unexpected Stop notification.")
        } catch (e: SecurityException) {
            Log.w(TAG, "Notification permission missing: ${e.message}")
        }
    }
}
