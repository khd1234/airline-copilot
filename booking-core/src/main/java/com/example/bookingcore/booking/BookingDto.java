package com.example.bookingcore.booking;

import java.time.LocalDateTime;

import com.fasterxml.jackson.annotation.JsonProperty;

public record BookingDto(
        String pnr,
        String status,
        String passenger,
        @JsonProperty("flight_no") String flightNo,
        String origin,
        String destination,
        LocalDateTime departure,
        @JsonProperty("fare_type") String fareType,
        @JsonProperty("total_paid_inr") int totalPaidInr) {

    public static BookingDto from(Booking b) {
        return new BookingDto(b.getPnr(), b.getStatus(), b.getPassenger(), b.getFlightNo(),
                b.getOrigin(), b.getDestination(), b.getDeparture(), b.getFareType(),
                b.getTotalPaidInr());
    }
}