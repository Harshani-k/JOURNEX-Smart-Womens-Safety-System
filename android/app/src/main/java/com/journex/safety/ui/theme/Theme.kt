package com.journex.safety.ui.theme

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val LightColorScheme = lightColorScheme(
    primary = PurplePrimary,
    onPrimary = BackgroundWhite,
    primaryContainer = LavenderSurface,
    onPrimaryContainer = PurpleDark,
    secondary = VioletSecondary,
    onSecondary = BackgroundWhite,
    secondaryContainer = LavenderPrimary,
    onSecondaryContainer = PurpleDark,
    tertiary = GuardianTeal,
    onTertiary = BackgroundWhite,
    tertiaryContainer = GuardianTealContainer,
    onTertiaryContainer = GuardianTeal,
    error = EmergencyRed,
    onError = BackgroundWhite,
    errorContainer = EmergencyRedContainer,
    onErrorContainer = EmergencyRedDark,
    background = BackgroundLightGrey,
    onBackground = TextPrimaryLight,
    surface = SurfaceCardWhite,
    onSurface = TextPrimaryLight,
    surfaceVariant = SurfaceVariantLight,
    onSurfaceVariant = TextSecondaryLight,
    outline = LavenderBorder
)

private val DarkColorScheme = darkColorScheme(
    primary = PurplePrimaryDark,
    onPrimary = BackgroundDark,
    primaryContainer = LavenderContainerDark,
    onPrimaryContainer = LavenderPrimary,
    secondary = PurpleLight,
    onSecondary = BackgroundDark,
    tertiary = GuardianTeal,
    onTertiary = BackgroundWhite,
    error = EmergencyRed,
    onError = BackgroundWhite,
    errorContainer = EmergencyRedDark,
    onErrorContainer = EmergencyRedContainer,
    background = BackgroundDark,
    onBackground = TextPrimaryDark,
    surface = SurfaceDark,
    onSurface = TextPrimaryDark,
    surfaceVariant = SurfaceVariantDark,
    onSurfaceVariant = TextSecondaryDark,
    outline = DividerDark
)

@Composable
fun JournexTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme
    val view = LocalView.current

    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.background.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
