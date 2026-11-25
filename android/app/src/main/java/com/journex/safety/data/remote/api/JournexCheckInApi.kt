package com.journex.safety.data.remote.api

import com.journex.safety.data.remote.model.CheckInConfirmRequest
import com.journex.safety.data.remote.model.CheckInCreateRequest
import com.journex.safety.data.remote.model.CheckInDto
import com.journex.safety.data.remote.model.CheckInListResponseData
import com.journex.safety.data.remote.model.DelayStatusDto
import com.journex.safety.data.remote.model.LocationApiResponse
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface JournexCheckInApi {

    @POST("api/v1/journeys/{journey_id}/checkins")
    suspend fun createCheckIn(
        @Path("journey_id") journeyId: Long,
        @Body request: CheckInCreateRequest,
        @Header("Authorization") token: String
    ): Response<LocationApiResponse<CheckInDto>>

    @GET("api/v1/journeys/{journey_id}/checkins")
    suspend fun listCheckIns(
        @Path("journey_id") journeyId: Long,
        @Query("page") page: Int = 1,
        @Query("per_page") perPage: Int = 10,
        @Header("Authorization") token: String
    ): Response<LocationApiResponse<CheckInListResponseData>>

    @GET("api/v1/journeys/{journey_id}/checkins/pending")
    suspend fun getPendingCheckIn(
        @Path("journey_id") journeyId: Long,
        @Header("Authorization") token: String
    ): Response<LocationApiResponse<CheckInDto?>>

    @POST("api/v1/checkins/{checkin_id}/confirm")
    suspend fun confirmCheckIn(
        @Path("checkin_id") checkinId: Long,
        @Body request: CheckInConfirmRequest,
        @Header("Authorization") token: String
    ): Response<LocationApiResponse<CheckInDto>>

    @POST("api/v1/checkins/{checkin_id}/cancel")
    suspend fun cancelCheckIn(
        @Path("checkin_id") checkinId: Long,
        @Header("Authorization") token: String
    ): Response<LocationApiResponse<CheckInDto>>

    @GET("api/v1/journeys/{journey_id}/delay")
    suspend fun getDelayStatus(
        @Path("journey_id") journeyId: Long,
        @Header("Authorization") token: String
    ): Response<LocationApiResponse<DelayStatusDto>>
}
