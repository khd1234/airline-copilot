package com.example.bookingcore.farerule;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class FareRuleController {

    private final FareRuleService service;

    public FareRuleController(FareRuleService service) {
        this.service = service;
    }

    @GetMapping("/fare-rules/{fareType}")
    public FareRuleDto get(@PathVariable String fareType) {
        return service.get(fareType);
    }
}