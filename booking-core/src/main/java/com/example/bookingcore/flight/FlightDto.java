package com.example.bookingcore.flight;

import java.time.LocalDateTime;

import com.fasterxml.jackson.annotation.JsonProperty;

public record FlightDto(
        @JsonProperty("flight_id") String flightId,
        @JsonProperty("flight_no") String flightNo,
        String airline,
        String origin,
        String destination,
        LocalDateTime departure,
        LocalDateTime arrival,
        @JsonProperty("fare_type") String fareType,
        @JsonProperty("price_inr") int priceInr,
        @JsonProperty("seats_left") int seatsLeft) {

    public static FlightDto from(Flight f) {
        return new FlightDto(f.getFlightId(), f.getFlightNo(), f.getAirline(), f.getOrigin(),
                f.getDestination(), f.getDeparture(), f.getArrival(), f.getFareType(),
                f.getPriceInr(), f.getSeatsLeft());
    }
}