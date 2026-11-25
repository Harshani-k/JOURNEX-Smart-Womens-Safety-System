package com.journex.safety.data.remote.model

import com.google.gson.annotations.SerializedName

data class RiskContributingFactorDto(
    @SerializedName("factor") val factor: String,
    @SerializedName("impact") val impact: String, // "POSITIVE", "LOW", "MODERATE", "HIGH", "CRITICAL", "NEUTRAL"
    @SerializedName("description") val description: String
)

data class RiskAnalysisDto(
    @SerializedName("id") val id: Long,
    @SerializedName("journey_id") val journeyId: Long,
    @SerializedName("user_id") val userId: Long,
    @SerializedName("risk_score") val riskScore: Float,
    @SerializedName("risk_category") val riskCategory: String, // "LOW", "MODERATE", "HIGH", "CRITICAL"
    @SerializedName("contributing_factors") val contributingFactors: List<RiskContributingFactorDto> = emptyList(),
    @SerializedName("model_version") val modelVersion: String = "1.0.0-rf",
    @SerializedName("analyzed_at") val analyzedAt: String,
    @SerializedName("created_at") val createdAt: String? = null
)

data class RiskAnalysisRequest(
    @SerializedName("force_recompute") val forceRecompute: Boolean = true
)

data class RiskHistoryData(
    @SerializedName("history") val history: List<RiskAnalysisDto> = emptyList(),
    @SerializedName("count") val count: Int = 0
)
