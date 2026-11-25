package com.journex.safety.data.remote.api

import com.journex.safety.data.remote.model.LocationApiResponse
import com.journex.safety.data.remote.model.LocationBatchUploadRequest
import com.journex.safety.data.remote.model.LocationUploadItemDto
import com.journex.safety.data.remote.model.LocationUploadResponseData
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.Path

interface JournexLocationApi {

    @POST("api/v1/journeys/{journeyId}/locations")
    suspend fun uploadLocations(
        @Path("journeyId") journeyId: Long,
        @Header("Authorization") bearerToken: String,
        @Body request: LocationBatchUploadRequest
    ): Response<LocationApiResponse<LocationUploadResponseData>>

    @GET("api/v1/journeys/{journeyId}/locations/latest")
    suspend fun getLatestLocation(
        @Path("journeyId") journeyId: Long,
        @Header("Authorization") bearerToken: String
    ): Response<LocationApiResponse<LocationUploadItemDto>>
}
