package com.journex.safety.data.local.entity

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(tableName = "safety_profile")
data class SafetyProfileEntity(
    @PrimaryKey
    val id: Int = 1,
    val fullName: String,
    val bloodGroup: String,
    val allergies: String,
    val homeAddress: String,
    val emergencyNotes: String
)

@Entity(tableName = "trusted_contacts")
data class ContactEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val name: String,
    val relationship: String,
    val phone: String,
    val isPrimary: Boolean = false
)

@Entity(tableName = "journey_records")
data class JourneyRecordEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val destination: String,
    val timestamp: Long = System.currentTimeMillis(),
    val durationMinutes: Int,
    val distanceKm: String,
    val safetyStatus: String
)

@Entity(
    tableName = "checkin_records",
    indices = [
        Index("journeyId"),
        Index("status"),
        Index("syncStatus")
    ]
)
data class CheckInRecordEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val journeyId: Long,
    val timestamp: Long = System.currentTimeMillis(),
    val status: String, // "CONFIRMED_SAFE", "SCHEDULED", "REMINDED", "MISSED", "CANCELLED"
    val responseTimeSeconds: Int = 0,
    val serverCheckinId: Long? = null,
    val scheduledAt: Long = System.currentTimeMillis(),
    val deadlineAt: Long = System.currentTimeMillis() + 180_000L,
    val respondedAt: Long? = null,
    val responseType: String? = "MANUAL_TAP",
    val clientActionId: String? = java.util.UUID.randomUUID().toString(),
    val syncStatus: String = "PENDING" // "PENDING", "SYNCED", "FAILED"
)

@Entity(tableName = "incident_journal")
data class IncidentJournalEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val title: String,
    val timestamp: Long = System.currentTimeMillis(),
    val category: String,
    val encryptedNotes: String, // AES-GCM Encrypted Base64
    val ivBase64: String         // Initialization Vector
)

@Entity(tableName = "journey_locations")
data class JourneyLocationEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val journeyId: Long,
    val latitude: Double,
    val longitude: Double,
    val accuracy: Float,
    val altitude: Double? = null,
    val speed: Float? = null,
    val bearing: Float? = null,
    val recordedAt: Long = System.currentTimeMillis(),
    val syncStatus: String = "PENDING" // "PENDING", "SYNCED", "FAILED"
)

@Entity(
    tableName = "safety_events",
    indices = [
        Index("journeyId"),
        Index("status"),
        Index("syncStatus")
    ]
)
data class SafetyEventEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val serverEventId: Long? = null,
    val journeyId: Long,
    val eventType: String, // "ROUTE_DEVIATION", "UNEXPECTED_STOP"
    val status: String,    // "ACTIVE", "ACKNOWLEDGED", "RESOLVED"
    val triggerReason: String,
    val severity: String = "MEDIUM",
    val latitude: Double? = null,
    val longitude: Double? = null,
    val deviationDistance: Double? = null,
    val durationSeconds: Int? = null,
    val detectedAt: Long = System.currentTimeMillis(),
    val acknowledgedAt: Long? = null,
    val resolvedAt: Long? = null,
    val resolutionNotes: String? = null,
    val clientActionId: String? = java.util.UUID.randomUUID().toString(),
    val syncStatus: String = "PENDING" // "PENDING", "SYNCED"
)

@Entity(
    tableName = "risk_analyses",
    indices = [
        Index("journeyId"),
        Index("analyzedAt")
    ]
)
data class RiskAnalysisEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val serverAnalysisId: Long? = null,
    val journeyId: Long,
    val riskScore: Float, // 0.0 to 1.0
    val riskCategory: String, // "LOW", "MODERATE", "HIGH", "CRITICAL"
    val contributingFactorsJson: String, // JSON array string
    val modelVersion: String = "1.0.0-rf",
    val isInsufficientData: Boolean = false,
    val analyzedAt: Long = System.currentTimeMillis(),
    val createdAt: Long = System.currentTimeMillis()
)

@Entity(
    tableName = "emergency_events",
    indices = [
        Index("journeyId"),
        Index("status"),
        Index("triggerTimestamp")
    ]
)
data class EmergencyEventEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val serverEventId: Long? = null,
    val journeyId: Long? = null,
    val triggerType: String = "MANUAL_SOS", // "MANUAL_SOS", "MISSED_CHECKIN_ESCALATION", "SILENT_ALERT"
    val status: String = "ACTIVE",          // "ACTIVE", "CANCELLED", "ESCALATED", "RESOLVED"
    val triggerTimestamp: Long = System.currentTimeMillis(),
    val cancellationTimestamp: Long? = null,
    val cancellationReason: String? = null,
    val latitude: Double? = null,
    val longitude: Double? = null,
    val accuracy: Float? = null,
    val locationAddress: String? = null,
    val currentEscalationLevel: Int = 1,
    val maxEscalationLevel: Int = 3,
    val clientActionId: String = java.util.UUID.randomUUID().toString(),
    val syncStatus: String = "PENDING",    // "PENDING", "SYNCED"
    val createdAt: Long = System.currentTimeMillis(),
    val updatedAt: Long = System.currentTimeMillis()
)

@Entity(
    tableName = "emergency_alert_dispatches",
    indices = [
        Index(value = ["emergencyEventId"], name = "index_dispatches_eventId"),
        Index(value = ["status"], name = "index_dispatches_status")
    ]
)
data class EmergencyAlertDispatchEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val serverDispatchId: Long? = null,
    val emergencyEventId: Long,
    val contactName: String,
    val contactPhone: String,
    val escalationLevel: Int = 1,
    val channel: String = "SMS",
    val status: String = "PENDING",        // "PENDING", "SENT", "DELIVERED", "FAILED"
    val providerMessageId: String? = null,
    val errorMessage: String? = null,
    val sentAt: Long? = null,
    val deliveredAt: Long? = null,
    val syncStatus: String = "PENDING"
)
