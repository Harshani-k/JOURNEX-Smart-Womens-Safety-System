package com.journex.safety

import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import com.journex.safety.data.local.entity.RiskAnalysisEntity
import com.journex.safety.data.remote.model.RiskAnalysisDto
import com.journex.safety.data.remote.model.RiskAnalysisRequest
import com.journex.safety.data.remote.model.RiskContributingFactorDto
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

class RiskAnalysisTest {

    private val gson = Gson()

    @Test
    fun testRiskAnalysisEntityInitialization() {
        val now = System.currentTimeMillis()
        val factorsJson = gson.toJson(listOf(
            RiskContributingFactorDto("Normal Corridor", "POSITIVE", "Within route corridor")
        ))

        val entity = RiskAnalysisEntity(
            journeyId = 10L,
            serverAnalysisId = 42L,
            riskScore = 0.05f,
            riskCategory = "LOW",
            contributingFactorsJson = factorsJson,
            modelVersion = "1.0.0-rf",
            isInsufficientData = false,
            analyzedAt = now
        )

        assertEquals(10L, entity.journeyId)
        assertEquals(42L, entity.serverAnalysisId)
        assertEquals(0.05f, entity.riskScore, 0.001f)
        assertEquals("LOW", entity.riskCategory)
        assertEquals("1.0.0-rf", entity.modelVersion)
        assertFalse(entity.isInsufficientData)
        assertEquals(now, entity.analyzedAt)
    }

    @Test
    fun testContributingFactorJsonSerializationAndParsing() {
        val originalFactors = listOf(
            RiskContributingFactorDto("Route Deviation Detected", "HIGH", "Vehicle diverted 546m from planned corridor."),
            RiskContributingFactorDto("Prolonged Unexpected Stop", "HIGH", "Stationary for 14 minutes away from destination.")
        )

        val json = gson.toJson(originalFactors)
        assertNotNull(json)
        assertTrue(json.contains("Route Deviation Detected"))

        val type = object : TypeToken<List<RiskContributingFactorDto>>() {}.type
        val parsed: List<RiskContributingFactorDto> = gson.fromJson(json, type)

        assertEquals(2, parsed.size)
        assertEquals("Route Deviation Detected", parsed[0].factor)
        assertEquals("HIGH", parsed[0].impact)
        assertEquals("Prolonged Unexpected Stop", parsed[1].factor)
    }

    @Test
    fun testInsufficientDataFlagRepresentation() {
        val factors = listOf(
            RiskContributingFactorDto("Insufficient Telemetry", "NEUTRAL", "Journey recently initiated; insufficient GPS history.")
        )
        val json = gson.toJson(factors)

        val entity = RiskAnalysisEntity(
            journeyId = 1L,
            riskScore = 0.05f,
            riskCategory = "LOW",
            contributingFactorsJson = json,
            isInsufficientData = true
        )

        assertTrue(entity.isInsufficientData)
        assertEquals("LOW", entity.riskCategory)
    }

    @Test
    fun testRiskCategoryThresholdMapping() {
        fun mapCategory(score: Float): String = when {
            score < 0.30f -> "LOW"
            score < 0.55f -> "MODERATE"
            score < 0.80f -> "HIGH"
            else -> "CRITICAL"
        }

        assertEquals("LOW", mapCategory(0.05f))
        assertEquals("LOW", mapCategory(0.29f))
        assertEquals("MODERATE", mapCategory(0.30f))
        assertEquals("MODERATE", mapCategory(0.54f))
        assertEquals("HIGH", mapCategory(0.55f))
        assertEquals("HIGH", mapCategory(0.79f))
        assertEquals("CRITICAL", mapCategory(0.80f))
        assertEquals("CRITICAL", mapCategory(0.95f))
    }

    @Test
    fun testRiskDtoMapping() {
        val dto = RiskAnalysisDto(
            id = 101L,
            journeyId = 22L,
            userId = 5L,
            riskScore = 0.72f,
            riskCategory = "HIGH",
            contributingFactors = listOf(
                RiskContributingFactorDto("Route Deviation Detected", "HIGH", "Diverted 750m.")
            ),
            modelVersion = "1.0.0-rf",
            analyzedAt = "2026-11-22T12:30:00Z"
        )

        assertEquals(101L, dto.id)
        assertEquals(22L, dto.journeyId)
        assertEquals("HIGH", dto.riskCategory)
        assertEquals(0.72f, dto.riskScore, 0.01f)
        assertEquals(1, dto.contributingFactors.size)
    }

    @Test
    fun testRiskAnalysisRequestSerialization() {
        val req = RiskAnalysisRequest(forceRecompute = true)
        val json = gson.toJson(req)
        assertTrue(json.contains("\"force_recompute\":true"))
    }
}
