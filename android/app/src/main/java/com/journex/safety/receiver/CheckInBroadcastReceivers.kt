package com.journex.safety.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import com.journex.safety.JournexApp
import com.journex.safety.data.repository.CheckInRepository
import com.journex.safety.notification.CheckInNotificationManager
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class CheckInAlarmReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val journeyId = intent.getLongExtra("EXTRA_JOURNEY_ID", 1L)
        val checkInId = intent.getLongExtra("EXTRA_CHECKIN_ID", 0L)
        Log.i("CheckInAlarmReceiver", "Received check-in alarm trigger for journeyId=$journeyId")
        CheckInNotificationManager.showCheckInReminder(
            context = context,
            journeyId = journeyId,
            checkInId = checkInId
        )
    }
}

class CheckInActionReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == "com.journex.safety.action.CONFIRM_SAFE") {
            val journeyId = intent.getLongExtra("EXTRA_JOURNEY_ID", 1L)
            val checkInId = intent.getLongExtra("EXTRA_CHECKIN_ID", 0L)
            Log.i("CheckInActionReceiver", "User tapped 'I AM SAFE' from notification for journeyId=$journeyId")

            // Dismiss notification immediately
            CheckInNotificationManager.cancelNotification(context)

            // Perform background safe confirmation via repository
            val app = context.applicationContext as JournexApp
            val repository = CheckInRepository(app.database)
            CoroutineScope(Dispatchers.IO).launch {
                repository.confirmSafety(journeyId, checkInId)
            }
        }
    }
}
