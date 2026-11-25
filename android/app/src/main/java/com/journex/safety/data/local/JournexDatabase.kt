package com.journex.safety.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase
import com.journex.safety.data.local.dao.CheckInRecordDao
import com.journex.safety.data.local.dao.ContactDao
import com.journex.safety.data.local.dao.IncidentJournalDao
import com.journex.safety.data.local.dao.JourneyLocationDao
import com.journex.safety.data.local.dao.JourneyRecordDao
import com.journex.safety.data.local.dao.SafetyProfileDao
import com.journex.safety.data.local.entity.CheckInRecordEntity
import com.journex.safety.data.local.entity.ContactEntity
import com.journex.safety.data.local.entity.IncidentJournalEntity
import com.journex.safety.data.local.entity.JourneyLocationEntity
import com.journex.safety.data.local.entity.JourneyRecordEntity
import com.journex.safety.data.local.dao.SafetyEventDao
import com.journex.safety.data.local.dao.RiskAnalysisDao
import com.journex.safety.data.local.dao.EmergencyEventDao
import com.journex.safety.data.local.dao.EmergencyAlertDispatchDao
import com.journex.safety.data.local.entity.SafetyEventEntity
import com.journex.safety.data.local.entity.RiskAnalysisEntity
import com.journex.safety.data.local.entity.EmergencyEventEntity
import com.journex.safety.data.local.entity.EmergencyAlertDispatchEntity
import com.journex.safety.data.local.entity.SafetyProfileEntity

@Database(
    entities = [
        SafetyProfileEntity::class,
        ContactEntity::class,
        JourneyRecordEntity::class,
        CheckInRecordEntity::class,
        IncidentJournalEntity::class,
        JourneyLocationEntity::class,
        SafetyEventEntity::class,
        RiskAnalysisEntity::class,
        EmergencyEventEntity::class,
        EmergencyAlertDispatchEntity::class
    ],
    version = 6,
    exportSchema = false
)
abstract class JournexDatabase : RoomDatabase() {

    abstract fun safetyProfileDao(): SafetyProfileDao
    abstract fun contactDao(): ContactDao
    abstract fun journeyRecordDao(): JourneyRecordDao
    abstract fun checkInRecordDao(): CheckInRecordDao
    abstract fun incidentJournalDao(): IncidentJournalDao
    abstract fun journeyLocationDao(): JourneyLocationDao
    abstract fun safetyEventDao(): SafetyEventDao
    abstract fun riskAnalysisDao(): RiskAnalysisDao
    abstract fun emergencyEventDao(): EmergencyEventDao
    abstract fun emergencyAlertDispatchDao(): EmergencyAlertDispatchDao

    companion object {
        @Volatile
        private var INSTANCE: JournexDatabase? = null

        val MIGRATION_2_3 = object : Migration(2, 3) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL("ALTER TABLE checkin_records ADD COLUMN serverCheckinId INTEGER")
                db.execSQL("ALTER TABLE checkin_records ADD COLUMN scheduledAt INTEGER NOT NULL DEFAULT 0")
                db.execSQL("ALTER TABLE checkin_records ADD COLUMN deadlineAt INTEGER NOT NULL DEFAULT 0")
                db.execSQL("ALTER TABLE checkin_records ADD COLUMN respondedAt INTEGER")
                db.execSQL("ALTER TABLE checkin_records ADD COLUMN responseType TEXT")
                db.execSQL("ALTER TABLE checkin_records ADD COLUMN clientActionId TEXT")
                db.execSQL("ALTER TABLE checkin_records ADD COLUMN syncStatus TEXT NOT NULL DEFAULT 'SYNCED'")
                db.execSQL("CREATE INDEX IF NOT EXISTS index_checkin_records_journeyId ON checkin_records(journeyId)")
                db.execSQL("CREATE INDEX IF NOT EXISTS index_checkin_records_status ON checkin_records(status)")
                db.execSQL("CREATE INDEX IF NOT EXISTS index_checkin_records_syncStatus ON checkin_records(syncStatus)")
            }
        }

        val MIGRATION_3_4 = object : Migration(3, 4) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL("""
                    CREATE TABLE IF NOT EXISTS safety_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        serverEventId INTEGER,
                        journeyId INTEGER NOT NULL,
                        eventType TEXT NOT NULL,
                        status TEXT NOT NULL,
                        triggerReason TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        latitude REAL,
                        longitude REAL,
                        deviationDistance REAL,
                        durationSeconds INTEGER,
                        detectedAt INTEGER NOT NULL,
                        acknowledgedAt INTEGER,
                        resolvedAt INTEGER,
                        resolutionNotes TEXT,
                        clientActionId TEXT,
                        syncStatus TEXT NOT NULL
                    )
                """.trimIndent())
                db.execSQL("CREATE INDEX IF NOT EXISTS index_safety_events_journeyId ON safety_events(journeyId)")
                db.execSQL("CREATE INDEX IF NOT EXISTS index_safety_events_status ON safety_events(status)")
                db.execSQL("CREATE INDEX IF NOT EXISTS index_safety_events_syncStatus ON safety_events(syncStatus)")
            }
        }

        val MIGRATION_4_5 = object : Migration(4, 5) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL("""
                    CREATE TABLE IF NOT EXISTS risk_analyses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        serverAnalysisId INTEGER,
                        journeyId INTEGER NOT NULL,
                        riskScore REAL NOT NULL,
                        riskCategory TEXT NOT NULL,
                        contributingFactorsJson TEXT NOT NULL,
                        modelVersion TEXT NOT NULL,
                        isInsufficientData INTEGER NOT NULL DEFAULT 0,
                        analyzedAt INTEGER NOT NULL,
                        createdAt INTEGER NOT NULL
                    )
                """.trimIndent())
                db.execSQL("CREATE INDEX IF NOT EXISTS index_risk_analyses_journeyId ON risk_analyses(journeyId)")
                db.execSQL("CREATE INDEX IF NOT EXISTS index_risk_analyses_analyzedAt ON risk_analyses(analyzedAt)")
            }
        }

        val MIGRATION_5_6 = object : Migration(5, 6) {
            override fun migrate(db: SupportSQLiteDatabase) {
                db.execSQL("""
                    CREATE TABLE IF NOT EXISTS emergency_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        serverEventId INTEGER,
                        journeyId INTEGER,
                        triggerType TEXT NOT NULL,
                        status TEXT NOT NULL,
                        triggerTimestamp INTEGER NOT NULL,
                        cancellationTimestamp INTEGER,
                        cancellationReason TEXT,
                        latitude REAL,
                        longitude REAL,
                        accuracy REAL,
                        locationAddress TEXT,
                        currentEscalationLevel INTEGER NOT NULL DEFAULT 1,
                        maxEscalationLevel INTEGER NOT NULL DEFAULT 3,
                        clientActionId TEXT NOT NULL,
                        syncStatus TEXT NOT NULL DEFAULT 'PENDING',
                        createdAt INTEGER NOT NULL,
                        updatedAt INTEGER NOT NULL
                    )
                """.trimIndent())
                db.execSQL("CREATE INDEX IF NOT EXISTS index_emergency_events_journeyId ON emergency_events(journeyId)")
                db.execSQL("CREATE INDEX IF NOT EXISTS index_emergency_events_status ON emergency_events(status)")
                db.execSQL("CREATE INDEX IF NOT EXISTS index_emergency_events_triggerTimestamp ON emergency_events(triggerTimestamp)")

                db.execSQL("""
                    CREATE TABLE IF NOT EXISTS emergency_alert_dispatches (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        serverDispatchId INTEGER,
                        emergencyEventId INTEGER NOT NULL,
                        contactName TEXT NOT NULL,
                        contactPhone TEXT NOT NULL,
                        escalationLevel INTEGER NOT NULL DEFAULT 1,
                        channel TEXT NOT NULL DEFAULT 'SMS',
                        status TEXT NOT NULL DEFAULT 'PENDING',
                        providerMessageId TEXT,
                        errorMessage TEXT,
                        sentAt INTEGER,
                        deliveredAt INTEGER,
                        syncStatus TEXT NOT NULL DEFAULT 'PENDING'
                    )
                """.trimIndent())
                db.execSQL("CREATE INDEX IF NOT EXISTS index_dispatches_eventId ON emergency_alert_dispatches(emergencyEventId)")
                db.execSQL("CREATE INDEX IF NOT EXISTS index_dispatches_status ON emergency_alert_dispatches(status)")
            }
        }

        fun getDatabase(context: Context): JournexDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    JournexDatabase::class.java,
                    "journex_safety.db"
                )
                    .addMigrations(MIGRATION_2_3, MIGRATION_3_4, MIGRATION_4_5, MIGRATION_5_6)
                    .fallbackToDestructiveMigration()
                    .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
