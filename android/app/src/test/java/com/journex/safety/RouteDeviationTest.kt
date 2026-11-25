package com.journex.safety

import com.journex.safety.data.local.entity.SafetyEventEntity
import com.journex.safety.data.remote.model.SafetyEventActionRequest
import com.journex.safety.data.remote.model.SafetyEventDto
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.UUID

class RouteDeviationTest {

    @Test
    fun testSafetyEventEntityInitialization() {
        val now = System.currentTimeMillis()
        val event = SafetyEventEntity(
            journeyId = 1L,
            eventType = "ROUTE_DEVIATION",
            status = "ACTIVE",
            triggerReason = "Deviated 350m from planned route corridor",
            severity = "MEDIUM",
            deviationDistance = 350.0,
            detectedAt = now
        )

        assertEquals(1L, event.journeyId)
        assertEquals("ROUTE_DEVIATION", event.eventType)
        assertEquals("ACTIVE", event.status)
        assertEquals("PENDING", event.syncStatus)
        assertEquals(350.0, event.deviationDistance!!, 0.01)
        assertNotNull(event.clientActionId)
    }

    @Test
    fun testAcknowledgeStateTransition() {
        val now = System.currentTimeMillis()
        val initial = SafetyEventEntity(
            id = 5L,
            journeyId = 1L,
            eventType = "ROUTE_DEVIATION",
            status = "ACTIVE",
            triggerReason = "Deviation observed",
            syncStatus = "SYNCED"
        )

        val ackTime = now + 5000L
        val acknowledged = initial.copy(
            status = "ACKNOWLEDGED",
            acknowledgedAt = ackTime,
            syncStatus = "PENDING"
        )

        assertEquals("ACKNOWLEDGED", acknowledged.status)
        assertEquals(ackTime, acknowledged.acknowledgedAt)
        assertEquals("PENDING", acknowledged.syncStatus)
    }

    @Test
    fun testResolveStateTransitionWithNotes() {
        val now = System.currentTimeMillis()
        val initial = SafetyEventEntity(
            id = 6L,
            journeyId = 1L,
            eventType = "UNEXPECTED_STOP",
            status = "ACTIVE",
            triggerReason = "Vehicle stationary for 12 mins",
            syncStatus = "SYNCED"
        )

        val resTime = now + 10000L
        val resolved = initial.copy(
            status = "RESOLVED",
            resolvedAt = resTime,
            resolutionNotes = "Driver refueled at gas station",
            syncStatus = "PENDING"
        )

        assertEquals("RESOLVED", resolved.status)
        assertEquals(resTime, resolved.resolvedAt)
        assertEquals("Driver refueled at gas station", resolved.resolutionNotes)
        assertEquals("PENDING", resolved.syncStatus)
    }

    @Test
    fun testSafetyEventDtoMapping() {
        val dto = SafetyEventDto(
            id = 10L,
            journeyId = 2L,
            userId = 42L,
            eventType = "ROUTE_DEVIATION",
            status = "ACTIVE",
            triggerReason = "Deviated 450m from expected corridor",
            severity = "HIGH",
            latitude = 11.0350,
            longitude = 77.0150,
            accuracy = 12.0f,
            deviationDistance = 450.0,
            durationSeconds = null,
            consecutiveCount = 3,
            detectedAt = "2026-11-22T17:30:00Z",
            acknowledgedAt = null,
            resolvedAt = null,
            resolutionNotes = null,
            clientActionId = "uuid-act-123",
            createdAt = "2026-11-22T17:30:00Z",
            updatedAt = "2026-11-22T17:30:00Z"
        )

        assertEquals(10L, dto.id)
        assertEquals("ROUTE_DEVIATION", dto.eventType)
        assertEquals("ACTIVE", dto.status)
        assertEquals(450.0, dto.deviationDistance!!, 0.01)
        assertEquals(3, dto.consecutiveCount)
    }

    @Test
    fun testActionRequestSerialization() {
        val actionId = UUID.randomUUID().toString()
        val req = SafetyEventActionRequest(
            resolutionNotes = "Detour due to construction",
            clientActionId = actionId
        )

        assertEquals("Detour due to construction", req.resolutionNotes)
        assertEquals(actionId, req.clientActionId)
    }
}
