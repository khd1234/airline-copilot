package com.example.bookingcore.booking;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class BookingController {

    private final BookingService service;

    public BookingController(BookingService service) {
        this.service = service;
    }

    @GetMapping("/bookings/{pnr}")
    public BookingDto get(@PathVariable String pnr) {
        return service.getByPnr(pnr);
    }
}