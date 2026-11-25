package com.journex.safety.location

import android.annotation.SuppressLint
import android.content.Context
import android.location.Location
import android.location.LocationManager
import android.os.Looper
import com.google.android.gms.location.FusedLocationProviderClient
import com.google.android.gms.location.LocationCallback
import com.google.android.gms.location.LocationRequest
import com.google.android.gms.location.LocationResult
import com.google.android.gms.location.LocationServices
import com.google.android.gms.location.Priority
import com.journex.safety.utils.PermissionUtils
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

data class GpsLocationFix(
    val latitude: Double,
    val longitude: Double,
    val accuracy: Float,
    val altitude: Double? = null,
    val speed: Float? = null,
    val bearing: Float? = null,
    val timestamp: Long = System.currentTimeMillis(),
    val provider: String = "fused_gps"
) {
    fun isValid(): Boolean {
        return latitude in -90.0..90.0 &&
                longitude in -180.0..180.0 &&
                accuracy > 0f &&
                accuracy <= 200f
    }
}

class RealLocationManager(private val context: Context) {

    private val fusedClient: FusedLocationProviderClient =
        LocationServices.getFusedLocationProviderClient(context)

    private val _currentLocation = MutableStateFlow<GpsLocationFix?>(null)
    val currentLocation: StateFlow<GpsLocationFix?> = _currentLocation.asStateFlow()

    private val _isTracking = MutableStateFlow(false)
    val isTracking: StateFlow<Boolean> = _isTracking.asStateFlow()

    private var activeCallback: LocationCallback? = null

    companion object {
        const val UPDATE_INTERVAL_MS = 5000L
        const val FASTEST_INTERVAL_MS = 2000L
        const val MIN_DISTANCE_METERS = 3.0f

        fun isLocationEnabled(context: Context): Boolean {
            val lm = context.getSystemService(Context.LOCATION_SERVICE) as? LocationManager
            return lm?.isProviderEnabled(LocationManager.GPS_PROVIDER) == true ||
                    lm?.isProviderEnabled(LocationManager.NETWORK_PROVIDER) == true
        }
    }

    @SuppressLint("MissingPermission")
    fun startUpdates(onLocationFix: (GpsLocationFix) -> Unit) {
        if (!PermissionUtils.hasLocationPermission(context)) {
            return
        }

        if (activeCallback != null) {
            return // Already tracking
        }

        val request = LocationRequest.Builder(Priority.PRIORITY_HIGH_ACCURACY, UPDATE_INTERVAL_MS)
            .setMinUpdateIntervalMillis(FASTEST_INTERVAL_MS)
            .setMinUpdateDistanceMeters(MIN_DISTANCE_METERS)
            .setWaitForAccurateLocation(false)
            .build()

        val callback = object : LocationCallback() {
            override fun onLocationResult(result: LocationResult) {
                for (loc in result.locations) {
                    val fix = GpsLocationFix(
                        latitude = loc.latitude,
                        longitude = loc.longitude,
                        accuracy = loc.accuracy,
                        altitude = if (loc.hasAltitude()) loc.altitude else null,
                        speed = if (loc.hasSpeed()) loc.speed else null,
                        bearing = if (loc.hasBearing()) loc.bearing else null,
                        timestamp = loc.time,
                        provider = loc.provider ?: "fused_gps"
                    )

                    if (fix.isValid()) {
                        _currentLocation.value = fix
                        onLocationFix(fix)
                    }
                }
            }
        }

        activeCallback = callback
        _isTracking.value = true
        fusedClient.requestLocationUpdates(request, callback, Looper.getMainLooper())
    }

    fun stopUpdates() {
        activeCallback?.let {
            fusedClient.removeLocationUpdates(it)
            activeCallback = null
        }
        _isTracking.value = false
    }
}
