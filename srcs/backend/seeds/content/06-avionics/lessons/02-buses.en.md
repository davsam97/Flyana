## Why buses?

An airliner holds hundreds of units exchanging thousands of data items. Wiring each pair together would take extra kilometres of cable, so hundreds of kilos. Instead they talk over shared **data buses**, standardised so that units from different suppliers understand each other. Each bus strikes a different balance between simplicity, bandwidth and determinism.

## ARINC 429: simple and one-way

The historical standard of civil aviation (1970s, still everywhere):

- **one-way**: on a twisted pair, **a single transmitter** talks and up to 20 receivers listen. Replying takes a second bus;
- **32-bit words**, including an 8-bit **label** that tells what the data is (altitude, heading…);
- two speeds: 12.5 kbit/s or **100 kbit/s**. At 100 kbit/s, one word lasts $32 / 100{,}000 = 0.32$ ms.

Very robust and easy to certify, but it needs a lot of cable.

## MIL-STD-1553: command and response

Born in US military aviation (1973, revision B in 1978), also used on satellites and the ISS:

- **1 Mbit/s** on a shared bus, **duplicated** for redundancy;
- a single **bus controller** decides who talks: it sends a command, the targeted **remote terminal** answers. Up to 31 terminals;
- no collision can happen, so behaviour is **deterministic**: you know exactly when each message goes through.

## CAN: multi-master and priorities

Invented by Bosch for cars (1980s), the **CAN** bus (Controller Area Network) has spread to drones, small satellites and, with the ARINC 825 profile, some aircraft:

- **multi-master**: any node may transmit when the bus is free;
- each message carries an **identifier** that sets its priority. If two nodes transmit at once, a bit-by-bit **arbitration** lets the lowest identifier win, without destroying its message: the other node falls silent and retries;
- up to 1 Mbit/s in classic CAN, more with CAN FD.

## AFDX: deterministic Ethernet

Recent aircraft (A380, A350) use **AFDX** (ARINC 664 part 7): switched Ethernet, duplicated, where each flow travels on a **virtual link** with guaranteed bandwidth. It brings Ethernet's data rates with the predictability aviation demands.

| Bus | Rate | Topology | Access |
|---|---|---|---|
| ARINC 429 | 12.5 or 100 kbit/s | one transmitter, ≤ 20 receivers | one-way |
| MIL-STD-1553 | 1 Mbit/s | shared bus, duplicated | command/response |
| CAN | ≤ 1 Mbit/s (classic) | shared bus | multi-master, arbitration |
| AFDX | 10/100 Mbit/s | switched Ethernet, duplicated | virtual links |
