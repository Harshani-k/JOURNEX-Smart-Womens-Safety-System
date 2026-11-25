package com.journex.safety.data.repository

import com.journex.safety.data.local.dao.JourneyLocationDao
import com.journex.safety.data.remote.RetrofitClient
import com.journex.safety.data.remote.api.JournexLocationApi
import com.journex.safety.data.remote.model.LocationBatchUploadRequest
import com.journex.safety.data.remote.model.LocationUploadItemDto
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone

class LocationSyncRepository(
    private val locationDao: JourneyLocationDao,
    private val locationApi: JournexLocationApi = RetrofitClient.locationApi
) {

    private val isoDateFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US).apply {
        timeZone = TimeZone.getTimeZone("UTC")
    }

    suspend fun syncPendingLocations(journeyId: Long, bearerToken: String): Result<Int> {
        return withContext(Dispatchers.IO) {
            try {
                val pendingList = locationDao.getUnsyncedLocations(journeyId, limit = 50)
                if (pendingList.isEmpty()) {
                    return@withContext Result.success(0)
                }

                val dtos = pendingList.map { entity ->
                    LocationUploadItemDto(
                        latitude = entity.latitude,
                        longitude = entity.longitude,
                        accuracy = entity.accuracy,
                        altitude = entity.altitude,
                        speed = entity.speed,
                        bearing = entity.bearing,
                        recordedAt = isoDateFormat.format(Date(entity.recordedAt))
                    )
                }

                val request = LocationBatchUploadRequest(locations = dtos)
                val response = locationApi.uploadLocations(
                    journeyId = journeyId,
                    bearerToken = if (bearerToken.startsWith("Bearer ")) bearerToken else "Bearer $bearerToken",
                    request = request
                )

                if (response.isSuccessful && response.body()?.success == true) {
                    val ids = pendingList.map { it.id }
                    locationDao.markAsSynced(ids)
                    val count = response.body()?.data?.acceptedCount ?: ids.size
                    Result.success(count)
                } else {
                    val errorBody = response.errorBody()?.string() ?: response.message()
                    Result.failure(Exception("Upload failed: $errorBody"))
                }
            } catch (e: Exception) {
                Result.failure(e)
            }
        }
    }
}
