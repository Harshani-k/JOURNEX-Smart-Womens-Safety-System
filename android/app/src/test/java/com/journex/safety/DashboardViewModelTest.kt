package com.journex.safety

import com.journex.safety.ui.screens.dashboard.DashboardViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class DashboardViewModelTest {

    private val testDispatcher = StandardTestDispatcher()
    private lateinit var viewModel: DashboardViewModel

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        viewModel = DashboardViewModel(repository = null)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun initialState_hasNoActiveJourney() {
        val state = viewModel.uiState.value
        assertFalse("Initial state should not have active journey", state.isJourneyActive)
        assertNull("Initial destination should be null", state.activeDestination)
        assertNull("Initial ETA should be null", state.estimatedArrivalText)
        assertEquals("Initial risk level should be normal", "LOW (NORMAL)", state.currentRiskLevel)
    }

    @Test
    fun startJourney_updatesStateToActive() = runTest {
        viewModel.startJourney(
            destination = "University Library",
            etaMinutes = 30,
            isRealGps = true
        )

        val state = viewModel.uiState.value
        assertTrue("Journey should be active", state.isJourneyActive)
        assertEquals("University Library", state.activeDestination)
        assertEquals("In 30 mins", state.estimatedArrivalText)
        assertEquals(30, state.activeEtaMinutes)
        assertTrue("Real GPS should be active", state.isRealGpsActive)
        assertTrue("Journey start time should be non-zero", state.journeyStartTimeMs > 0L)
    }

    @Test
    fun endJourney_resetsStateToInactive() = runTest {
        viewModel.startJourney("City Hospital", 15, false)
        assertTrue(viewModel.uiState.value.isJourneyActive)

        viewModel.endJourney()

        val state = viewModel.uiState.value
        assertFalse("Journey should be inactive after ending", state.isJourneyActive)
        assertNull("Destination should be cleared", state.activeDestination)
        assertNull("ETA should be cleared", state.estimatedArrivalText)
        assertNotNull("Snackbar completion message should be set", state.snackbarMessage)
    }

    @Test
    fun triggerEmergencySos_setsEmergencyAlertInState() = runTest {
        viewModel.triggerEmergencySos()

        val state = viewModel.uiState.value
        assertNotNull(state.snackbarMessage)
        assertTrue(
            "Snackbar should contain EMERGENCY ALERT DISPATCHED",
            state.snackbarMessage!!.contains("EMERGENCY ALERT DISPATCHED")
        )

        viewModel.clearSnackbarMessage()
        assertNull(viewModel.uiState.value.snackbarMessage)
    }
}
