package com.example.bookingcore.booking;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.example.bookingcore.common.NotFoundException;

@Service
public class BookingService {

    private final BookingRepository bookings;

    public BookingService(BookingRepository bookings) {
        this.bookings = bookings;
    }

    @Transactional(readOnly = true)
    public BookingDto getByPnr(String pnr) {
        return bookings.findByPnr(pnr.toUpperCase())
                .map(BookingDto::from)
                .orElseThrow(() -> new NotFoundException("Booking not found"));
    }
}