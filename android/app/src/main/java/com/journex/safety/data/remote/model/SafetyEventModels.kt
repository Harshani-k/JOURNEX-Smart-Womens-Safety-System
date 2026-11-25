package com.journex.safety.data.remote.model

import com.google.gson.annotations.SerializedName

data class SafetyEventDto(
    @SerializedName("id") val id: Long,
    @SerializedName("journey_id") val journeyId: Long,
    @SerializedName("user_id") val userId: Long,
    @SerializedName("event_type") val eventType: String,
    @SerializedName("status") val status: String,
    @SerializedName("trigger_reason") val triggerReason: String,
    @SerializedName("severity") val severity: String,
    @SerializedName("latitude") val latitude: Double?,
    @SerializedName("longitude") val longitude: Double?,
    @SerializedName("accuracy") val accuracy: Float?,
    @SerializedName("deviation_distance") val deviationDistance: Double?,
    @SerializedName("duration_seconds") val durationSeconds: Int?,
    @SerializedName("consecutive_count") val consecutiveCount: Int?,
    @SerializedName("detected_at") val detectedAt: String?,
    @SerializedName("acknowledged_at") val acknowledgedAt: String?,
    @SerializedName("resolved_at") val resolvedAt: String?,
    @SerializedName("resolution_notes") val resolutionNotes: String?,
    @SerializedName("client_action_id") val clientActionId: String?,
    @SerializedName("created_at") val createdAt: String?,
    @SerializedName("updated_at") val updatedAt: String?
)

data class SafetyEventActionRequest(
    @SerializedName("resolution_notes") val resolutionNotes: String? = null,
    @SerializedName("client_action_id") val clientActionId: String? = null
)

data class SafetyEventListResponseData(
    @SerializedName("safety_events") val safetyEvents: List<SafetyEventDto>
)

data class ActiveSafetyEventsResponseData(
    @SerializedName("active_events") val activeEvents: List<SafetyEventDto>
)
