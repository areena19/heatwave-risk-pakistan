import numpy as np


def heat_index_c(temp_c, rh):
    """NWS Rothfusz heat index. Input: temp in C, RH in %. Output: C."""
    t = temp_c * 9 / 5 + 32  # to Fahrenheit

    simple = 0.5 * (t + 61.0 + (t - 68.0) * 1.2 + rh * 0.094)

    full = (
        -42.379
        + 2.04901523 * t
        + 10.14333127 * rh
        - 0.22475541 * t * rh
        - 0.00683783 * t * t
        - 0.05481717 * rh * rh
        + 0.00122874 * t * t * rh
        + 0.00085282 * t * rh * rh
        - 0.00000199 * t * t * rh * rh
    )

    # NWS adjustments
    full = np.where(
        (rh < 13) & (t >= 80) & (t <= 112),
        full - ((13 - rh) / 4) * np.sqrt(np.clip((17 - np.abs(t - 95)) / 17, 0, None)),
        full,
    )
    full = np.where(
        (rh > 85) & (t >= 80) & (t <= 87),
        full + ((rh - 85) / 10) * ((87 - t) / 5),
        full,
    )

    # NWS rule: use the simple formula if its average with T is below 80F
    hi_f = np.where(simple < 80, simple, full)
    return (hi_f - 32) * 5 / 9


if __name__ == "__main__":
    # quick sanity check: 35C at 60% humidity should be about 45C
    print(heat_index_c(np.array([35.0, 40.0, 30.0]), np.array([60, 40, 30])))