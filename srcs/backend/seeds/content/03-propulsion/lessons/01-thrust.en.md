Every aircraft or rocket engine relies on **Newton's third law**: to move forward, you throw matter backwards. The force the engine exerts on that matter to accelerate it, the matter exerts back on the engine: that is **thrust**.

## Thrust comes from a flow of momentum

An engine that ejects a mass $\dot m$ each second (the **mass flow rate**, in kg/s) at speed $v_e$ relative to itself receives a thrust:

$$
F = \dot m\,v_e
$$

**Example.** A rocket engine ejecting 250 kg of gas per second at 3,000 m/s pushes with $250 \times 3{,}000 = 750{,}000$ N, i.e. 750 kN.

The same thrust can come from ejecting **a little mass very fast** or **a lot of mass slowly**. That choice lies at the heart of engine design.

## The rocket case

A rocket needs nothing outside itself to push on: it pushes on its own gases. So it works **in a vacuum too**, even better, since the atmosphere no longer hinders the flow leaving the nozzle. Its full equation adds a pressure term:

$$
F = \dot m\,v_e + (p_e - p_a)\,A_e
$$

- $p_e$: gas pressure at the nozzle exit
- $p_a$: ambient pressure
- $A_e$: nozzle exit area

At sea level, $p_a$ is about 1 bar and this term reduces thrust. In a vacuum, $p_a = 0$ and it adds to it. The same engine therefore **pushes harder in a vacuum than at sea level**.

## The jet engine case

A jet engine takes in the air ahead of it (arriving at the flight speed $v_0$) and throws it out faster. Only the **difference in speed** produces thrust:

$$
F \approx \dot m_{air}\,(v_e - v_0)
$$

The small mass of fuel added is neglected here.

## Lifting off: thrust-to-weight ratio

A rocket leaving vertically must push harder than its weight: its thrust-to-weight ratio at lift-off must exceed 1, typically 1.2 to 1.5. An aircraft does not need thrust equal to its weight: the wing provides lift, and the engine only has to overcome drag, ten to twenty times smaller.
