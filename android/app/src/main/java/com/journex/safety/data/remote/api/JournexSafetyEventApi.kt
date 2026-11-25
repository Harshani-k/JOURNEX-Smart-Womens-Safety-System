package com.journex.safety.data.remote.api

import com.journex.safety.data.remote.model.ActiveSafetyEventsResponseData
import com.journex.safety.data.remote.model.LocationApiResponse
import com.journex.safety.data.remote.model.SafetyEventActionRequest
import com.journex.safety.data.remote.model.SafetyEventDto
import com.journex.safety.data.remote.model.SafetyEventListResponseData
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.Path

interface JournexSafetyEventApi {

    @GET("/api/v1/journeys/{journeyId}/safety-events")
    suspend fun listSafetyEvents(
        @Path("journeyId") journeyId: Long,
        @Header("Authorization") token: String
    ): Response<LocationApiResponse<SafetyEventListResponseData>>

    @GET("/api/v1/journeys/{journeyId}/safety-events/active")
    suspend fun getActiveSafetyEvents(
        @Path("journeyId") journeyId: Long,
        @Header("Authorization") token: String
    ): Response<LocationApiResponse<ActiveSafetyEventsResponseData>>

    @POST("/api/v1/journeys/{journeyId}/safety-events/{eventId}/acknowledge")
    suspend fun acknowledgeSafetyEvent(
        @Path("journeyId") journeyId: Long,
        @Path("eventId") eventId: Long,
        @Header("Authorization") token: String
    ): Response<LocationApiResponse<SafetyEventDto>>

    @POST("/api/v1/journeys/{journeyId}/safety-events/{eventId}/resolve")
    suspend fun resolveSafetyEvent(
        @Path("journeyId") journeyId: Long,
        @Path("eventId") eventId: Long,
        @Body request: SafetyEventActionRequest,
        @Header("Authorization") token: String
    ): Response<LocationApiResponse<SafetyEventDto>>
}
