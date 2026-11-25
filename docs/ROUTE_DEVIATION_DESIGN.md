# JOURNEX – Phase 6: Route Deviation & Unexpected Stop System Design

**Project:** JOURNEX – Smart Women's Safety Check-In and Journey Monitoring System  
**Document:** System Design & Technical Specification  
**Component:** Route Deviation & Stop Anomaly Engine (Backend Service & Android Client)  
**Version:** 1.0.0  
**Phase:** 6  

---

## 1. System Overview & Problem Statement

During solo travel, route deviations (divergence from planned corridors) and unexpected prolonged stops in unfamiliar areas represent critical risk precursors. However, real-world GPS signals are noisy, urban canyons cause momentary multipath scattering, and normal traffic delays can mimic vehicle stops.

The **JOURNEX Route Deviation & Unexpected Stop Subsystem** introduces:
1. **Mathematical Cross-Track Corridor Modeling:** Calculates exact point-to-segment geographic distance from real-time GPS fixes to the planned route corridor.
2. **Provisional Geodesic Corridor Detection Strategy:** When detailed turn-by-turn routing polylines are unavailable, a geodesic great-circle corridor between origin and destination coordinates is utilized with configurable tolerance.
3. **Multi-Observation Noise Filtering:** Enforces strict accuracy gates ($\le 50.0$m) and requires **at least 3 consecutive deviated observations** before triggering an anomaly event, eliminating false alarms from momentary turns or fly-away fixes.
4. **Traffic-Aware Unexpected Stop Heuristic:** Analyzes historical velocity and cluster displacement over a 10-minute window, distinguishing stop-and-go traffic from static vehicle immobility.
5. **Traveler Agency & Non-Intrusive Safety Rules:** Deviation and stop warnings never automatically trigger emergency phone calls or cancel trips. Travelers can easily acknowledge or resolve alerts with contextual reasons (e.g. "Taking alternate route", "Stopping for fuel").

---

## 2. Mathematical Algorithms

### 2.1 Great-Circle Cross-Track Distance Formula

Given:
- Origin $A = (\phi_1, \lambda_1)$
- Destination $B = (\phi_2, \lambda_2)$
- Current GPS Observation $P = (\phi_3, \lambda_3)$
- Earth Mean Radius $R = 6,371,000 \text{ m}$

#### Step 1: Angular Distance and Bearings
$$\Delta\phi = \phi_3 - \phi_1, \quad \Delta\lambda = \lambda_3 - \lambda_1$$
$$d(A, P) = R \cdot 2 \arcsin\left(\sqrt{\sin^2(\Delta\phi/2) + \cos\phi_1 \cos\phi_3 \sin^2(\Delta\lambda/2)}\right)$$
$$\delta_{AP} = \frac{d(A, P)}{R}$$

Initial Bearings:
$$\theta_{AB} = \text{atan2}\left(\sin(\lambda_2 - \lambda_1)\cos\phi_2, \cos\phi_1\sin\phi_2 - \sin\phi_1\cos\phi_2\cos(\lambda_2 - \lambda_1)\right)$$
$$\theta_{AP} = \text{atan2}\left(\sin(\lambda_3 - \lambda_1)\cos\phi_3, \cos\phi_1\sin\phi_3 - \sin\phi_1\cos\phi_3\cos(\lambda_3 - \lambda_1)\right)$$

#### Step 2: Cross-Track Distance ($d_{xt}$)
$$d_{xt} = \left|\arcsin\left(\sin\delta_{AP} \cdot \sin(\theta_{AP} - \theta_{AB})\right)\right| \cdot R$$

#### Step 3: Along-Track Distance ($d_{at}$) & Segment Clamping
$$d_{at} = \arccos\left(\frac{\cos\delta_{AP}}{\cos(d_{xt}/R)}\right) \cdot R$$

- If $\cos(\theta_{AP} - \theta_{AB}) < 0$ (projection falls behind Origin $A$):
  $$\text{Effective Distance} = d(A, P)$$
- If $d_{at} > d(A, B)$ (projection extends past Destination $B$):
  $$\text{Effective Distance} = d(B, P)$$
- Otherwise (projection lies along segment $AB$):
  $$\text{Effective Distance} = d_{xt}$$

---

## 3. Heuristic Rules & Noise Filtering

### 3.1 Route Deviation Evaluation
| Parameter | Default Value | Purpose |
|---|---|---|
| `corridor_threshold_meters` | 300.0 m | Maximum permitted perpendicular divergence from route line. |
| `max_accuracy_meters` | 50.0 m | GPS fixes with accuracy $> 50$m are discarded as unreliable noise. |
| `min_consecutive_fixes` | 3 | Single outlier fixes are filtered; 3 consecutive fixes required to trigger alert. |
| Severity Threshold | 600.0 m | Deviation $> 2 \times$ threshold escalates event severity to `HIGH`. |

### 3.2 Unexpected Stop Evaluation
| Parameter | Default Value | Purpose |
|---|---|---|
| `stop_threshold_seconds` | 600 s (10 mins) | Sustained duration required before flagging stationary stop. |
| `max_displacement_meters` | 25.0 m | Maximum distance between any two fixes in the window. |
| `max_average_speed` | 0.8 m/s | Speed over ground indicating vehicle is stationary. |
| Destination Proximity Filter | 100.0 m | Stops within 100m of destination are treated as normal arrival. |
| Traffic Delay Discrimination | Displacement $> 30$m | Stop-and-go progression in heavy traffic is excluded from stops. |

---

## 4. Incident Lifecycle & State Transitions

```
                    +--------------------+
                    |  Anomaly Detected  |
                    +---------+----------+
                              |
                              v
                    +--------------------+
                    |       ACTIVE       |
                    +----+----------+----+
                         |          |
            (User taps   |          | (User taps "I'm OK /
          "Acknowledge") |          |  Expected" with notes)
                         v          v
+-----------------------------+   +-----------------------------+
|        ACKNOWLEDGED         |   |          RESOLVED           |
+--------------+--------------+   +-----------------------------+
               |                                 ^
               | (User later provides reason)    |
               +---------------------------------+
```

- **`ACTIVE`**: Incident currently active. Surfaces prominent warning card in Android UI and triggers notification.
- **`ACKNOWLEDGED`**: Traveler saw warning and acknowledged receipt; alarms silenced.
- **`RESOLVED`**: Traveler confirmed route change or stop was intentional (e.g. "Taking alternate route", "Stopping for fuel"); incident closed.
- **Duplicate Prevention:** If an incident of type `ROUTE_DEVIATION` or `UNEXPECTED_STOP` is already `ACTIVE`, subsequent deviated fixes update the existing incident rather than generating spam duplicate events.

---

## 5. Offline Sync & Idempotency

- **Local Persistence:** Android client records safety event state in Room database (`safety_events` table).
- **Optimistic UI:** When the traveler taps "Acknowledge" or "I'm OK", Room updates locally immediately, changing UI state in under 5 milliseconds.
- **`client_action_id`:** UUID generated on device guarantees that retrying network sync does not create duplicate resolution records.

---

## 6. Safety Governance Rules

1. **No Automatic Emergency Dispatch:** In Phase 6, route deviations and unexpected stops NEVER trigger automated 911 calls or SMS alerts to emergency contacts. Emergency dispatch is governed exclusively by Phase 7 SOS panic triggers and unconfirmed missed check-in escalations.
2. **Trip Preservation:** Detection never cancels or completes an active journey automatically.
3. **Traveler Autonomy:** Travelers maintain complete control to dismiss, acknowledge, or explain any route or stop anomaly.
