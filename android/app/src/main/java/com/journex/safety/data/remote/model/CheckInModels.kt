package com.journex.safety.data.remote.model

import com.google.gson.annotations.SerializedName

data class CheckInDto(
    @SerializedName("id") val id: Long,
    @SerializedName("journey_id") val journeyId: Long,
    @SerializedName("user_id") val userId: Long,
    @SerializedName("scheduled_at") val scheduledAt: String?,
    @SerializedName("deadline_at") val deadlineAt: String?,
    @SerializedName("responded_at") val respondedAt: String?,
    @SerializedName("status") val status: String,
    @SerializedName("response_type") val responseType: String?,
    @SerializedName("client_action_id") val clientActionId: String?,
    @SerializedName("created_at") val createdAt: String?,
    @SerializedName("updated_at") val updatedAt: String?
)

data class CheckInCreateRequest(
    @SerializedName("scheduled_at") val scheduledAt: String? = null,
    @SerializedName("deadline_at") val deadlineAt: String? = null,
    @SerializedName("client_action_id") val clientActionId: String? = null
)

data class CheckInConfirmRequest(
    @SerializedName("responded_at") val respondedAt: String? = null,
    @SerializedName("response_type") val responseType: String? = "MANUAL_TAP",
    @SerializedName("client_action_id") val clientActionId: String? = null
)

data class CheckInListResponseData(
    @SerializedName("checkins") val checkins: List<CheckInDto>
)

data class DelayStatusDto(
    @SerializedName("journey_id") val journeyId: Long,
    @SerializedName("status") val status: String,
    @SerializedName("is_delayed") val isDelayed: Boolean,
    @SerializedName("delayed_at") val delayedAt: String?,
    @SerializedName("expected_arrival_time") val expectedArrivalTime: String?,
    @SerializedName("minutes_delayed") val minutesDelayed: Int
)
