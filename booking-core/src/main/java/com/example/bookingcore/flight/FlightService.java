package com.example.bookingcore.flight;

import java.time.LocalDate;
import java.util.List;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.example.bookingcore.common.Airports;
import com.example.bookingcore.common.BadRequestException;
import com.example.bookingcore.common.NotFoundException;

@Service
public class FlightService {

    private final FlightRepository flights;

    public FlightService(FlightRepository flights) {
        this.flights = flights;
    }

    @Transactional(readOnly = true)
    public List<FlightDto> search(String origin, String destination, LocalDate date) {
        String from = origin.toUpperCase();
        String to = destination.toUpperCase();

        if (!Airports.CODES.containsKey(from) || !Airports.CODES.containsKey(to)) {
            throw new NotFoundException("Unknown airport code");
        }
        if (from.equals(to)) {
            throw new BadRequestException("Origin and destination must differ");
        }
        if (date.isBefore(LocalDate.now())) {
            throw new BadRequestException("Date is in the past");
        }

        return flights.search(from, to, date.atStartOfDay(), date.plusDays(1).atStartOfDay())
                .stream()
                .map(FlightDto::from)
                .toList();
    }
}