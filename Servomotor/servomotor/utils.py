import pigpio

def frequency_to_period(frequency: float) -> int:
    return int(round(1_000_000.0 / frequency))

def add_pulse_pair(pulses, gpio_mask, high_time_us, low_time_us):
    """
    Append one HIGH and one LOW pulse to the list 'pulses'.
    Each pulse is a pigpio.pulse object that stores:
        - GPIO bits that become HIGH
        - GPIO bits that become LOW
        - duration in microseconds
    """
    pulses.append(pigpio.pulse(gpio_mask, 0, high_time_us))  # HIGH
    pulses.append(pigpio.pulse(0, gpio_mask, low_time_us))  # LOW

def create_ramp_waveform(
        pi: pigpio.pi,
        accel_steps: int,
        decel_steps: int,
        total_steps: int,
        target_freq: int,
        start_freq: int,
        pin_step: int,
        duty: float) -> int:
    if accel_steps + decel_steps > total_steps:
        raise ValueError("accel_steps + decel_steps must be ≤ total_steps")

    freq_table = []

    # Ramp up
    if accel_steps > 0:
        delta_f = (target_freq - start_freq) / accel_steps
        for i in range(accel_steps):
            freq_table.append(start_freq + i * delta_f)

    # Constant speed
    const_steps = total_steps - accel_steps - decel_steps
    freq_table.extend([target_freq] * const_steps)

    # Ramp down
    if decel_steps > 0:
        delta_f = (target_freq - start_freq) / decel_steps
        for i in range(decel_steps):
            freq_table.append(target_freq - (i + 1) * delta_f)

    # Build pulses
    pulses = []
    gpio_mask = 1 << pin_step

    for freq in freq_table:
        period = frequency_to_period(freq)
        # Convert the duty cycle (%) to actual microseconds of ON time
        high_time = int(round(period * duty / 100.0))
        low_time = period - high_time

        # Safety: pigpio needs each pulse ≥ 1µs
        if high_time < 1 or low_time < 1:
            raise ValueError(f"Frequency {freq}Hz with duty {duty}% " f"produces sub‑microsecond pulse. Reduce freq or adjust duty")
        add_pulse_pair(pulses, gpio_mask, high_time, low_time)

    # Build wave
    #pi.wave_clear()                # free all old waveforms to avoid memory leak
    pi.wave_add_generic(pulses)     # add new waveform
    wave_id = pi.wave_create()      # create the wave and get the ID

    if wave_id < 0:
        raise RuntimeError("Failed to create wave – too many pulses or out of DMA memory")
    return wave_id