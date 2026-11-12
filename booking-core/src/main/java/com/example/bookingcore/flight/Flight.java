package com.example.bookingcore.flight;

import java.time.LocalDateTime;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.Table;

@Entity
@Table(name = "flights",
        indexes = @Index(name = "idx_flight_route_dep", columnList = "origin,destination,departure"))
public class Flight {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String flightId;   // stored as flight_id, e.g. 6E202-DEL-BOM-2026-11-10

    private String flightNo;
    private String airline;
    private String origin;
    private String destination;
    private LocalDateTime departure;
    private LocalDateTime arrival;
    private String fareType;
    private int priceInr;
    private int seatsLeft;

    protected Flight() {} // JPA needs an empty constructor

    public Flight(String flightId, String flightNo, String airline, String origin,
                  String destination, LocalDateTime departure, LocalDateTime arrival,
                  String fareType, int priceInr, int seatsLeft) {
        this.flightId = flightId;
        this.flightNo = flightNo;
        this.airline = airline;
        this.origin = origin;
        this.destination = destination;
        this.departure = departure;
        this.arrival = arrival;
        this.fareType = fareType;
        this.priceInr = priceInr;
        this.seatsLeft = seatsLeft;
    }

    public Long getId() { return id; }
    public String getFlightId() { return flightId; }
    public String getFlightNo() { return flightNo; }
    public String getAirline() { return airline; }
    public String getOrigin() { return origin; }
    public String getDestination() { return destination; }
    public LocalDateTime getDeparture() { return departure; }
    public LocalDateTime getArrival() { return arrival; }
    public String getFareType() { return fareType; }
    public int getPriceInr() { return priceInr; }
    public int getSeatsLeft() { return seatsLeft; }
}