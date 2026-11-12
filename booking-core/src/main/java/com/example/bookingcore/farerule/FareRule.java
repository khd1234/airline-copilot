package com.example.bookingcore.farerule;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "fare_rules")
public class FareRule {

    @Id
    private String fareType;   // SAVER or FLEX is the primary key

    private String changes;
    private String cancellation;
    private String baggage;

    protected FareRule() {}

    public FareRule(String fareType, String changes, String cancellation, String baggage) {
        this.fareType = fareType;
        this.changes = changes;
        this.cancellation = cancellation;
        this.baggage = baggage;
    }

    public String getFareType() { return fareType; }
    public String getChanges() { return changes; }
    public String getCancellation() { return cancellation; }
    public String getBaggage() { return baggage; }
}