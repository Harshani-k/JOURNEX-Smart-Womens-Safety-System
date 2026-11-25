package com.journex.safety.data.repository

import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import com.journex.safety.data.local.JournexDatabase
import com.journex.safety.data.local.entity.RiskAnalysisEntity
import com.journex.safety.data.remote.RetrofitClient
import com.journex.safety.data.remote.model.RiskAnalysisDto
import com.journex.safety.data.remote.model.RiskAnalysisRequest
import com.journex.safety.data.remote.model.RiskContributingFactorDto
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.withContext

class RiskAnalysisRepository(
    private val database: JournexDatabase,
    private val gson: Gson = Gson()
) {
    private val riskDao = database.riskAnalysisDao()
    private val riskApi = RetrofitClient.riskApi

    fun getLatestRiskFlow(journeyId: Long): Flow<RiskAnalysisEntity?> {
        return riskDao.getLatestRiskAnalysisFlow(journeyId)
    }

    suspend fun getLatestCachedRisk(journeyId: Long): RiskAnalysisEntity? = withContext(Dispatchers.IO) {
        riskDao.getLatestRiskAnalysis(journeyId)
    }

    suspend fun fetchLatestRisk(journeyId: Long): Result<RiskAnalysisEntity?> = withContext(Dispatchers.IO) {
        try {
            val response = riskApi.getLatestRisk(journeyId)
            if (response.isSuccessful && response.body()?.data != null) {
                val dto = response.body()!!.data!!
                val entity = mapDtoToEntity(dto)
                riskDao.insert(entity)
                Result.success(entity)
            } else {
                // If network failed or no data, fallback to cached entity
                val cached = riskDao.getLatestRiskAnalysis(journeyId)
                Result.success(cached)
            }
        } catch (e: Exception) {
            // Offline or network error: return local cached record
            val cached = riskDao.getLatestRiskAnalysis(journeyId)
            Result.success(cached)
        }
    }

    suspend fun requestRiskAnalysis(journeyId: Long, forceRecompute: Boolean = true): Result<RiskAnalysisEntity> = withContext(Dispatchers.IO) {
        try {
            val response = riskApi.analyzeRisk(journeyId, RiskAnalysisRequest(forceRecompute))
            if (response.isSuccessful && response.body()?.data != null) {
                val dto = response.body()!!.data!!
                val entity = mapDtoToEntity(dto)
                riskDao.insert(entity)
                Result.success(entity)
            } else {
                val cached = riskDao.getLatestRiskAnalysis(journeyId)
                if (cached != null) {
                    Result.success(cached)
                } else {
                    Result.failure(Exception("Failed to evaluate risk: HTTP ${response.code()}"))
                }
            }
        } catch (e: Exception) {
            val cached = riskDao.getLatestRiskAnalysis(journeyId)
            if (cached != null) {
                Result.success(cached)
            } else {
                Result.failure(e)
            }
        }
    }

    fun parseContributingFactors(json: String): List<RiskContributingFactorDto> {
        return try {
            val type = object : TypeToken<List<RiskContributingFactorDto>>() {}.type
            gson.fromJson(json, type) ?: emptyList()
        } catch (e: Exception) {
            emptyList()
        }
    }

    private fun mapDtoToEntity(dto: RiskAnalysisDto): RiskAnalysisEntity {
        val factorsJson = gson.toJson(dto.contributingFactors)
        val isInsufficient = dto.contributingFactors.any { it.factor.contains("Insufficient", ignoreCase = true) }
        return RiskAnalysisEntity(
            serverAnalysisId = dto.id,
            journeyId = dto.journeyId,
            riskScore = dto.riskScore,
            riskCategory = dto.riskCategory,
            contributingFactorsJson = factorsJson,
            modelVersion = dto.modelVersion,
            isInsufficientData = isInsufficient,
            analyzedAt = System.currentTimeMillis()
        )
    }
}
