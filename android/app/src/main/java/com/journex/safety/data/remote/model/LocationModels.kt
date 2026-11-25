package com.journex.safety.data.remote.model

import com.google.gson.annotations.SerializedName

data class LocationUploadItemDto(
    @SerializedName("latitude") val latitude: Double,
    @SerializedName("longitude") val longitude: Double,
    @SerializedName("accuracy") val accuracy: Float,
    @SerializedName("altitude") val altitude: Double? = null,
    @SerializedName("speed") val speed: Float? = null,
    @SerializedName("bearing") val bearing: Float? = null,
    @SerializedName("recorded_at") val recordedAt: String
)

data class LocationBatchUploadRequest(
    @SerializedName("locations") val locations: List<LocationUploadItemDto>
)

data class LocationUploadResponseData(
    @SerializedName("accepted_count") val acceptedCount: Int,
    @SerializedName("rejected_count") val rejectedCount: Int,
    @SerializedName("total_received") val totalReceived: Int
)

data class LocationApiResponse<T>(
    @SerializedName("success") val success: Boolean,
    @SerializedName("message") val message: String,
    @SerializedName("data") val data: T?,
    @SerializedName("errors") val errors: Any?,
    @SerializedName("timestamp") val timestamp: String
)
