# Thermodynamics: Laws and Heat Engines (Lecture 4 notes)

## 1. Systems and temperature
A **system** is the part of the universe we study; everything else is the **surroundings**. An *isolated* system exchanges neither energy nor matter, a *closed* system exchanges energy only, an *open* system exchanges both.

### 1.1 Zeroth law
If A is in thermal equilibrium with C, and B is in thermal equilibrium with C, then A and B are in thermal equilibrium with each other. This transitivity is what makes **temperature** a well-defined property and justifies thermometers.

## 2. First law: energy conservation
The internal energy change of a closed system is heat added minus work done by the system:

ΔU = Q − W

Sign convention: Q > 0 when heat flows in; W > 0 when the system does work on the surroundings.

**Example 2.1.** A gas absorbs 500 J of heat and does 200 J of work on a piston. ΔU = 500 − 200 = 300 J, so its internal energy rises by 300 J.

### 2.2 Cyclic processes
Over one complete cycle the system returns to its initial state, so ΔU = 0 and therefore Q_net = W_net.

## 3. Heat engines
A heat engine takes heat Q_H from a hot reservoir at T_H, converts part of it into work W, and rejects heat Q_C to a cold reservoir at T_C. By the first law over a cycle, W = Q_H − Q_C.

**Thermal efficiency:** η = W / Q_H = 1 − Q_C / Q_H.

No real engine converts all the heat to work. Why not? That is the second law.

## 4. Second law
Two equivalent statements:
- **Kelvin-Planck:** no cyclic device can take heat from a single reservoir and convert all of it into work.
- **Clausius:** heat cannot flow spontaneously from a colder body to a hotter body.

### 4.1 Entropy
For heat Q transferred reversibly at constant temperature T, the entropy change is ΔS = Q / T (units J/K). For an isolated system, ΔS ≥ 0: entropy never decreases. ΔS = 0 only for reversible processes; real (irreversible) processes have ΔS > 0.

**Example 4.1.** 600 J of heat flows reversibly into a reservoir at 300 K: ΔS = 600 / 300 = 2 J/K.

## 5. The Carnot engine
The Carnot cycle consists of four reversible steps: isothermal expansion at T_H, adiabatic expansion, isothermal compression at T_C, adiabatic compression. It is the most efficient engine possible between two given temperatures. Temperatures must be in kelvin.

**Carnot efficiency:** η_Carnot = 1 − T_C / T_H.

**Example 5.1.** An engine operates between 500 K and 300 K and takes in Q_H = 800 J per cycle. η_max = 1 − 300/500 = 0.40 = 40%. Maximum work W = 0.40 × 800 = 320 J; heat rejected Q_C = 800 − 320 = 480 J.

### 5.2 Consequences
- Raising T_H or lowering T_C raises the maximum efficiency.
- η_Carnot = 100% would need T_C = 0 K, which is unattainable.
- No real engine can beat a Carnot engine working between the same reservoirs (Carnot's theorem).
