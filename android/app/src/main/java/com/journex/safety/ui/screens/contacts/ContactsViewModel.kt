package com.journex.safety.ui.screens.contacts

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.journex.safety.data.local.entity.ContactEntity
import com.journex.safety.data.repository.JournexRepository
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class ContactsViewModel(
    private val repository: JournexRepository
) : ViewModel() {

    val contacts: StateFlow<List<ContactEntity>> = repository.trustedContactsFlow
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    fun addContact(name: String, relationship: String, phone: String, isPrimary: Boolean = false) {
        viewModelScope.launch {
            repository.addContact(name, relationship, phone, isPrimary)
        }
    }

    fun deleteContact(contact: ContactEntity) {
        viewModelScope.launch {
            repository.deleteContact(contact)
        }
    }

    companion object {
        fun provideFactory(repository: JournexRepository): ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T {
                    return ContactsViewModel(repository) as T
                }
            }
    }
}
