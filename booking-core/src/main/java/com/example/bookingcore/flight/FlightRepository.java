package com.example.bookingcore.flight;

import java.time.LocalDateTime;
import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface FlightRepository extends JpaRepository<Flight, Long> {
    @Query("""
            select f from Flight f
            where f.origin = :origin and f.destination = :destination
              and f.departure >= :from and f.departure < :to
            order by f.departure
            """)
    List<Flight> search(@Param("origin") String origin,
                        @Param("destination") String destination,
                        @Param("from") LocalDateTime from,
                        @Param("to") LocalDateTime to);

    boolean existsByDepartureBetween(LocalDateTime from, LocalDateTime to);
}