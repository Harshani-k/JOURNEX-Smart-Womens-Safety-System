package com.journex.safety.ui.screens.profile

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.journex.safety.data.local.entity.SafetyProfileEntity
import com.journex.safety.data.repository.JournexRepository
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class ProfileViewModel(
    private val repository: JournexRepository
) : ViewModel() {

    val profile: StateFlow<SafetyProfileEntity?> = repository.safetyProfileFlow
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), null)

    fun saveProfile(
        fullName: String,
        bloodGroup: String,
        allergies: String,
        homeAddress: String,
        emergencyNotes: String
    ) {
        viewModelScope.launch {
            repository.saveSafetyProfile(
                SafetyProfileEntity(
                    id = 1,
                    fullName = fullName,
                    bloodGroup = bloodGroup,
                    allergies = allergies,
                    homeAddress = homeAddress,
                    emergencyNotes = emergencyNotes
                )
            )
        }
    }

    companion object {
        fun provideFactory(repository: JournexRepository): ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T {
                    return ProfileViewModel(repository) as T
                }
            }
    }
}
