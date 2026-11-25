package com.journex.safety.data.remote.api

import com.journex.safety.data.remote.model.EmergencyDeliveryStatusSummary
import com.journex.safety.data.remote.model.EmergencyEventCancelRequest
import com.journex.safety.data.remote.model.EmergencyEventCreateRequest
import com.journex.safety.data.remote.model.EmergencyEventDto
import com.journex.safety.data.remote.model.EmergencyEventEscalateRequest
import com.journex.safety.data.remote.model.EmergencyHistoryData
import com.journex.safety.data.remote.model.LocationApiResponse
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface JournexEmergencyApi {

    @POST("api/v1/emergency-events")
    suspend fun triggerEmergency(
        @Body request: EmergencyEventCreateRequest
    ): Response<LocationApiResponse<EmergencyEventDto>>

    @POST("api/v1/journeys/{journey_id}/emergency-events")
    suspend fun triggerJourneyEmergency(
        @Path("journey_id") journeyId: Long,
        @Body request: EmergencyEventCreateRequest
    ): Response<LocationApiResponse<EmergencyEventDto>>

    @GET("api/v1/emergency-events/{event_id}")
    suspend fun getEmergencyEvent(
        @Path("event_id") eventId: Long
    ): Response<LocationApiResponse<EmergencyEventDto>>

    @GET("api/v1/emergency-events")
    suspend fun listEmergencyEvents(
        @Query("page") page: Int = 1,
        @Query("per_page") perPage: Int = 10
    ): Response<LocationApiResponse<EmergencyHistoryData>>

    @POST("api/v1/emergency-events/{event_id}/cancel")
    suspend fun cancelEmergency(
        @Path("event_id") eventId: Long,
        @Body request: EmergencyEventCancelRequest
    ): Response<LocationApiResponse<EmergencyEventDto>>

    @POST("api/v1/emergency-events/{event_id}/escalate")
    suspend fun escalateEmergency(
        @Path("event_id") eventId: Long,
        @Body request: EmergencyEventEscalateRequest = EmergencyEventEscalateRequest()
    ): Response<LocationApiResponse<EmergencyEventDto>>

    @GET("api/v1/emergency-events/{event_id}/delivery-status")
    suspend fun getDeliveryStatus(
        @Path("event_id") eventId: Long
    ): Response<LocationApiResponse<EmergencyDeliveryStatusSummary>>
}
