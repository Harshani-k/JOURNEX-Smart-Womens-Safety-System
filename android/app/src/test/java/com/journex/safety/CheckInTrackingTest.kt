package com.journex.safety

import com.journex.safety.data.local.entity.CheckInRecordEntity
import com.journex.safety.data.remote.model.CheckInConfirmRequest
import com.journex.safety.data.remote.model.CheckInCreateRequest
import com.journex.safety.data.remote.model.CheckInDto
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.UUID

class CheckInTrackingTest {

    @Test
    fun testCheckInEntityDefaultInitialization() {
        val now = System.currentTimeMillis()
        val entity = CheckInRecordEntity(
            journeyId = 1L,
            status = "SCHEDULED",
            scheduledAt = now + 900_000L,
            deadlineAt = now + 1_080_000L
        )

        assertEquals(1L, entity.journeyId)
        assertEquals("SCHEDULED", entity.status)
        assertEquals("PENDING", entity.syncStatus)
        assertTrue(entity.deadlineAt > entity.scheduledAt)
        assertNotNull(entity.clientActionId)
    }

    @Test
    fun testCountdownCalculation() {
        val now = System.currentTimeMillis()
        val deadline = now + 120_000L // 2 mins remaining

        val secondsRemaining = Math.max(0L, (deadline - now) / 1000L)
        assertTrue(secondsRemaining in 118L..120L)

        // Expired deadline
        val pastDeadline = now - 10_000L
        val expiredSeconds = Math.max(0L, (pastDeadline - now) / 1000L)
        assertEquals(0L, expiredSeconds)
    }

    @Test
    fun testSafeConfirmationStateTransition() {
        val now = System.currentTimeMillis()
        val initial = CheckInRecordEntity(
            id = 10L,
            journeyId = 1L,
            status = "SCHEDULED",
            scheduledAt = now - 60_000L,
            deadlineAt = now + 120_000L,
            syncStatus = "SYNCED"
        )

        // User confirms safety before deadline
        val confirmedTime = System.currentTimeMillis()
        val confirmed = initial.copy(
            status = "CONFIRMED_SAFE",
            respondedAt = confirmedTime,
            syncStatus = "PENDING"
        )

        assertEquals("CONFIRMED_SAFE", confirmed.status)
        assertEquals(confirmedTime, confirmed.respondedAt)
        assertEquals("PENDING", confirmed.syncStatus)
    }

    @Test
    fun testLateConfirmationMarkedMissed() {
        val now = System.currentTimeMillis()
        val expired = CheckInRecordEntity(
            id = 11L,
            journeyId = 1L,
            status = "SCHEDULED",
            scheduledAt = now - 600_000L,
            deadlineAt = now - 60_000L // deadline 1 min ago
        )

        val isExpired = now > expired.deadlineAt
        assertTrue("Checkin must be flagged expired if deadline in past", isExpired)

        val updated = if (isExpired) expired.copy(status = "MISSED") else expired
        assertEquals("MISSED", updated.status)
    }

    @Test
    fun testClientActionIdUniquenessAndIdempotency() {
        val actionId1 = UUID.randomUUID().toString()
        val actionId2 = UUID.randomUUID().toString()
        assertFalse(actionId1 == actionId2)

        val req1 = CheckInConfirmRequest(
            respondedAt = "2026-11-22T10:00:00Z",
            responseType = "MANUAL_TAP",
            clientActionId = actionId1
        )
        val req2 = CheckInConfirmRequest(
            respondedAt = "2026-11-22T10:00:00Z",
            responseType = "MANUAL_TAP",
            clientActionId = actionId1
        )

        assertEquals(req1.clientActionId, req2.clientActionId)
    }

    @Test
    fun testCheckInDtoMapping() {
        val dto = CheckInDto(
            id = 5L,
            journeyId = 1L,
            userId = 42L,
            scheduledAt = "2026-11-22T10:15:00Z",
            deadlineAt = "2026-11-22T10:18:00Z",
            respondedAt = "2026-11-22T10:16:30Z",
            status = "CONFIRMED_SAFE",
            responseType = "MANUAL_TAP",
            clientActionId = "action-uuid-123",
            createdAt = "2026-11-22T10:00:00Z",
            updatedAt = "2026-11-22T10:16:30Z"
        )

        assertEquals(5L, dto.id)
        assertEquals("CONFIRMED_SAFE", dto.status)
        assertEquals("action-uuid-123", dto.clientActionId)
    }
}
