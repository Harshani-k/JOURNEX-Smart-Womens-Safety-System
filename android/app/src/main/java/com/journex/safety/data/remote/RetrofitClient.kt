package com.journex.safety.data.remote

import com.journex.safety.data.remote.api.JournexLocationApi
import com.journex.safety.data.remote.api.JournexCheckInApi
import com.journex.safety.data.remote.api.JournexSafetyEventApi
import com.journex.safety.data.remote.api.JournexRiskApi
import com.journex.safety.data.remote.api.JournexEmergencyApi
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object RetrofitClient {

    // Default to 127.0.0.1:5000 (accessible via 'adb reverse tcp:5000 tcp:5000' on physical USB device)
    // or 10.0.2.2:5000 for standard Android Emulator
    private const val BASE_URL = "http://127.0.0.1:5000/"

    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }

    private val okHttpClient = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(10, TimeUnit.SECONDS)
        .writeTimeout(10, TimeUnit.SECONDS)
        .addInterceptor(loggingInterceptor)
        .build()

    private val retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(okHttpClient)
        .addConverterFactory(GsonConverterFactory.create())
        .build()

    val locationApi: JournexLocationApi by lazy {
        retrofit.create(JournexLocationApi::class.java)
    }

    val checkInApi: JournexCheckInApi by lazy {
        retrofit.create(JournexCheckInApi::class.java)
    }

    val safetyEventApi: JournexSafetyEventApi by lazy {
        retrofit.create(JournexSafetyEventApi::class.java)
    }

    val riskApi: JournexRiskApi by lazy {
        retrofit.create(JournexRiskApi::class.java)
    }

    val emergencyApi: JournexEmergencyApi by lazy {
        retrofit.create(JournexEmergencyApi::class.java)
    }
}
