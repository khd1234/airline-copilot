package com.example.bookingcore.seed;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Random;

import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

import com.example.bookingcore.booking.Booking;
import com.example.bookingcore.booking.BookingRepository;
import com.example.bookingcore.common.Airports;
import com.example.bookingcore.farerule.FareRule;
import com.example.bookingcore.farerule.FareRuleRepository;
import com.example.bookingcore.flight.Flight;
import com.example.bookingcore.flight.FlightRepository;

/** Runs once at startup and fills the database with demo data (safe to re-run). */
@Component
public class DataSeeder implements CommandLineRunner {

    private static final int DAYS_AHEAD = 30;

    private record Slot(String airline, String number, int hour, int minute) {}

    private static final List<Slot> SLOTS = List.of(
            new Slot("Air India", "AI101", 6, 15),
            new Slot("IndiGo", "6E202", 9, 40),
            new Slot("Vistara", "UK303", 14, 5),
            new Slot("IndiGo", "6E404", 19, 30));

    private final FlightRepository flights;
    private final BookingRepository bookings;
    private final FareRuleRepository fareRules;

    public DataSeeder(FlightRepository flights, BookingRepository bookings,
                      FareRuleRepository fareRules) {
        this.flights = flights;
        this.bookings = bookings;
        this.fareRules = fareRules;
    }

    @Override
    public void run(String... args) {
        seedFareRules();
        seedBookings();
        seedFlights();
    }

    private void seedFareRules() {
        if (fareRules.count() > 0) return;
        fareRules.saveAll(List.of(
                new FareRule("SAVER",
                        "Allowed up to 24h before departure. Fee INR 3000 plus any fare difference.",
                        "Refund minus INR 3500 fee. No refund within 4h of departure.",
                        "15 kg check-in, 7 kg cabin."),
                new FareRule("FLEX",
                        "Free changes up to 2h before departure. Fare difference applies.",
                        "Refund minus INR 1000 fee. No refund within 2h of departure.",
                        "25 kg check-in, 7 kg cabin.")));
    }

    private void seedBookings() {
        if (bookings.count() > 0) return;
        bookings.saveAll(List.of(
                new Booking("ABC123", "CONFIRMED", "Ravi Kumar", "6E202", "DEL", "BOM",
                        LocalDateTime.of(2026, 11, 20, 9, 40), "SAVER", 5200),
                new Booking("XYZ789", "CANCELLED", "Anita Rao", "AI101", "BLR", "DEL",
                        LocalDateTime.of(2026, 11, 18, 6, 15), "FLEX", 8900)));
    }

    private void seedFlights() {
        LocalDate today = LocalDate.now();
        for (int i = 0; i < DAYS_AHEAD; i++) {
            LocalDate day = today.plusDays(i);
            // Skip days that already have flights, so restarting tops up new days only.
            if (flights.existsByDepartureBetween(day.atStartOfDay(), day.plusDays(1).atStartOfDay())) {
                continue;
            }
            List<Flight> batch = new ArrayList<>();
            for (String origin : Airports.CODES.keySet()) {
                for (String destination : Airports.CODES.keySet()) {
                    if (origin.equals(destination)) continue;
                    for (Slot s : SLOTS) {
                        Random rnd = new Random(Objects.hash(origin, destination, day.toString(), s.number()));
                        LocalDateTime departure = day.atTime(s.hour(), s.minute());
                        LocalDateTime arrival = departure.plusMinutes(110 + rnd.nextInt(70));
                        batch.add(new Flight(
                                s.number() + "-" + origin + "-" + destination + "-" + day,
                                s.number(), s.airline(), origin, destination, departure, arrival,
                                rnd.nextBoolean() ? "SAVER" : "FLEX",
                                3000 + rnd.nextInt(5000), 1 + rnd.nextInt(9)));
                    }
                }
            }
            flights.saveAll(batch);
        }
    }
}