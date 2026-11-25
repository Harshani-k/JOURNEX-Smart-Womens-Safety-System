package com.journex.safety

import android.Manifest
import com.journex.safety.utils.PermissionUtils
import org.junit.Assert.assertTrue
import org.junit.Test

class PermissionUtilsTest {

    @Test
    fun requiredLocationPermissions_containsFineAndCoarse() {
        val perms = PermissionUtils.REQUIRED_LOCATION_PERMISSIONS
        assertTrue(perms.contains(Manifest.permission.ACCESS_FINE_LOCATION))
        assertTrue(perms.contains(Manifest.permission.ACCESS_COARSE_LOCATION))
    }
}
