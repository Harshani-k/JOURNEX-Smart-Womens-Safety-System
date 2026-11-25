package com.journex.safety.data.remote.api

import com.journex.safety.data.remote.model.LocationApiResponse
import com.journex.safety.data.remote.model.RiskAnalysisDto
import com.journex.safety.data.remote.model.RiskAnalysisRequest
import com.journex.safety.data.remote.model.RiskHistoryData
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query

interface JournexRiskApi {

    @POST("api/v1/journeys/{journey_id}/risk-analysis")
    suspend fun analyzeRisk(
        @Path("journey_id") journeyId: Long,
        @Body request: RiskAnalysisRequest = RiskAnalysisRequest(forceRecompute = true)
    ): Response<LocationApiResponse<RiskAnalysisDto>>

    @GET("api/v1/journeys/{journey_id}/risk-analysis/latest")
    suspend fun getLatestRisk(
        @Path("journey_id") journeyId: Long
    ): Response<LocationApiResponse<RiskAnalysisDto?>>

    @GET("api/v1/journeys/{journey_id}/risk-analysis/history")
    suspend fun getRiskHistory(
        @Path("journey_id") journeyId: Long,
        @Query("limit") limit: Int = 20
    ): Response<LocationApiResponse<RiskHistoryData>>
}
