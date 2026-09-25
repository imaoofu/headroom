# Checks on the live card that a registered design depends on.
#
# WHY. Collect.ps1 builds its suite grid from the card's supported-clock table: 40% of the table's
# top entry, up to that top entry, in 13 points. On 2026-09-25 the 3070 Ti's table had 116 entries
# and topped out at 2130 MHz, against 115 entries and 2115 the day before. Session D2's top six
# targets moved by 15 MHz, and its registered prediction (8d), which named Session D's grid, became
# NOT SCOREABLE after three hours of collection. A catalog can now state the table top its grid
# needs, and the engine refuses at the start instead.

# Returns $null when the table top matches, or a sentence saying why the session must not start.
function Get-SuiteTopProblem([int]$tableTopMhz, $card) {
    if ($null -eq $card.suiteTopClockMhz) { return $null }
    $expected = [int]$card.suiteTopClockMhz
    if ($tableTopMhz -eq $expected) { return $null }
    return ("The card's supported-clock table tops out at {0} MHz, not the {1} MHz this run list's " +
            "registered suite grid is built from. The suites would sweep a different grid and the " +
            "registered prediction could not be scored. Nothing was run.") -f $tableTopMhz, $expected
}
