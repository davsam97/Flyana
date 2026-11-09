## Real time: right, and on time

A **real-time** system must not only compute the right answer: it must deliver it **before a deadline**. A control law that computes the correct surface command 200 ms late can make the aircraft oscillate. We distinguish:

- **hard real time**: missing a deadline is a failure, as for flight controls;
- **soft real time**: a delay degrades service without danger, as for an entertainment screen.

The point is not to go "as fast as possible" but to be **deterministic**: know the **worst-case execution time** (WCET) of every task and prove that all of them meet their deadlines. Classic schedulers follow the **rate monotonic** rule: the task with the shortest period gets the highest priority. A **watchdog** restarts the computer if the software stops responding.

Integrated modular avionics (IMA) runs several functions on the same computer. The **ARINC 653** standard isolates them in **partitions**, each with its own memory and time slots, so that a faulty function cannot disturb the others.

## Surviving failures: redundancy

- **Active redundancy with voting**: three identical computers work in parallel and a voter keeps the majority value. One failure is masked ("two out of three").
- **Dissimilar redundancy**: the same design error, in software above all, will hit every identical copy at once (a **common-mode** failure). Airbus flight controls therefore use computers of different designs, programmed by different teams.

## A textbook case: Ariane 501

On 4 June 1996, the first flight of Ariane 5 ended with the destruction of the launcher about 40 seconds after lift-off. The inquiry board established the cause:

1. The inertial reference system (SRI) software, **reused from Ariane 4**, converted a 64-bit floating-point value (the horizontal bias) into a 16-bit signed integer. On Ariane 5's faster trajectory the value **overflowed** the integer, raising an unhandled exception.
2. The backup unit, **identical**, had hit the same error a moment earlier.
3. The on-board computer read the diagnostic message as flight data and commanded an extreme nozzle deflection.

The lessons: redundancy does not protect against a common software error, and reused software must be revalidated in its **new** context.

## Certifying software: DO-178C

To be certified, software on board an aircraft must follow **DO-178C** (Software Considerations in Airborne Systems and Equipment Certification), published in 2011 by RTCA, and in Europe by EUROCAE as ED-12C. It ranks each piece of software by the consequences of its failure, its **Design Assurance Level** (DAL):

| Level | Failure consequence | Example test requirement |
|---|---|---|
| A | catastrophic (loss of the aircraft) | **MC/DC** coverage |
| B | hazardous | decision coverage |
| C | major | statement coverage |
| D | minor | — |
| E | no safety effect | no objectives |

**MC/DC** (Modified Condition/Decision Coverage) requires tests to show that each condition in a decision independently affects its outcome. DO-178C also demands traceability between requirements, code and tests, and independent reviews. Complex electronic hardware follows a sister standard, DO-254.
