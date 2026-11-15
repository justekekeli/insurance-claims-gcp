
SELECT
    region,
    COUNT(*) AS total_claims,
    ROUND(SUM(claim_amount),2) AS total_claim_amount,
    ROUND(AVG(claim_amount),2) AS average_claim_amount,
    ROUND(SUM(reimbursement_amount),2) AS total_reimbursement_amount,
    ROUND(SAFE_DIVIDE(SUM(reimbursement_amount),SUM(claim_amount)) * 100,2) AS reimbursement_rate_pct
FROM `PROJECT_ID.analytics_dt.claims_clean`
GROUP BY region
ORDER BY total_claim_amount DESC;
