def fleetRow(performanceGivenUp, powerSaved):
        # Rounding only at render so derived claims (trade, breakeven) use full-precision intermediates.
        perfRetained = 100 - performanceGivenUp
        powerPerUnit = 100 - powerSaved
        units = 100 / perfRetained
        fleetPower = units * powerPerUnit
        return perfRetained, powerPerUnit, units, fleetPower

    @claim("5.6.3-unconstrained-row", PAPER, "5.6.3")
    def unconstrainedRow():
        perfRetained, powerPerUnit, units, fleetPower = fleetRow(
            SUMMARY["performance_given_up_pct"].mean(),
            SUMMARY["power_saved_pct"].mean(),
        )
        return (
            f"| unconstrained optimum (5.1) | {perfRetained:.1f}% | "
            f"{powerPerUnit:.1f}% | {units:.3f} | {fleetPower:.1f}% |"
        )

    @claim("5.6.3-floor-row", PAPER, "5.6.3")
    def floorRow():
        perfRetained, powerPerUnit, units, fleetPower = fleetRow(
            DATA["floorRow"]["loss_mean"],
            DATA["floorRow"]["power_saved_mean"],
        )
        return (
            f"| 95% floor (5.6) | {perfRetained:.1f}% | "
            f"{powerPerUnit:.1f}% | {units:.3f} | {fleetPower:.1f}% |"
        )

    @claim("5.6.3-unconstrained-trade", PAPER, "5.6.3")
    def unconstrainedTrade():
        # The bare numbers recur in the "buying" sentence; the word "trades" is what makes this match exactly once.
        _, _, units, fleetPower = fleetRow(
            SUMMARY["performance_given_up_pct"].mean(),
            SUMMARY["power_saved_pct"].mean(),
        )
        extraUnits = units * 100 - 100
        fleetSaving = 100 - fleetPower
        return f"trades {extraUnits:.1f}% more units for {fleetSaving:.1f}% less fleet power"

    @claim("5.6.3-floor-trade", PAPER, "5.6.3")
    def floorTrade():
        # Ends at "less" with no "fleet power" suffix, which is what separates this match from the unconstrained trade.
        _, _, units, fleetPower = fleetRow(
            DATA["floorRow"]["loss_mean"],
            DATA["floorRow"]["power_saved_mean"],
        )
        extraUnits = units * 100 - 100
        fleetSaving = 100 - fleetPower
        return f"trades {extraUnits:.1f}% more units for {fleetSaving:.1f}% less"

    @claim("5.6.3-unconstrained-breakeven", PAPER, "5.6.3")
    def unconstrainedBreakeven():
        # Catches a paper that quotes a breakeven fraction or ratio that does not follow from the fleet math.
        _, _, units, fleetPower = fleetRow(
            SUMMARY["performance_given_up_pct"].mean(),
            SUMMARY["power_saved_pct"].mean(),
        )
        extraUnits = units * 100 - 100
        fleetSaving = 100 - fleetPower
        a = extraUnits / 100
        b = fleetSaving / 100
        pct = 100 * a / b
        return f"unconstrained {a:.3f} / {b:.3f} = lifetime energy must exceed {pct:.0f}% of unit price"

    @claim("5.6.3-floor-breakeven", PAPER, "5.6.3")
    def floorBreakeven():
        # Catches a paper that quotes a floor breakeven fraction or ratio that does not follow from the fleet math.
        _, _, units, fleetPower = fleetRow(
            DATA["floorRow"]["loss_mean"],
            DATA["floorRow"]["power_saved_mean"],
        )
        extraUnits = units * 100 - 100
        fleetSaving = 100 - fleetPower
        a = extraUnits / 100
        b = fleetSaving / 100
        pct = 100 * a / b
        return f"95% floor {a:.3f} / {b:.3f} = lifetime energy must exceed {pct:.0f}% of unit price"