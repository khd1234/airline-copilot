package com.example.bookingcore.farerule;

import com.fasterxml.jackson.annotation.JsonProperty;

public record FareRuleDto(
        @JsonProperty("fare_type") String fareType,
        String changes,
        String cancellation,
        String baggage) {

    public static FareRuleDto from(FareRule r) {
        return new FareRuleDto(r.getFareType(), r.getChanges(), r.getCancellation(), r.getBaggage());
    }
}