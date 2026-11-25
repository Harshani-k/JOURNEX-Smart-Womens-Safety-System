package com.journex.safety.data.remote.model

import com.google.gson.annotations.SerializedName

data class EmergencyAlertDispatchDto(
    @SerializedName("id") val id: Long,
    @SerializedName("emergency_event_id") val emergencyEventId: Long,
    @SerializedName("contact_id") val contactId: Long? = null,
    @SerializedName("contact_name") val contactName: String,
    @SerializedName("contact_phone") val contactPhone: String,
    @SerializedName("escalation_level") val escalationLevel: Int = 1,
    @SerializedName("channel") val channel: String = "SMS",
    @SerializedName("status") val status: String, // "PENDING", "SENT", "DELIVERED", "FAILED"
    @SerializedName("provider_message_id") val providerMessageId: String? = null,
    @SerializedName("retry_count") val retryCount: Int = 0,
    @SerializedName("max_retries") val maxRetries: Int = 3,
    @SerializedName("error_message") val errorMessage: String? = null,
    @SerializedName("sent_at") val sentAt: String? = null,
    @SerializedName("delivered_at") val deliveredAt: String? = null,
    @SerializedName("acknowledged_at") val acknowledgedAt: String? = null,
    @SerializedName("created_at") val createdAt: String? = null
)

data class EmergencyEventDto(
    @SerializedName("id") val id: Long,
    @SerializedName("journey_id") val journeyId: Long? = null,
    @SerializedName("user_id") val userId: Long,
    @SerializedName("trigger_type") val triggerType: String,
    @SerializedName("status") val status: String,
    @SerializedName("trigger_timestamp") val triggerTimestamp: String,
    @SerializedName("cancellation_timestamp") val cancellationTimestamp: String? = null,
    @SerializedName("cancellation_reason") val cancellationReason: String? = null,
    @SerializedName("latitude") val latitude: Double? = null,
    @SerializedName("longitude") val longitude: Double? = null,
    @SerializedName("accuracy") val accuracy: Float? = null,
    @SerializedName("location_address") val locationAddress: String? = null,
    @SerializedName("current_escalation_level") val currentEscalationLevel: Int = 1,
    @SerializedName("max_escalation_level") val maxEscalationLevel: Int = 3,
    @SerializedName("client_action_id") val clientActionId: String? = null,
    @SerializedName("dispatches") val dispatches: List<EmergencyAlertDispatchDto> = emptyList(),
    @SerializedName("created_at") val createdAt: String? = null
)

data class EmergencyEventCreateRequest(
    @SerializedName("trigger_type") val triggerType: String = "MANUAL_SOS",
    @SerializedName("journey_id") val journeyId: Long? = null,
    @SerializedName("latitude") val latitude: Double? = null,
    @SerializedName("longitude") val longitude: Double? = null,
    @SerializedName("accuracy") val accuracy: Float? = null,
    @SerializedName("location_address") val locationAddress: String? = null,
    @SerializedName("client_action_id") val clientActionId: String? = null
)

data class EmergencyEventCancelRequest(
    @SerializedName("cancellation_reason") val cancellationReason: String = "Cancelled by user"
)

data class EmergencyEventEscalateRequest(
    @SerializedName("target_level") val targetLevel: Int? = null
)

data class EmergencyDeliveryStatusSummary(
    @SerializedName("emergency_event_id") val emergencyEventId: Long,
    @SerializedName("status") val status: String,
    @SerializedName("current_escalation_level") val currentEscalationLevel: Int,
    @SerializedName("total_dispatches") val totalDispatches: Int,
    @SerializedName("dispatches") val dispatches: List<EmergencyAlertDispatchDto> = emptyList()
)

data class EmergencyHistoryData(
    @SerializedName("events") val events: List<EmergencyEventDto> = emptyList(),
    @SerializedName("page") val page: Int = 1,
    @SerializedName("per_page") val perPage: Int = 10,
    @SerializedName("total") val total: Int = 0
)
