package com.example.bookingcore.common;

import java.util.Map;

public final class Airports {
    private Airports() {}

    public static final Map<String, String> CODES = Map.of(
        "DEL", "Delhi",
        "BOM", "Mumbai",
        "BLR", "Bengaluru",
        "HYD", "Hyderabad",
        "MAA", "Chennai",
        "CCU", "Kolkata"
    );
}