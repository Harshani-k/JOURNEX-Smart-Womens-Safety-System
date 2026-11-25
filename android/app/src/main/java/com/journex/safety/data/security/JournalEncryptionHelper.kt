package com.journex.safety.data.security

import java.security.KeyStore
import java.security.SecureRandom
import java.util.Base64
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

data class EncryptedPayload(
    val cipherTextBase64: String,
    val ivBase64: String
)

/**
 * JournalEncryptionHelper:
 * Implements hardware-backed AES-256-GCM encryption using the Android KeyStore.
 * Falls back to an in-memory software key during local JVM unit testing.
 */
object JournalEncryptionHelper {

    private const val ANDROID_KEYSTORE = "AndroidKeyStore"
    private const val KEY_ALIAS = "JournexJournalKey"
    private const val TRANSFORMATION = "AES/GCM/NoPadding"
    private const val GCM_TAG_LENGTH = 128
    private const val IV_LENGTH = 12

    private var fallbackTestKey: SecretKey? = null

    private fun getSecretKey(): SecretKey {
        return try {
            val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }
            if (!keyStore.containsAlias(KEY_ALIAS)) {
                val keyGen = KeyGenerator.getInstance("AES", ANDROID_KEYSTORE)
                val keySpec = android.security.keystore.KeyGenParameterSpec.Builder(
                    KEY_ALIAS,
                    android.security.keystore.KeyProperties.PURPOSE_ENCRYPT or android.security.keystore.KeyProperties.PURPOSE_DECRYPT
                )
                    .setBlockModes(android.security.keystore.KeyProperties.BLOCK_MODE_GCM)
                    .setEncryptionPaddings(android.security.keystore.KeyProperties.ENCRYPTION_PADDING_NONE)
                    .setKeySize(256)
                    .build()
                keyGen.init(keySpec)
                keyGen.generateKey()
            } else {
                keyStore.getKey(KEY_ALIAS, null) as SecretKey
            }
        } catch (e: Exception) {
            // Fallback for JVM unit tests without Android KeyStore service
            fallbackTestKey ?: synchronized(this) {
                fallbackTestKey ?: run {
                    val keyGen = KeyGenerator.getInstance("AES")
                    keyGen.init(256, SecureRandom())
                    val generated = keyGen.generateKey()
                    fallbackTestKey = generated
                    generated
                }
            }
        }
    }

    fun encrypt(plainText: String): EncryptedPayload {
        if (plainText.isEmpty()) return EncryptedPayload("", "")
        val key = getSecretKey()
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, key)
        val iv = cipher.iv
        val encryptedBytes = cipher.doFinal(plainText.toByteArray(Charsets.UTF_8))
        return EncryptedPayload(
            cipherTextBase64 = Base64.getEncoder().encodeToString(encryptedBytes),
            ivBase64 = Base64.getEncoder().encodeToString(iv)
        )
    }

    fun decrypt(cipherTextBase64: String, ivBase64: String): String {
        if (cipherTextBase64.isEmpty() || ivBase64.isEmpty()) return ""
        val key = getSecretKey()
        val iv = Base64.getDecoder().decode(ivBase64)
        val encryptedBytes = Base64.getDecoder().decode(cipherTextBase64)
        val cipher = Cipher.getInstance(TRANSFORMATION)
        val spec = GCMParameterSpec(GCM_TAG_LENGTH, iv)
        cipher.init(Cipher.DECRYPT_MODE, key, spec)
        val decryptedBytes = cipher.doFinal(encryptedBytes)
        return String(decryptedBytes, Charsets.UTF_8)
    }
}
