package com.journex.safety.ui.screens.journal

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.journex.safety.data.repository.DecryptedIncidentLog
import com.journex.safety.data.repository.JournexRepository
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class JournalViewModel(
    private val repository: JournexRepository
) : ViewModel() {

    val incidentLogs: StateFlow<List<DecryptedIncidentLog>> = repository.decryptedIncidentLogsFlow
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    fun addIncident(title: String, category: String, notes: String) {
        viewModelScope.launch {
            repository.addEncryptedIncident(title, category, notes)
        }
    }

    fun clearAll() {
        viewModelScope.launch {
            repository.clearIncidentLogs()
        }
    }

    companion object {
        fun provideFactory(repository: JournexRepository): ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T {
                    return JournalViewModel(repository) as T
                }
            }
    }
}
