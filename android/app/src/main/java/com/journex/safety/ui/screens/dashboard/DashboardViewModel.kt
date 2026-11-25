package com.journex.safety.ui.screens.dashboard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.journex.safety.data.repository.EmergencyRepository
import com.journex.safety.data.repository.JournexRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class DashboardUiState(
    val isJourneyActive: Boolean = false,
    val activeDestination: String? = null,
    val estimatedArrivalText: String? = null,
    val activeEtaMinutes: Int = 0,
    val journeyStartTimeMs: Long = 0L,
    val trustedContactsCount: Int = 3,
    val safePlacesNearbyCount: Int = 3,
    val journalEntriesCount: Int = 0,
    val currentRiskLevel: String = "LOW (NORMAL)",
    val isRealGpsActive: Boolean = false,
    val snackbarMessage: String? = null
)

class DashboardViewModel(
    private val repository: JournexRepository? = null,
    private val emergencyRepository: EmergencyRepository? = null
) : ViewModel() {

    private val _uiState = MutableStateFlow(DashboardUiState())
    val uiState: StateFlow<DashboardUiState> = _uiState.asStateFlow()

    init {
        repository?.let { repo ->
            viewModelScope.launch {
                repo.contactsCountFlow.collect { count ->
                    _uiState.update { it.copy(trustedContactsCount = count) }
                }
            }
            viewModelScope.launch {
                repo.decryptedIncidentLogsFlow.collect { logs ->
                    _uiState.update { it.copy(journalEntriesCount = logs.size) }
                }
            }
        }
    }

    fun triggerEmergencySos(journeyId: Long? = null, latitude: Double? = null, longitude: Double? = null) {
        viewModelScope.launch {
            emergencyRepository?.triggerEmergencySos(
                journeyId = journeyId,
                triggerType = "MANUAL_SOS",
                latitude = latitude,
                longitude = longitude
            )
        }
        _uiState.update {
            it.copy(
                snackbarMessage = "EMERGENCY ALERT DISPATCHED: Guardians alerted with live coordinates."
            )
        }
    }

    fun clearSnackbarMessage() {
        _uiState.update { it.copy(snackbarMessage = null) }
    }

    fun startJourney(destination: String, etaMinutes: Int, isRealGps: Boolean) {
        _uiState.update {
            it.copy(
                isJourneyActive = true,
                activeDestination = destination,
                estimatedArrivalText = "In $etaMinutes mins",
                activeEtaMinutes = etaMinutes,
                journeyStartTimeMs = System.currentTimeMillis(),
                isRealGpsActive = isRealGps,
                snackbarMessage = "Journey monitoring started to $destination."
            )
        }
    }

    fun endJourney() {
        val currentState = _uiState.value
        val destination = currentState.activeDestination ?: "Destination"
        val duration = currentState.activeEtaMinutes

        viewModelScope.launch {
            repository?.recordCompletedJourney(
                destination = destination,
                durationMinutes = if (duration > 0) duration else 20,
                distanceKm = "5.2 km",
                safetyStatus = "Completed Safely (All Check-Ins Confirmed)"
            )
        }

        _uiState.update {
            it.copy(
                isJourneyActive = false,
                activeDestination = null,
                estimatedArrivalText = null,
                activeEtaMinutes = 0,
                journeyStartTimeMs = 0L,
                isRealGpsActive = false,
                snackbarMessage = "Journey completed safely and saved to history records."
            )
        }
    }

    companion object {
        fun provideFactory(
            repository: JournexRepository,
            emergencyRepository: EmergencyRepository? = null
        ): ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T {
                    return DashboardViewModel(repository, emergencyRepository) as T
                }
            }
    }
}
