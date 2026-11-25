package com.journex.safety.data.repository

import com.journex.safety.data.local.JournexDatabase
import com.journex.safety.data.local.entity.EmergencyAlertDispatchEntity
import com.journex.safety.data.local.entity.EmergencyEventEntity
import com.journex.safety.data.remote.RetrofitClient
import com.journex.safety.data.remote.model.EmergencyDeliveryStatusSummary
import com.journex.safety.data.remote.model.EmergencyEventCancelRequest
import com.journex.safety.data.remote.model.EmergencyEventCreateRequest
import com.journex.safety.data.remote.model.EmergencyEventDto
import com.journex.safety.data.remote.model.EmergencyEventEscalateRequest
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.withContext
import java.util.UUID

class EmergencyRepository(
    private val database: JournexDatabase
) {
    private val emergencyDao = database.emergencyEventDao()
    private val dispatchDao = database.emergencyAlertDispatchDao()
    private val emergencyApi = RetrofitClient.emergencyApi

    fun getActiveEmergencyFlow(): Flow<EmergencyEventEntity?> {
        return emergencyDao.getActiveEmergencyFlow()
    }

    suspend fun getActiveEmergency(): EmergencyEventEntity? = withContext(Dispatchers.IO) {
        emergencyDao.getActiveEmergency()
    }

    fun getDispatchesForEventFlow(eventId: Long): Flow<List<EmergencyAlertDispatchEntity>> {
        return dispatchDao.getDispatchesForEventFlow(eventId)
    }

    suspend fun triggerEmergencySos(
        journeyId: Long? = null,
        triggerType: String = "MANUAL_SOS",
        latitude: Double? = null,
        longitude: Double? = null,
        accuracy: Float? = null,
        locationAddress: String? = null
    ): Result<EmergencyEventEntity> = withContext(Dispatchers.IO) {
        val clientActionId = UUID.randomUUID().toString()
        val now = System.currentTimeMillis()

        // 1. Optimistic Local Room Insert
        val localEntity = EmergencyEventEntity(
            journeyId = journeyId,
            triggerType = triggerType,
            status = "ACTIVE",
            triggerTimestamp = now,
            latitude = latitude,
            longitude = longitude,
            accuracy = accuracy,
            locationAddress = locationAddress,
            currentEscalationLevel = 1,
            maxEscalationLevel = 3,
            clientActionId = clientActionId,
            syncStatus = "PENDING"
        )
        val localId = emergencyDao.insert(localEntity)
        val savedEntity = localEntity.copy(id = localId)

        // 2. Network Dispatch
        try {
            val req = EmergencyEventCreateRequest(
                triggerType = triggerType,
                journeyId = journeyId,
                latitude = latitude,
                longitude = longitude,
                accuracy = accuracy,
                locationAddress = locationAddress,
                clientActionId = clientActionId
            )
            val response = if (journeyId != null) {
                emergencyApi.triggerJourneyEmergency(journeyId, req)
            } else {
                emergencyApi.triggerEmergency(req)
            }

            if (response.isSuccessful && response.body()?.data != null) {
                val dto = response.body()!!.data!!
                emergencyDao.markSynced(localId, dto.id)

                // Sync dispatches into Room
                val dispatchEntities = dto.dispatches.map { d ->
                    EmergencyAlertDispatchEntity(
                        serverDispatchId = d.id,
                        emergencyEventId = localId,
                        contactName = d.contactName,
                        contactPhone = d.contactPhone,
                        escalationLevel = d.escalationLevel,
                        channel = d.channel,
                        status = d.status,
                        providerMessageId = d.providerMessageId,
                        errorMessage = d.errorMessage,
                        syncStatus = "SYNCED"
                    )
                }
                dispatchDao.clearForEvent(localId)
                dispatchDao.insertAll(dispatchEntities)

                Result.success(savedEntity.copy(serverEventId = dto.id, syncStatus = "SYNCED"))
            } else {
                Result.success(savedEntity)
            }
        } catch (e: Exception) {
            // Offline fallback: keep local PENDING record
            Result.success(savedEntity)
        }
    }

    suspend fun cancelEmergency(
        eventId: Long,
        serverEventId: Long?,
        cancellationReason: String = "Cancelled by traveler"
    ): Result<Unit> = withContext(Dispatchers.IO) {
        val now = System.currentTimeMillis()

        // 1. Optimistic Local Cancellation
        emergencyDao.markCancelled(eventId, now, cancellationReason, "PENDING")

        // 2. Network Sync
        val remoteId = serverEventId ?: eventId
        try {
            val response = emergencyApi.cancelEmergency(
                remoteId,
                EmergencyEventCancelRequest(cancellationReason = cancellationReason)
            )
            if (response.isSuccessful) {
                emergencyDao.markCancelled(eventId, now, cancellationReason, "SYNCED")
            }
            Result.success(Unit)
        } catch (e: Exception) {
            Result.success(Unit)
        }
    }

    suspend fun escalateEmergency(
        eventId: Long,
        serverEventId: Long?
    ): Result<Int> = withContext(Dispatchers.IO) {
        val remoteId = serverEventId ?: eventId
        try {
            val response = emergencyApi.escalateEmergency(remoteId, EmergencyEventEscalateRequest())
            if (response.isSuccessful && response.body()?.data != null) {
                val dto = response.body()!!.data!!
                emergencyDao.markEscalated(eventId, dto.currentEscalationLevel, "SYNCED")

                // Update dispatches
                val dispatchEntities = dto.dispatches.map { d ->
                    EmergencyAlertDispatchEntity(
                        serverDispatchId = d.id,
                        emergencyEventId = eventId,
                        contactName = d.contactName,
                        contactPhone = d.contactPhone,
                        escalationLevel = d.escalationLevel,
                        channel = d.channel,
                        status = d.status,
                        providerMessageId = d.providerMessageId,
                        errorMessage = d.errorMessage,
                        syncStatus = "SYNCED"
                    )
                }
                dispatchDao.clearForEvent(eventId)
                dispatchDao.insertAll(dispatchEntities)

                Result.success(dto.currentEscalationLevel)
            } else {
                Result.failure(Exception("Failed to escalate: HTTP ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun fetchDeliveryStatus(
        eventId: Long,
        serverEventId: Long?
    ): Result<EmergencyDeliveryStatusSummary> = withContext(Dispatchers.IO) {
        val remoteId = serverEventId ?: eventId
        try {
            val response = emergencyApi.getDeliveryStatus(remoteId)
            if (response.isSuccessful && response.body()?.data != null) {
                Result.success(response.body()!!.data!!)
            } else {
                Result.failure(Exception("HTTP ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
