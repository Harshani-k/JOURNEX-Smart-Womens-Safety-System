package com.journex.safety

import com.journex.safety.data.local.entity.JourneyLocationEntity
import com.journex.safety.data.remote.model.LocationUploadItemDto
import com.journex.safety.location.GpsLocationFix
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

class GpsTrackingTest {

    @Test
    fun testValidGpsLocationFix() {
        val fix = GpsLocationFix(
            latitude = 12.971598,
            longitude = 77.594566,
            accuracy = 8.5f,
            speed = 12.0f,
            bearing = 180.0f
        )
        assertTrue("Valid GPS fix should pass validation", fix.isValid())
    }

    @Test
    fun testInvalidLatitudeRejected() {
        val badLat = GpsLocationFix(
            latitude = 95.0,
            longitude = 77.0,
            accuracy = 5.0f
        )
        assertFalse("Latitude > 90 must be invalid", badLat.isValid())

        val badLatNeg = GpsLocationFix(
            latitude = -91.0,
            longitude = 77.0,
            accuracy = 5.0f
        )
        assertFalse("Latitude < -90 must be invalid", badLatNeg.isValid())
    }

    @Test
    fun testInvalidLongitudeRejected() {
        val badLng = GpsLocationFix(
            latitude = 12.0,
            longitude = 185.0,
            accuracy = 5.0f
        )
        assertFalse("Longitude > 180 must be invalid", badLng.isValid())

        val badLngNeg = GpsLocationFix(
            latitude = 12.0,
            longitude = -185.0,
            accuracy = 5.0f
        )
        assertFalse("Longitude < -180 must be invalid", badLngNeg.isValid())
    }

    @Test
    fun testInvalidAccuracyRejected() {
        val zeroAcc = GpsLocationFix(
            latitude = 12.0,
            longitude = 77.0,
            accuracy = 0.0f
        )
        assertFalse("Accuracy == 0 must be invalid", zeroAcc.isValid())

        val highAcc = GpsLocationFix(
            latitude = 12.0,
            longitude = 77.0,
            accuracy = 250.0f
        )
        assertFalse("Accuracy > 200m must be rejected as inaccurate fix", highAcc.isValid())
    }

    @Test
    fun testJourneyLocationEntityCreation() {
        val entity = JourneyLocationEntity(
            id = 101L,
            journeyId = 1L,
            latitude = 12.9756,
            longitude = 77.6066,
            accuracy = 6.2f,
            speed = 8.5f,
            bearing = 90.0f,
            syncStatus = "PENDING"
        )
        assertEquals(101L, entity.id)
        assertEquals(1L, entity.journeyId)
        assertEquals("PENDING", entity.syncStatus)
        assertEquals(12.9756, entity.latitude, 0.0001)
    }

    @Test
    fun testLocationUploadItemDtoMapping() {
        val entity = JourneyLocationEntity(
            id = 1L,
            journeyId = 42L,
            latitude = 13.0827,
            longitude = 80.2707,
            accuracy = 4.0f,
            altitude = 15.0,
            speed = 5.0f,
            bearing = 45.0f
        )

        val dto = LocationUploadItemDto(
            latitude = entity.latitude,
            longitude = entity.longitude,
            accuracy = entity.accuracy,
            altitude = entity.altitude,
            speed = entity.speed,
            bearing = entity.bearing,
            recordedAt = "2026-11-22T08:00:00Z"
        )

        assertEquals(13.0827, dto.latitude, 0.0001)
        assertEquals(80.2707, dto.longitude, 0.0001)
        assertEquals(4.0f, dto.accuracy, 0.01f)
        assertNotNull(dto.recordedAt)
    }
}
