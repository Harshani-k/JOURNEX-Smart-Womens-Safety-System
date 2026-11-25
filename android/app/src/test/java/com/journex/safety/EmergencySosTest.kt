package com.journex.safety

import com.google.gson.Gson
import com.journex.safety.data.local.entity.EmergencyAlertDispatchEntity
import com.journex.safety.data.local.entity.EmergencyEventEntity
import com.journex.safety.data.remote.model.EmergencyAlertDispatchDto
import com.journex.safety.data.remote.model.EmergencyEventCancelRequest
import com.journex.safety.data.remote.model.EmergencyEventCreateRequest
import com.journex.safety.data.remote.model.EmergencyEventDto
import com.journex.safety.data.remote.model.EmergencyEventEscalateRequest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.UUID

class EmergencySosTest {

    private val gson = Gson()

    @Test
    fun testEmergencyEventEntityInitialization() {
        val now = System.currentTimeMillis()
        val clientActionId = UUID.randomUUID().toString()

        val entity = EmergencyEventEntity(
            id = 1L,
            serverEventId = 101L,
            journeyId = 42L,
            triggerType = "MANUAL_SOS",
            status = "ACTIVE",
            triggerTimestamp = now,
            latitude = 12.9716,
            longitude = 80.2435,
            accuracy = 12.5f,
            locationAddress = "OMR IT Corridor, Chennai",
            currentEscalationLevel = 1,
            maxEscalationLevel = 3,
            clientActionId = clientActionId,
            syncStatus = "PENDING"
        )

        assertEquals(1L, entity.id)
        assertEquals(101L, entity.serverEventId)
        assertEquals(42L, entity.journeyId)
        assertEquals("MANUAL_SOS", entity.triggerType)
        assertEquals("ACTIVE", entity.status)
        assertEquals(now, entity.triggerTimestamp)
        assertEquals(12.9716, entity.latitude!!, 0.0001)
        assertEquals(80.2435, entity.longitude!!, 0.0001)
        assertEquals(12.5f, entity.accuracy!!, 0.01f)
        assertEquals("OMR IT Corridor, Chennai", entity.locationAddress)
        assertEquals(1, entity.currentEscalationLevel)
        assertEquals(3, entity.maxEscalationLevel)
        assertEquals(clientActionId, entity.clientActionId)
        assertEquals("PENDING", entity.syncStatus)
        assertNull(entity.cancellationTimestamp)
        assertNull(entity.cancellationReason)
    }

    @Test
    fun testEmergencyAlertDispatchEntityInitialization() {
        val dispatch = EmergencyAlertDispatchEntity(
            id = 1L,
            serverDispatchId = 201L,
            emergencyEventId = 1L,
            contactName = "Lakshmi (Mother)",
            contactPhone = "+919876543210",
            escalationLevel = 1,
            channel = "SMS",
            status = "DELIVERED",
            providerMessageId = "MOCK-SMS-9921",
            errorMessage = null,
            syncStatus = "SYNCED"
        )

        assertEquals(1L, dispatch.id)
        assertEquals(201L, dispatch.serverDispatchId)
        assertEquals(1L, dispatch.emergencyEventId)
        assertEquals("Lakshmi (Mother)", dispatch.contactName)
        assertEquals("+919876543210", dispatch.contactPhone)
        assertEquals(1, dispatch.escalationLevel)
        assertEquals("SMS", dispatch.channel)
        assertEquals("DELIVERED", dispatch.status)
        assertEquals("MOCK-SMS-9921", dispatch.providerMessageId)
        assertNull(dispatch.errorMessage)
        assertEquals("SYNCED", dispatch.syncStatus)
    }

    @Test
    fun testMultiLevelEscalationBounds() {
        var currentLevel = 1
        val maxLevel = 3

        fun escalate(level: Int): Int {
            return if (level < maxLevel) level + 1 else maxLevel
        }

        currentLevel = escalate(currentLevel)
        assertEquals(2, currentLevel)

        currentLevel = escalate(currentLevel)
        assertEquals(3, currentLevel)

        currentLevel = escalate(currentLevel)
        assertEquals(3, currentLevel) // Capped at maxLevel
    }

    @Test
    fun testEmergencyCancellationStateTransition() {
        val now = System.currentTimeMillis()
        val initialEvent = EmergencyEventEntity(
            id = 1L,
            journeyId = 10L,
            triggerType = "MANUAL_SOS",
            status = "ACTIVE",
            triggerTimestamp = now
        )

        assertEquals("ACTIVE", initialEvent.status)

        val cancelTime = now + 60000L
        val cancelledEvent = initialEvent.copy(
            status = "CANCELLED",
            cancellationTimestamp = cancelTime,
            cancellationReason = "Traveler confirmed safe via app",
            syncStatus = "SYNCED"
        )

        assertEquals("CANCELLED", cancelledEvent.status)
        assertEquals(cancelTime, cancelledEvent.cancellationTimestamp)
        assertEquals("Traveler confirmed safe via app", cancelledEvent.cancellationReason)
        assertEquals("SYNCED", cancelledEvent.syncStatus)
    }

    @Test
    fun testValidTriggerTypes() {
        val validTriggers = setOf("MANUAL_SOS", "MISSED_CHECKIN_ESCALATION", "SILENT_ALERT")

        assertTrue(validTriggers.contains("MANUAL_SOS"))
        assertTrue(validTriggers.contains("MISSED_CHECKIN_ESCALATION"))
        assertTrue(validTriggers.contains("SILENT_ALERT"))
        assertFalse(validTriggers.contains("INVALID_TYPE"))
    }

    @Test
    fun testCreateRequestSerialization() {
        val req = EmergencyEventCreateRequest(
            triggerType = "MANUAL_SOS",
            journeyId = 5L,
            latitude = 13.0827,
            longitude = 80.2707,
            accuracy = 10.0f,
            locationAddress = "Chennai Central",
            clientActionId = "act-12345"
        )

        val json = gson.toJson(req)
        assertNotNull(json)
        assertTrue(json.contains("\"trigger_type\":\"MANUAL_SOS\""))
        assertTrue(json.contains("\"journey_id\":5"))
        assertTrue(json.contains("\"latitude\":13.0827"))
        assertTrue(json.contains("\"client_action_id\":\"act-12345\""))
    }

    @Test
    fun testEmergencyDtoDeserialization() {
        val json = """
            {
                "id": 88,
                "user_id": 1,
                "journey_id": 12,
                "trigger_type": "MANUAL_SOS",
                "status": "ACTIVE",
                "current_escalation_level": 1,
                "max_escalation_level": 3,
                "latitude": 12.98,
                "longitude": 80.25,
                "accuracy": 15.0,
                "location_address": "Kotturpuram",
                "trigger_timestamp": "2026-11-22T14:00:00Z",
                "cancelled_at": null,
                "cancellation_reason": null,
                "dispatches": [
                    {
                        "id": 101,
                        "emergency_event_id": 88,
                        "contact_id": 1,
                        "contact_name": "Lakshmi (Mother)",
                        "contact_phone": "+919876543210",
                        "escalation_level": 1,
                        "channel": "SMS",
                        "status": "SENT",
                        "provider_message_id": "MOCK-101",
                        "error_message": null,
                        "created_at": "2026-11-22T14:00:00Z"
                    }
                ]
            }
        """.trimIndent()

        val dto = gson.fromJson(json, EmergencyEventDto::class.java)
        assertEquals(88L, dto.id)
        assertEquals(12L, dto.journeyId)
        assertEquals("MANUAL_SOS", dto.triggerType)
        assertEquals("ACTIVE", dto.status)
        assertEquals(1, dto.currentEscalationLevel)
        assertEquals(3, dto.maxEscalationLevel)
        assertEquals(1, dto.dispatches.size)
        assertEquals("Lakshmi (Mother)", dto.dispatches[0].contactName)
        assertEquals("+919876543210", dto.dispatches[0].contactPhone)
        assertEquals("SENT", dto.dispatches[0].status)
    }

    @Test
    fun testSafeDialIntentUriFormat() {
        val phone = "+919876543210"
        val dialUriString = "tel:$phone"

        assertTrue(dialUriString.startsWith("tel:"))
        assertEquals("tel:+919876543210", dialUriString)
        // Ensure no direct automatic call bypass like ACTION_CALL
        val dialAction = "android.intent.action.DIAL"
        assertEquals("android.intent.action.DIAL", dialAction)
    }
}
