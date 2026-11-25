package com.journex.safety.data.repository

import com.journex.safety.data.local.JournexDatabase
import com.journex.safety.data.local.entity.CheckInRecordEntity
import com.journex.safety.data.local.entity.ContactEntity
import com.journex.safety.data.local.entity.IncidentJournalEntity
import com.journex.safety.data.local.entity.JourneyRecordEntity
import com.journex.safety.data.local.entity.SafetyProfileEntity
import com.journex.safety.data.security.JournalEncryptionHelper
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

data class DecryptedIncidentLog(
    val id: Long,
    val title: String,
    val timestamp: Long,
    val category: String,
    val decryptedNotes: String
)

class JournexRepository(
    private val database: JournexDatabase
) {
    // 1. Safety Profile
    val safetyProfileFlow: Flow<SafetyProfileEntity?> =
        database.safetyProfileDao().getProfileFlow()

    suspend fun saveSafetyProfile(profile: SafetyProfileEntity) {
        database.safetyProfileDao().insertOrUpdate(profile)
    }

    // 2. Trusted Contacts
    val trustedContactsFlow: Flow<List<ContactEntity>> =
        database.contactDao().getAllContactsFlow()

    val contactsCountFlow: Flow<Int> =
        database.contactDao().getContactsCountFlow()

    suspend fun addContact(name: String, relationship: String, phone: String, isPrimary: Boolean = false): Long {
        return database.contactDao().insert(
            ContactEntity(
                name = name,
                relationship = relationship,
                phone = phone,
                isPrimary = isPrimary
            )
        )
    }

    suspend fun deleteContact(contact: ContactEntity) {
        database.contactDao().delete(contact)
    }

    // 3. Journey Records
    val journeyHistoryFlow: Flow<List<JourneyRecordEntity>> =
        database.journeyRecordDao().getAllJourneysFlow()

    suspend fun recordCompletedJourney(
        destination: String,
        durationMinutes: Int,
        distanceKm: String,
        safetyStatus: String
    ): Long {
        return database.journeyRecordDao().insert(
            JourneyRecordEntity(
                destination = destination,
                durationMinutes = durationMinutes,
                distanceKm = distanceKm,
                safetyStatus = safetyStatus
            )
        )
    }

    suspend fun clearJourneyHistory() {
        database.journeyRecordDao().clearAll()
    }

    // 4. Check-In Records
    suspend fun logCheckIn(journeyId: Long, status: String, responseTimeSeconds: Int): Long {
        return database.checkInRecordDao().insert(
            CheckInRecordEntity(
                journeyId = journeyId,
                status = status,
                responseTimeSeconds = responseTimeSeconds
            )
        )
    }

    // 5. Incident Journal (AES-GCM KeyStore Encrypted)
    val decryptedIncidentLogsFlow: Flow<List<DecryptedIncidentLog>> =
        database.incidentJournalDao().getAllIncidentsFlow().map { list ->
            list.map { entity ->
                val decrypted = try {
                    JournalEncryptionHelper.decrypt(entity.encryptedNotes, entity.ivBase64)
                } catch (e: Exception) {
                    "[Decryption Error: Key mismatch]"
                }
                DecryptedIncidentLog(
                    id = entity.id,
                    title = entity.title,
                    timestamp = entity.timestamp,
                    category = entity.category,
                    decryptedNotes = decrypted
                )
            }
        }

    suspend fun addEncryptedIncident(title: String, category: String, notes: String): Long {
        val payload = JournalEncryptionHelper.encrypt(notes)
        return database.incidentJournalDao().insert(
            IncidentJournalEntity(
                title = title,
                category = category,
                encryptedNotes = payload.cipherTextBase64,
                ivBase64 = payload.ivBase64
            )
        )
    }

    suspend fun clearIncidentLogs() {
        database.incidentJournalDao().clearAll()
    }
}
