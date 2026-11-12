package com.example.bookingcore.booking;

import java.time.LocalDateTime;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "bookings")
public class Booking {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true)
    private String pnr;

    private String status;
    private String passenger;
    private String flightNo;
    private String origin;
    private String destination;
    private LocalDateTime departure;
    private String fareType;
    private int totalPaidInr;

    protected Booking() {}

    public Booking(String pnr, String status, String passenger, String flightNo, String origin,
                   String destination, LocalDateTime departure, String fareType, int totalPaidInr) {
        this.pnr = pnr;
        this.status = status;
        this.passenger = passenger;
        this.flightNo = flightNo;
        this.origin = origin;
        this.destination = destination;
        this.departure = departure;
        this.fareType = fareType;
        this.totalPaidInr = totalPaidInr;
    }

    public Long getId() { return id; }
    public String getPnr() { return pnr; }
    public String getStatus() { return status; }
    public String getPassenger() { return passenger; }
    public String getFlightNo() { return flightNo; }
    public String getOrigin() { return origin; }
    public String getDestination() { return destination; }
    public LocalDateTime getDeparture() { return departure; }
    public String getFareType() { return fareType; }
    public int getTotalPaidInr() { return totalPaidInr; }
}