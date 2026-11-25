package com.journex.safety

import android.app.Application
import com.journex.safety.data.local.JournexDatabase
import com.journex.safety.data.local.entity.ContactEntity
import com.journex.safety.data.local.entity.SafetyProfileEntity
import com.journex.safety.data.repository.JournexRepository
import com.journex.safety.data.repository.CheckInRepository
import com.journex.safety.data.repository.SafetyEventRepository
import com.journex.safety.data.repository.RiskAnalysisRepository
import com.journex.safety.data.repository.EmergencyRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class JournexApp : Application() {

    val database by lazy { JournexDatabase.getDatabase(this) }
    val repository by lazy { JournexRepository(database) }
    val checkInRepository by lazy { CheckInRepository(database) }
    val safetyEventRepository by lazy { SafetyEventRepository(database) }
    val riskAnalysisRepository by lazy { RiskAnalysisRepository(database) }
    val emergencyRepository by lazy { EmergencyRepository(database) }

    override fun onCreate() {
        super.onCreate()
        // Pre-populate default initial profile & emergency contacts if first launch
        CoroutineScope(Dispatchers.IO).launch {
            seedInitialDataIfEmpty()
        }
    }

    private suspend fun seedInitialDataIfEmpty() {
        val profile = database.safetyProfileDao().getProfile()
        if (profile == null) {
            database.safetyProfileDao().insertOrUpdate(
                SafetyProfileEntity(
                    id = 1,
                    fullName = "Harshini S",
                    bloodGroup = "O +ve",
                    allergies = "None recorded",
                    homeAddress = "Plot 42, Green Avenue, Chennai",
                    emergencyNotes = "Student commuter. Please contact primary guardian immediately in emergencies."
                )
            )
        }

        database.contactDao().getContactsCountFlow().collect { count ->
            if (count == 0) {
                repository.addContact("Mother (Lakshmi)", "Parent", "+91 98765 43210", isPrimary = true)
                repository.addContact("Father (Suresh)", "Parent", "+91 98765 43211", isPrimary = false)
                repository.addContact("Priya (Hostel Warden)", "Guardian", "+91 98765 43212", isPrimary = false)
            }
        }
    }
}
