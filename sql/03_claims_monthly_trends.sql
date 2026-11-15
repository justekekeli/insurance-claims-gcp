WITH monthly_claims AS (
    SELECT
        DATE_TRUNC(claim_date, MONTH) AS claim_month,
        COUNT(*) AS total_claims,
        ROUND(SUM(claim_amount),2) AS total_claim_amount,
        ROUND(SUM(reimbursement_amount),2) AS total_reimbursement_amount,
        ROUND(AVG(claim_amount),2) AS average_claim_amount
    FROM `PROJECT_ID.analytics_dt.claims_clean`
    GROUP BY 1
),

monthly_trends AS (SELECT *,
                    LAG(total_claims) OVER (ORDER BY claim_month ) AS previous_month_claims
                    FROM monthly_claims)

SELECT
    claim_month,
    total_claims,
    total_claim_amount,
    total_reimbursement_amount,
    average_claim_amount,
    previous_month_claims,
    ROUND(SAFE_DIVIDE(total_claims - previous_month_claims,previous_month_claims) * 100,2) AS claims_growth_pct

FROM monthly_trends
ORDER BY claim_month;
