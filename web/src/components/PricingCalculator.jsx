import React, { useState, useMemo } from 'react';
import './PricingCalculator.css';

const PricingCalculator = () => {
    const [services, setServices] = useState(10);
    const [incidents, setIncidents] = useState(50);
    const [teamSize, setTeamSize] = useState(3);
    const [selectedPlan, setSelectedPlan] = useState('pro');

    const plans = {
        free: {
            name: 'Free',
            price: 0,
            limits: {
                services: 3,
                incidents: 10,
                team: 1
            },
            features: [
                'HTTP health monitoring',
                'Basic anomaly detection',
                '1 AI postmortem/day',
                'Slack alerts',
                '7-day data retention'
            ]
        },
        pro: {
            name: 'Pro',
            price: 19,
            limits: {
                services: 100,
                incidents: -1, // unlimited
                team: 10
            },
            features: [
                'Everything in Free +',
                'Unlimited incidents',
                'Unlimited AI postmortems',
                'Incident Memory',
                'Deployment correlation',
                'On-call scheduling',
                'Custom health checks',
                'CLI tool',
                '1-year data retention'
            ]
        },
        enterprise: {
            name: 'Enterprise',
            price: -1, // custom
            limits: {
                services: -1,
                incidents: -1,
                team: -1
            },
            features: [
                'Everything in Pro +',
                'Unlimited everything',
                'SSO/SAML',
                'Dedicated support',
                'Custom integrations',
                'SLA guarantees',
                'On-premise option'
            ]
        }
    };

    const recommendation = useMemo(() => {
        // Free tier limits
        if (services <= 3 && incidents <= 10 && teamSize <= 1) {
            return 'free';
        }

        // Pro tier limits
        if (services <= 100 && teamSize <= 10) {
            return 'pro';
        }

        // Need enterprise
        return 'enterprise';
    }, [services, incidents, teamSize]);

    const monthlyCost = useMemo(() => {
        const plan = plans[selectedPlan];
        if (plan.price === -1) return 'Custom';
        if (plan.price === 0) return '$0';

        // Pro is flat rate
        return `$${plan.price}`;
    }, [selectedPlan]);

    const yearlyCost = useMemo(() => {
        const plan = plans[selectedPlan];
        if (plan.price === -1) return 'Custom';
        if (plan.price === 0) return '$0';

        // 2 months free on yearly
        const yearly = plan.price * 10;
        return `$${yearly}`;
    }, [selectedPlan]);

    const competitorCost = useMemo(() => {
        // Rough competitor pricing calculation
        // PagerDuty: ~$25/user/month
        // Datadog: ~$15/host/month + $0.10/GB logs

        const pagerDuty = teamSize * 25;
        const datadog = services * 15;

        return {
            pagerDuty: pagerDuty,
            datadog: datadog,
            combined: pagerDuty + datadog
        };
    }, [services, teamSize]);

    const savings = useMemo(() => {
        if (selectedPlan === 'free') return competitorCost.combined;
        if (selectedPlan === 'pro') return Math.max(0, competitorCost.combined - 19);
        return null; // Enterprise needs custom quote
    }, [selectedPlan, competitorCost]);

    return (
        <div className="pricing-calculator">
            <div className="calculator-header">
                <h2>Pricing Calculator</h2>
                <p>See how much you could save with DevOps Sentinel</p>
            </div>

            <div className="calculator-body">
                <div className="calculator-inputs">
                    <div className="input-section">
                        <label>
                            <span className="label-text">Services to monitor</span>
                            <span className="label-value">{services}</span>
                        </label>
                        <input
                            type="range"
                            min="1"
                            max="200"
                            value={services}
                            onChange={(e) => setServices(parseInt(e.target.value))}
                        />
                        <div className="range-labels">
                            <span>1</span>
                            <span>200+</span>
                        </div>
                    </div>

                    <div className="input-section">
                        <label>
                            <span className="label-text">Expected incidents/month</span>
                            <span className="label-value">{incidents}</span>
                        </label>
                        <input
                            type="range"
                            min="1"
                            max="200"
                            value={incidents}
                            onChange={(e) => setIncidents(parseInt(e.target.value))}
                        />
                        <div className="range-labels">
                            <span>1</span>
                            <span>200+</span>
                        </div>
                    </div>

                    <div className="input-section">
                        <label>
                            <span className="label-text">On-call team size</span>
                            <span className="label-value">{teamSize}</span>
                        </label>
                        <input
                            type="range"
                            min="1"
                            max="20"
                            value={teamSize}
                            onChange={(e) => setTeamSize(parseInt(e.target.value))}
                        />
                        <div className="range-labels">
                            <span>1</span>
                            <span>20+</span>
                        </div>
                    </div>
                </div>

                <div className="plan-recommendation">
                    <div className="recommendation-badge">
                        Recommended for you
                    </div>
                    <h3>{plans[recommendation].name}</h3>

                    <div className="price-display">
                        <span className="price">
                            {plans[recommendation].price === -1 ? 'Custom' : `$${plans[recommendation].price}`}
                        </span>
                        {plans[recommendation].price > 0 && (
                            <span className="period">/month</span>
                        )}
                    </div>

                    <ul className="feature-list">
                        {plans[recommendation].features.slice(0, 5).map((feature, i) => (
                            <li key={i}>{feature}</li>
                        ))}
                    </ul>

                    <button className="cta-button">
                        {recommendation === 'free' ? 'Start Free' :
                            recommendation === 'pro' ? 'Start 14-day Trial' :
                                'Contact Sales'}
                    </button>
                </div>
            </div>

            <div className="comparison-section">
                <h3>Compare to Competitors</h3>

                <div className="comparison-table">
                    <div className="comparison-row header">
                        <span>Tool</span>
                        <span>Estimated Monthly Cost</span>
                    </div>

                    <div className="comparison-row competitor">
                        <span>PagerDuty</span>
                        <span className="cost">${competitorCost.pagerDuty}/mo</span>
                    </div>

                    <div className="comparison-row competitor">
                        <span>Datadog Infrastructure</span>
                        <span className="cost">${competitorCost.datadog}/mo</span>
                    </div>

                    <div className="comparison-row competitor total">
                        <span>Combined</span>
                        <span className="cost">${competitorCost.combined}/mo</span>
                    </div>

                    <div className="comparison-row sentinel">
                        <span>DevOps Sentinel</span>
                        <span className="cost">{monthlyCost}/mo</span>
                    </div>
                </div>

                {savings !== null && savings > 0 && (
                    <div className="savings-callout">
                        <span className="savings-amount">Save ${savings}/month</span>
                        <span className="savings-percent">
                            ({Math.round((savings / competitorCost.combined) * 100)}% less)
                        </span>
                    </div>
                )}
            </div>

            <div className="yearly-discount">
                <div className="discount-content">
                    <span className="discount-badge">SAVE 17%</span>
                    <span className="discount-text">
                        Pay yearly: {yearlyCost}/year (2 months free)
                    </span>
                </div>
            </div>
        </div>
    );
};

export default PricingCalculator;
