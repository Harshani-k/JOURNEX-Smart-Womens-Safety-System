package com.journex.safety.data.local.dao

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.journex.safety.data.local.entity.CheckInRecordEntity
import com.journex.safety.data.local.entity.ContactEntity
import com.journex.safety.data.local.entity.IncidentJournalEntity
import com.journex.safety.data.local.entity.JourneyLocationEntity
import com.journex.safety.data.local.entity.JourneyRecordEntity
import com.journex.safety.data.local.entity.SafetyProfileEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface SafetyProfileDao {
    @Query("SELECT * FROM safety_profile WHERE id = 1 LIMIT 1")
    fun getProfileFlow(): Flow<SafetyProfileEntity?>

    @Query("SELECT * FROM safety_profile WHERE id = 1 LIMIT 1")
    suspend fun getProfile(): SafetyProfileEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertOrUpdate(profile: SafetyProfileEntity)
}

@Dao
interface ContactDao {
    @Query("SELECT * FROM trusted_contacts ORDER BY isPrimary DESC, name ASC")
    fun getAllContactsFlow(): Flow<List<ContactEntity>>

    @Query("SELECT COUNT(*) FROM trusted_contacts")
    fun getContactsCountFlow(): Flow<Int>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(contact: ContactEntity): Long

    @Delete
    suspend fun delete(contact: ContactEntity)

    @Query("DELETE FROM trusted_contacts WHERE id = :id")
    suspend fun deleteById(id: Long)
}

@Dao
interface JourneyRecordDao {
    @Query("SELECT * FROM journey_records ORDER BY timestamp DESC")
    fun getAllJourneysFlow(): Flow<List<JourneyRecordEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(journey: JourneyRecordEntity): Long

    @Query("DELETE FROM journey_records")
    suspend fun clearAll()
}

@Dao
interface CheckInRecordDao {
    @Query("SELECT * FROM checkin_records WHERE journeyId = :journeyId ORDER BY scheduledAt DESC")
    fun getCheckInsForJourney(journeyId: Long): Flow<List<CheckInRecordEntity>>

    @Query("SELECT * FROM checkin_records WHERE journeyId = :journeyId ORDER BY scheduledAt DESC LIMIT 1")
    fun getLatestCheckInFlow(journeyId: Long): Flow<CheckInRecordEntity?>

    @Query("SELECT * FROM checkin_records WHERE journeyId = :journeyId ORDER BY scheduledAt DESC LIMIT 1")
    suspend fun getLatestCheckIn(journeyId: Long): CheckInRecordEntity?

    @Query("SELECT * FROM checkin_records WHERE syncStatus = 'PENDING' ORDER BY timestamp ASC")
    suspend fun getPendingSyncCheckIns(): List<CheckInRecordEntity>

    @Query("SELECT COUNT(*) FROM checkin_records WHERE journeyId = :journeyId AND syncStatus = 'PENDING'")
    fun getUnsyncedCheckInCountFlow(journeyId: Long): Flow<Int>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(checkIn: CheckInRecordEntity): Long

    @Query("UPDATE checkin_records SET status = :status, respondedAt = :respondedAt, syncStatus = :syncStatus WHERE id = :id")
    suspend fun updateStatus(id: Long, status: String, respondedAt: Long?, syncStatus: String)

    @Query("UPDATE checkin_records SET syncStatus = 'SYNCED', serverCheckinId = :serverId WHERE id = :id")
    suspend fun markSynced(id: Long, serverId: Long)
}

@Dao
interface IncidentJournalDao {
    @Query("SELECT * FROM incident_journal ORDER BY timestamp DESC")
    fun getAllIncidentsFlow(): Flow<List<IncidentJournalEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(incident: IncidentJournalEntity): Long

    @Delete
    suspend fun delete(incident: IncidentJournalEntity)

    @Query("DELETE FROM incident_journal")
    suspend fun clearAll()
}

@Dao
interface JourneyLocationDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertLocation(location: JourneyLocationEntity): Long

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertLocations(locations: List<JourneyLocationEntity>)

    @Query("SELECT * FROM journey_locations WHERE journeyId = :journeyId ORDER BY recordedAt ASC")
    fun getLocationsForJourney(journeyId: Long): Flow<List<JourneyLocationEntity>>

    @Query("SELECT * FROM journey_locations WHERE journeyId = :journeyId AND syncStatus = 'PENDING' ORDER BY recordedAt ASC LIMIT :limit")
    suspend fun getUnsyncedLocations(journeyId: Long, limit: Int = 50): List<JourneyLocationEntity>

    @Query("UPDATE journey_locations SET syncStatus = 'SYNCED' WHERE id IN (:ids)")
    suspend fun markAsSynced(ids: List<Long>)

    @Query("DELETE FROM journey_locations WHERE syncStatus = 'SYNCED' AND recordedAt < :cutoffTime")
    suspend fun deleteSyncedLocationsBefore(cutoffTime: Long)

    @Query("SELECT COUNT(*) FROM journey_locations WHERE journeyId = :journeyId AND syncStatus = 'PENDING'")
    fun getUnsyncedCountFlow(journeyId: Long): Flow<Int>
}

@Dao
interface SafetyEventDao {
    @Query("SELECT * FROM safety_events WHERE journeyId = :journeyId AND status = 'ACTIVE' ORDER BY detectedAt DESC")
    fun getActiveEventsFlow(journeyId: Long): Flow<List<com.journex.safety.data.local.entity.SafetyEventEntity>>

    @Query("SELECT * FROM safety_events WHERE journeyId = :journeyId ORDER BY detectedAt DESC")
    fun getAllEventsFlow(journeyId: Long): Flow<List<com.journex.safety.data.local.entity.SafetyEventEntity>>

    @Query("SELECT * FROM safety_events WHERE journeyId = :journeyId AND status = 'ACTIVE' LIMIT 1")
    suspend fun getActiveEvent(journeyId: Long): com.journex.safety.data.local.entity.SafetyEventEntity?

    @Query("SELECT * FROM safety_events WHERE syncStatus = 'PENDING'")
    suspend fun getPendingSyncEvents(): List<com.journex.safety.data.local.entity.SafetyEventEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(event: com.journex.safety.data.local.entity.SafetyEventEntity): Long

    @Update
    suspend fun update(event: com.journex.safety.data.local.entity.SafetyEventEntity)

    @Query("UPDATE safety_events SET status = 'ACKNOWLEDGED', acknowledgedAt = :timestamp, syncStatus = :syncStatus WHERE id = :id")
    suspend fun markAcknowledged(id: Long, timestamp: Long, syncStatus: String)

    @Query("UPDATE safety_events SET status = 'RESOLVED', resolvedAt = :timestamp, resolutionNotes = :notes, syncStatus = :syncStatus WHERE id = :id")
    suspend fun markResolved(id: Long, timestamp: Long, notes: String?, syncStatus: String)

    @Query("UPDATE safety_events SET syncStatus = 'SYNCED', serverEventId = :serverEventId WHERE id = :id")
    suspend fun markSynced(id: Long, serverEventId: Long)
}

@Dao
interface RiskAnalysisDao {
    @Query("SELECT * FROM risk_analyses WHERE journeyId = :journeyId ORDER BY analyzedAt DESC LIMIT 1")
    fun getLatestRiskAnalysisFlow(journeyId: Long): Flow<com.journex.safety.data.local.entity.RiskAnalysisEntity?>

    @Query("SELECT * FROM risk_analyses WHERE journeyId = :journeyId ORDER BY analyzedAt DESC LIMIT 1")
    suspend fun getLatestRiskAnalysis(journeyId: Long): com.journex.safety.data.local.entity.RiskAnalysisEntity?

    @Query("SELECT * FROM risk_analyses WHERE journeyId = :journeyId ORDER BY analyzedAt DESC")
    fun getAllRiskAnalysesFlow(journeyId: Long): Flow<List<com.journex.safety.data.local.entity.RiskAnalysisEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(analysis: com.journex.safety.data.local.entity.RiskAnalysisEntity): Long

    @Query("DELETE FROM risk_analyses WHERE journeyId = :journeyId")
    suspend fun clearForJourney(journeyId: Long)
}

@Dao
interface EmergencyEventDao {
    @Query("SELECT * FROM emergency_events WHERE status = 'ACTIVE' ORDER BY triggerTimestamp DESC LIMIT 1")
    fun getActiveEmergencyFlow(): Flow<com.journex.safety.data.local.entity.EmergencyEventEntity?>

    @Query("SELECT * FROM emergency_events WHERE status = 'ACTIVE' ORDER BY triggerTimestamp DESC LIMIT 1")
    suspend fun getActiveEmergency(): com.journex.safety.data.local.entity.EmergencyEventEntity?

    @Query("SELECT * FROM emergency_events WHERE journeyId = :journeyId ORDER BY triggerTimestamp DESC LIMIT 1")
    fun getLatestForJourneyFlow(journeyId: Long): Flow<com.journex.safety.data.local.entity.EmergencyEventEntity?>

    @Query("SELECT * FROM emergency_events ORDER BY triggerTimestamp DESC")
    fun getAllEventsFlow(): Flow<List<com.journex.safety.data.local.entity.EmergencyEventEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(event: com.journex.safety.data.local.entity.EmergencyEventEntity): Long

    @Update
    suspend fun update(event: com.journex.safety.data.local.entity.EmergencyEventEntity)

    @Query("UPDATE emergency_events SET status = 'CANCELLED', cancellationTimestamp = :timestamp, cancellationReason = :reason, syncStatus = :syncStatus WHERE id = :id")
    suspend fun markCancelled(id: Long, timestamp: Long, reason: String, syncStatus: String)

    @Query("UPDATE emergency_events SET currentEscalationLevel = :level, syncStatus = :syncStatus WHERE id = :id")
    suspend fun markEscalated(id: Long, level: Int, syncStatus: String)

    @Query("UPDATE emergency_events SET syncStatus = 'SYNCED', serverEventId = :serverId WHERE id = :id")
    suspend fun markSynced(id: Long, serverId: Long)
}

@Dao
interface EmergencyAlertDispatchDao {
    @Query("SELECT * FROM emergency_alert_dispatches WHERE emergencyEventId = :eventId ORDER BY escalationLevel ASC")
    fun getDispatchesForEventFlow(eventId: Long): Flow<List<com.journex.safety.data.local.entity.EmergencyAlertDispatchEntity>>

    @Query("SELECT * FROM emergency_alert_dispatches WHERE emergencyEventId = :eventId ORDER BY escalationLevel ASC")
    suspend fun getDispatchesForEvent(eventId: Long): List<com.journex.safety.data.local.entity.EmergencyAlertDispatchEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(dispatches: List<com.journex.safety.data.local.entity.EmergencyAlertDispatchEntity>)

    @Query("DELETE FROM emergency_alert_dispatches WHERE emergencyEventId = :eventId")
    suspend fun clearForEvent(eventId: Long)
}
