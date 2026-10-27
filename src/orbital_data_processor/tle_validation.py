"""Small, dependency-free checks before propagating a two-line element set."""


def validate_tle_lines(line1, line2):
    if not isinstance(line1, str) or not isinstance(line2, str):
        raise ValueError("TLE must contain two text lines.")
    for line, prefix in ((line1, "1 "), (line2, "2 ")):
        if len(line) != 69 or not line.startswith(prefix):
            raise ValueError("Invalid TLE line structure.")
        if not line[-1].isdigit():
            raise ValueError("Invalid TLE checksum digit.")
        checksum = sum(int(char) if char.isdigit() else char == "-"
                       for char in line[:-1]) % 10
        if checksum != int(line[-1]):
            raise ValueError("Invalid TLE checksum.")
    if line1[2:7] != line2[2:7]:
        raise ValueError("TLE lines refer to different NORAD IDs.")
    try:
        float(line2[8:16])
    except ValueError as error:
        raise ValueError("Invalid TLE inclination.") from error
    return line1, line2
