package com.journex.safety

import com.journex.safety.data.security.JournalEncryptionHelper
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class JournalEncryptionTest {

    @Test
    fun encryptAndDecrypt_recoversOriginalPlainText() {
        val originalText = "Suspicious white sedan TN-09-AB-1234 following on pedestrian path."
        val payload = JournalEncryptionHelper.encrypt(originalText)

        assertTrue("Ciphertext should not be empty", payload.cipherTextBase64.isNotEmpty())
        assertTrue("IV should not be empty", payload.ivBase64.isNotEmpty())
        assertNotEquals("Ciphertext must not match plain text", originalText, payload.cipherTextBase64)

        val decrypted = JournalEncryptionHelper.decrypt(payload.cipherTextBase64, payload.ivBase64)
        assertEquals("Decrypted text must match original plain text", originalText, decrypted)
    }

    @Test
    fun encryptSameTextTwice_generatesUniqueIVsAndCiphertexts() {
        val text = "Confidential safety incident note"
        val payload1 = JournalEncryptionHelper.encrypt(text)
        val payload2 = JournalEncryptionHelper.encrypt(text)

        assertNotEquals("Each encryption should use a unique random IV", payload1.ivBase64, payload2.ivBase64)
        assertNotEquals("Different IVs must produce distinct ciphertexts", payload1.cipherTextBase64, payload2.cipherTextBase64)

        assertEquals(text, JournalEncryptionHelper.decrypt(payload1.cipherTextBase64, payload1.ivBase64))
        assertEquals(text, JournalEncryptionHelper.decrypt(payload2.cipherTextBase64, payload2.ivBase64))
    }

    @Test
    fun emptyString_handlesGracefully() {
        val payload = JournalEncryptionHelper.encrypt("")
        assertEquals("", payload.cipherTextBase64)
        assertEquals("", payload.ivBase64)

        val decrypted = JournalEncryptionHelper.decrypt("", "")
        assertEquals("", decrypted)
    }
}
