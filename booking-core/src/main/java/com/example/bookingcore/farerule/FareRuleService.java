package com.example.bookingcore.farerule;

import com.example.bookingcore.common.NotFoundException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class FareRuleService {

    private final FareRuleRepository rules;

    public FareRuleService(FareRuleRepository rules) {
        this.rules = rules;
    }

    @Transactional(readOnly = true)
    public FareRuleDto get(String fareType) {
        return rules.findById(fareType.toUpperCase())
                .map(FareRuleDto::from)
                .orElseThrow(() -> new NotFoundException("Unknown fare type. Known: SAVER, FLEX"));
    }
}