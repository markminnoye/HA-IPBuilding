# Implementatieplan: Geoptimaliseerde Polling Strategie

Om de belasting op het netwerk en de IPBuilding controller te minimaliseren, implementeren we een **Dual-Coordinator Strategie**. In plaats van elk apparaat individueel te laten pollen of alles elke 30 seconden op te halen, splitsen we het verkeer in twee stromen.

## 1. De Strategie

We maken gebruik van twee onafhankelijke `DataUpdateCoordinator` instanties in Home Assistant. Elke coordinator is verantwoordelijk voor een specifieke set apparaat-types.

### A. Fast Coordinator (Hoge Prioriteit)
Deze pollt frequent omdat deze stati direct zichtbaar moeten zijn of snel veranderen.

*   **Interval**: 30 seconden
*   **API Call**: `GET /api/v1/comp/items?types=1,2,3,60,40,41,56,200`
*   **Apparaat Types**:
    *   Verlichting (Relais, Dimmers, LED, DMX)
    *   Sensoren waarvan de waarde snel boeit (Energie, Temperatuur, Detectors)
    *   Systeemstatus (Tijd, Regime)

### B. Slow Coordinator (Lage Prioriteit)
Deze pollt minder vaak, omdat deze apparaten zelden van status veranderen of "stateless" zijn (zoals knoppen die alleen events sturen, of scenes die je activeert maar niet echt een 'aan' status hebben).

*   **Interval**: 300 seconden (5 minuten)
*   **API Call**: `GET /api/v1/comp/items?types=50,100,101,70,80`
*   **Apparaat Types**:
    *   Bediening (Buttons)
    *   Scenes (Sferen)
    *   Toegang (Card readers, codesloten)
    *   Logica (Programma's)

## 2. Technische Implementatie

### Stap 1: API Client Aanpassing (Gereed)
De `get_devices` functie in `api.py` is aangepast zodat deze een lijst van types accepteert (bv. `[1, 2]`) en dit omzet naar een komma-gescheiden lijst voor de URL parameter (`?types=1,2`). Dit zorgt voor Server-Side Filtering, wat veel efficiënter is.

### Stap 2: Coordinators Opzetten (Gereed)
In `__init__.py` worden bij het opstarten twee coordinators aangemaakt:
*   `coordinator_fast`
*   `coordinator_slow`

Deze halen bij start direct hun data op en plannen daarna hun eigen updates in.

### Stap 3: Componenten Migreren
Elk platform (`light`, `switch`, etc.) krijgt bij het opstarten de juiste coordinator doorgegeven.
*   **Lights & Switches**: Gebruiken `coordinator_fast`. (Migratie Gereed)
*   **Buttons & Scenes**: Gebruiken `coordinator_slow`. (Migratie Gereed)
*   **Sensors**: Moeten nog gemigreerd worden. Power sensors gaan naar `fast`, statische info kan eventueel naar `slow`.

## 3. Voordelen

1.  **Minder Netwerkverkeer**: We halen geen onnodige data op van knoppen of sferen elke 30 seconden.
2.  **Responsiviteit**: Het pollen van verlichting blijft snel (of kan zelfs sneller als dat nodig is) zonder de overhead van honderden andere componenten.
3.  **Schaalbaarheid**: Als je systeem groeit, blijft de performance goed omdat we gericht pollen.

## Volgende Stappen

1.  Ik zal nu `sensor.py` ombouwen om ook gebruik te maken van de coordinators.
2.  Daarna testen we of alle apparaten correct blijven updaten.
