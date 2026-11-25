package com.journex.safety.data.repository

import android.content.Context
import android.util.Log
import com.journex.safety.data.local.JournexDatabase
import com.journex.safety.data.local.entity.CheckInRecordEntity
import com.journex.safety.data.remote.RetrofitClient
import com.journex.safety.data.remote.model.CheckInConfirmRequest
import com.journex.safety.data.remote.model.CheckInCreateRequest
import com.journex.safety.data.remote.model.DelayStatusDto
import com.journex.safety.notification.CheckInNotificationManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.withContext
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone
import java.util.UUID

class CheckInRepository(
    private val database: JournexDatabase,
    private val authTokenProvider: () -> String? = { null }
) {
    private val checkInDao = database.checkInRecordDao()
    private val checkInApi = RetrofitClient.checkInApi

    companion object {
        private const val TAG = "CheckInRepository"
        private val isoFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US).apply {
            timeZone = TimeZone.getTimeZone("UTC")
        }
    }

    fun getLatestCheckInFlow(journeyId: Long): Flow<CheckInRecordEntity?> {
        return checkInDao.getLatestCheckInFlow(journeyId)
    }

    fun getUnsyncedCountFlow(journeyId: Long): Flow<Int> {
        return checkInDao.getUnsyncedCheckInCountFlow(journeyId)
    }

    /**
     * Initializes a new scheduled check-in locally and attempts to sync to backend.
     */
    suspend fun scheduleNextCheckIn(
        context: Context,
        journeyId: Long,
        intervalMinutes: Int = 15,
        gracePeriodMinutes: Int = 3
    ): CheckInRecordEntity = withContext(Dispatchers.IO) {
        val now = System.currentTimeMillis()
        val scheduledAt = now + (intervalMinutes * 60 * 1000L)
        val deadlineAt = scheduledAt + (gracePeriodMinutes * 60 * 1000L)
        val clientActionId = UUID.randomUUID().toString()

        val entity = CheckInRecordEntity(
            journeyId = journeyId,
            timestamp = now,
            status = "SCHEDULED",
            scheduledAt = scheduledAt,
            deadlineAt = deadlineAt,
            clientActionId = clientActionId,
            syncStatus = "PENDING"
        )
        val localId = checkInDao.insert(entity)
        val inserted = entity.copy(id = localId)

        // Schedule system notification alarm
        CheckInNotificationManager.scheduleCheckInAlarm(
            context = context,
            journeyId = journeyId,
            checkInId = localId,
            triggerAtMillis = scheduledAt
        )

        // Try backend sync if token available
        val token = authTokenProvider()
        if (token != null) {
            try {
                val req = CheckInCreateRequest(
                    scheduledAt = isoFormat.format(Date(scheduledAt)),
                    deadlineAt = isoFormat.format(Date(deadlineAt)),
                    clientActionId = clientActionId
                )
                val resp = checkInApi.createCheckIn(journeyId, req, "Bearer $token")
                if (resp.isSuccessful && resp.body()?.data != null) {
                    val serverDto = resp.body()!!.data!!
                    checkInDao.markSynced(localId, serverDto.id)
                    Log.i(TAG, "Synced scheduled check-in $localId with backend id ${serverDto.id}")
                }
            } catch (e: Exception) {
                Log.w(TAG, "Offline or backend unreachable for schedule check-in: ${e.message}")
            }
        }

        inserted
    }

    /**
     * Confirms safety when user taps "I Am Safe".
     * Performs optimistic local update, records device response timestamp,
     * and attempts remote sync or queues offline.
     */
    suspend fun confirmSafety(journeyId: Long, checkInId: Long): CheckInRecordEntity? = withContext(Dispatchers.IO) {
        val checkIn = if (checkInId > 0) {
            checkInDao.getLatestCheckIn(journeyId)?.takeIf { it.id == checkInId }
        } else {
            checkInDao.getLatestCheckIn(journeyId)
        } ?: return@withContext null

        val now = System.currentTimeMillis()

        // Check if deadline already passed locally
        if (now > checkIn.deadlineAt) {
            Log.w(TAG, "Cannot confirm safety: Check-in deadline expired ($now > ${checkIn.deadlineAt})")
            checkInDao.updateStatus(checkIn.id, "MISSED", checkIn.respondedAt, "SYNCED")
            return@withContext checkIn.copy(status = "MISSED")
        }

        // Optimistic update
        checkInDao.updateStatus(
            id = checkIn.id,
            status = "CONFIRMED_SAFE",
            respondedAt = now,
            syncStatus = "PENDING"
        )

        val updated = checkIn.copy(
            status = "CONFIRMED_SAFE",
            respondedAt = now,
            syncStatus = "PENDING"
        )

        // Sync with backend
        val token = authTokenProvider()
        if (token != null && checkIn.serverCheckinId != null) {
            try {
                val req = CheckInConfirmRequest(
                    respondedAt = isoFormat.format(Date(now)),
                    responseType = "MANUAL_TAP",
                    clientActionId = checkIn.clientActionId
                )
                val resp = checkInApi.confirmCheckIn(checkIn.serverCheckinId, req, "Bearer $token")
                if (resp.isSuccessful) {
                    checkInDao.updateStatus(checkIn.id, "CONFIRMED_SAFE", now, "SYNCED")
                    Log.i(TAG, "Successfully synced CONFIRMED_SAFE for checkin ${checkIn.id}")
                } else if (resp.code() == 409) {
                    // Conflict / Expired on server: Never silently convert late offline confirmation
                    Log.w(TAG, "Server rejected confirmation: marked MISSED by server.")
                    checkInDao.updateStatus(checkIn.id, "MISSED", now, "SYNCED")
                    return@withContext updated.copy(status = "MISSED", syncStatus = "SYNCED")
                }
            } catch (e: Exception) {
                Log.w(TAG, "Network offline. Confirmation buffered locally: ${e.message}")
            }
        }

        updated
    }

    /**
     * Flushes offline pending check-in actions to backend when connectivity is restored.
     */
    suspend fun syncPendingCheckIns(): Int = withContext(Dispatchers.IO) {
        val token = authTokenProvider() ?: return@withContext 0
        val pending = checkInDao.getPendingSyncCheckIns()
        var syncedCount = 0

        for (item in pending) {
            try {
                if (item.status == "CONFIRMED_SAFE" && item.serverCheckinId != null) {
                    val req = CheckInConfirmRequest(
                        respondedAt = item.respondedAt?.let { isoFormat.format(Date(it)) },
                        responseType = item.responseType ?: "MANUAL_TAP",
                        clientActionId = item.clientActionId
                    )
                    val resp = checkInApi.confirmCheckIn(item.serverCheckinId, req, "Bearer $token")
                    if (resp.isSuccessful) {
                        checkInDao.updateStatus(item.id, "CONFIRMED_SAFE", item.respondedAt, "SYNCED")
                        syncedCount++
                    } else if (resp.code() == 409) {
                        checkInDao.updateStatus(item.id, "MISSED", item.respondedAt, "SYNCED")
                    }
                }
            } catch (e: Exception) {
                Log.w(TAG, "Sync failed for item ${item.id}: ${e.message}")
            }
        }
        syncedCount
    }

    /**
     * Fetches current journey delay status from backend.
     */
    suspend fun fetchJourneyDelayStatus(journeyId: Long): DelayStatusDto? = withContext(Dispatchers.IO) {
        val token = authTokenProvider() ?: return@withContext null
        try {
            val resp = checkInApi.getDelayStatus(journeyId, "Bearer $token")
            if (resp.isSuccessful && resp.body()?.data != null) {
                return@withContext resp.body()!!.data
            }
        } catch (e: Exception) {
            Log.w(TAG, "Unable to query journey delay status: ${e.message}")
        }
        null
    }
}
