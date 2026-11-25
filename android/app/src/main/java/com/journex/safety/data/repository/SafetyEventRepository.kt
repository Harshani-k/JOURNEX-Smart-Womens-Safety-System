package com.journex.safety.data.repository

import android.util.Log
import com.journex.safety.data.local.JournexDatabase
import com.journex.safety.data.local.entity.SafetyEventEntity
import com.journex.safety.data.remote.RetrofitClient
import com.journex.safety.data.remote.model.SafetyEventActionRequest
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.withContext
import java.util.UUID

class SafetyEventRepository(
    private val database: JournexDatabase,
    private val authTokenProvider: () -> String? = { null }
) {
    private val safetyEventDao = database.safetyEventDao()
    private val safetyEventApi = RetrofitClient.safetyEventApi

    companion object {
        private const val TAG = "SafetyEventRepo"
    }

    fun getActiveEventsFlow(journeyId: Long): Flow<List<SafetyEventEntity>> {
        return safetyEventDao.getActiveEventsFlow(journeyId)
    }

    fun getAllEventsFlow(journeyId: Long): Flow<List<SafetyEventEntity>> {
        return safetyEventDao.getAllEventsFlow(journeyId)
    }

    suspend fun recordLocalEvent(event: SafetyEventEntity): Long = withContext(Dispatchers.IO) {
        safetyEventDao.insert(event)
    }

    suspend fun acknowledgeEvent(journeyId: Long, localEventId: Long): SafetyEventEntity? = withContext(Dispatchers.IO) {
        val now = System.currentTimeMillis()
        safetyEventDao.markAcknowledged(localEventId, now, "PENDING")

        val token = authTokenProvider()
        val event = safetyEventDao.getActiveEvent(journeyId)
        if (token != null && event?.serverEventId != null) {
            try {
                val resp = safetyEventApi.acknowledgeSafetyEvent(journeyId, event.serverEventId, "Bearer $token")
                if (resp.isSuccessful) {
                    safetyEventDao.markAcknowledged(localEventId, now, "SYNCED")
                    Log.i(TAG, "Synced ACKNOWLEDGED for event $localEventId")
                }
            } catch (e: Exception) {
                Log.w(TAG, "Offline. Event acknowledgment buffered locally: ${e.message}")
            }
        }
        event?.copy(status = "ACKNOWLEDGED", acknowledgedAt = now, syncStatus = "PENDING")
    }

    suspend fun resolveEvent(
        journeyId: Long,
        localEventId: Long,
        notes: String? = "Marked safe / expected by traveler"
    ): SafetyEventEntity? = withContext(Dispatchers.IO) {
        val now = System.currentTimeMillis()
        safetyEventDao.markResolved(localEventId, now, notes, "PENDING")

        val token = authTokenProvider()
        val event = safetyEventDao.getActiveEvent(journeyId)
        if (token != null && event?.serverEventId != null) {
            try {
                val req = SafetyEventActionRequest(
                    resolutionNotes = notes,
                    clientActionId = event.clientActionId
                )
                val resp = safetyEventApi.resolveSafetyEvent(journeyId, event.serverEventId, req, "Bearer $token")
                if (resp.isSuccessful) {
                    safetyEventDao.markResolved(localEventId, now, notes, "SYNCED")
                    Log.i(TAG, "Synced RESOLVED for event $localEventId")
                }
            } catch (e: Exception) {
                Log.w(TAG, "Offline. Event resolution buffered locally: ${e.message}")
            }
        }
        event?.copy(status = "RESOLVED", resolvedAt = now, resolutionNotes = notes, syncStatus = "PENDING")
    }

    suspend fun syncPendingEvents(): Int = withContext(Dispatchers.IO) {
        val token = authTokenProvider() ?: return@withContext 0
        val pending = safetyEventDao.getPendingSyncEvents()
        var syncedCount = 0

        for (item in pending) {
            try {
                if (item.serverEventId != null) {
                    when (item.status) {
                        "ACKNOWLEDGED" -> {
                            val resp = safetyEventApi.acknowledgeSafetyEvent(item.journeyId, item.serverEventId, "Bearer $token")
                            if (resp.isSuccessful) {
                                safetyEventDao.markAcknowledged(item.id, item.acknowledgedAt ?: System.currentTimeMillis(), "SYNCED")
                                syncedCount++
                            }
                        }
                        "RESOLVED" -> {
                            val req = SafetyEventActionRequest(
                                resolutionNotes = item.resolutionNotes,
                                clientActionId = item.clientActionId
                            )
                            val resp = safetyEventApi.resolveSafetyEvent(item.journeyId, item.serverEventId, req, "Bearer $token")
                            if (resp.isSuccessful) {
                                safetyEventDao.markResolved(item.id, item.resolvedAt ?: System.currentTimeMillis(), item.resolutionNotes, "SYNCED")
                                syncedCount++
                            }
                        }
                    }
                }
            } catch (e: Exception) {
                Log.w(TAG, "Failed syncing event ${item.id}: ${e.message}")
            }
        }
        syncedCount
    }

    suspend fun fetchRemoteActiveEvents(journeyId: Long): List<SafetyEventEntity> = withContext(Dispatchers.IO) {
        val token = authTokenProvider() ?: return@withContext emptyList()
        try {
            val resp = safetyEventApi.getActiveSafetyEvents(journeyId, "Bearer $token")
            val body = resp.body()
            if (resp.isSuccessful && body?.data?.activeEvents != null) {
                val dtos = body.data!!.activeEvents
                val resultList = mutableListOf<SafetyEventEntity>()
                for (dto in dtos) {
                    val entity = SafetyEventEntity(
                        serverEventId = dto.id,
                        journeyId = dto.journeyId,
                        eventType = dto.eventType,
                        status = dto.status,
                        triggerReason = dto.triggerReason,
                        severity = dto.severity,
                        latitude = dto.latitude,
                        longitude = dto.longitude,
                        deviationDistance = dto.deviationDistance,
                        durationSeconds = dto.durationSeconds,
                        clientActionId = dto.clientActionId ?: UUID.randomUUID().toString(),
                        syncStatus = "SYNCED"
                    )
                    val localId = safetyEventDao.insert(entity)
                    resultList.add(entity.copy(id = localId))
                }
                return@withContext resultList
            }
        } catch (e: Exception) {
            Log.w(TAG, "Unable to query remote active safety events: ${e.message}")
        }
        emptyList()
    }
}
