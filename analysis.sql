-- analysis.sql
-- SQL queries that explore default risk by borrower segment.
-- Run them all from Python with:  python run_sql_analysis.py
-- Or run them in MySQL with:      mysql -u root -p credit_risk_db < analysis.sql
 
-- Q1: Overall portfolio default rate
SELECT
    COUNT(*) AS total_loans,
    SUM(default_flag) AS total_defaults,
    ROUND(100.0 * AVG(default_flag), 2) AS default_rate_pct
FROM loans;
 
-- Q2: Default rate by credit score band
SELECT
    CASE
        WHEN credit_score < 580 THEN '1. Poor (under 580)'
        WHEN credit_score < 670 THEN '2. Fair (580-669)'
        WHEN credit_score < 740 THEN '3. Good (670-739)'
        WHEN credit_score < 800 THEN '4. Very Good (740-799)'
        ELSE '5. Exceptional (800+)'
    END AS credit_band,
    COUNT(*) AS loans,
    ROUND(100.0 * AVG(default_flag), 2) AS default_rate_pct
FROM loans
GROUP BY credit_band
ORDER BY credit_band;
 
-- Q3: Default rate by income bracket
SELECT
    CASE
        WHEN income < 40000 THEN '1. Under 40K'
        WHEN income < 70000 THEN '2. 40K-70K'
        WHEN income < 100000 THEN '3. 70K-100K'
        ELSE '4. 100K+'
    END AS income_bracket,
    COUNT(*) AS loans,
    ROUND(AVG(loan_amount), 0) AS avg_loan_amount,
    ROUND(100.0 * AVG(default_flag), 2) AS default_rate_pct
FROM loans
GROUP BY income_bracket
ORDER BY income_bracket;
 
-- Q4: Default rate by debt-to-income ratio
SELECT
    CASE
        WHEN dti_ratio < 0.2 THEN '1. Under 0.2'
        WHEN dti_ratio < 0.4 THEN '2. 0.2-0.4'
        WHEN dti_ratio < 0.6 THEN '3. 0.4-0.6'
        ELSE '4. 0.6+'
    END AS dti_bucket,
    COUNT(*) AS loans,
    ROUND(100.0 * AVG(default_flag), 2) AS default_rate_pct
FROM loans
GROUP BY dti_bucket
ORDER BY dti_bucket;
 
-- Q5: Loan purposes ranked from riskiest to safest (window function)
SELECT
    loan_purpose,
    COUNT(*) AS loans,
    ROUND(100.0 * AVG(default_flag), 2) AS default_rate_pct,
    RANK() OVER (ORDER BY AVG(default_flag) DESC) AS risk_rank
FROM loans
GROUP BY loan_purpose
ORDER BY risk_rank;
 
-- Q6: Default rate by employment type
SELECT
    employment_type,
    COUNT(*) AS loans,
    ROUND(AVG(months_employed), 1) AS avg_months_employed,
    ROUND(100.0 * AVG(default_flag), 2) AS default_rate_pct
FROM loans
GROUP BY employment_type
ORDER BY default_rate_pct DESC;
 
-- Q7: Does having a co-signer lower default risk
SELECT
    has_cosigner,
    COUNT(*) AS loans,
    ROUND(100.0 * AVG(default_flag), 2) AS default_rate_pct
FROM loans
GROUP BY has_cosigner;
 
-- Q8: Default rate by age group
SELECT
    CASE
        WHEN age < 25 THEN '1. 18-24'
        WHEN age < 35 THEN '2. 25-34'
        WHEN age < 45 THEN '3. 35-44'
        WHEN age < 55 THEN '4. 45-54'
        ELSE '5. 55+'
    END AS age_group,
    COUNT(*) AS loans,
    ROUND(100.0 * AVG(default_flag), 2) AS default_rate_pct
FROM loans
GROUP BY age_group
ORDER BY age_group;
 
-- Q9: Profile of defaulters vs non-defaulters
SELECT
    CASE WHEN default_flag = 1 THEN 'Defaulted' ELSE 'Repaid' END AS outcome,
    COUNT(*) AS loans,
    ROUND(AVG(income), 0) AS avg_income,
    ROUND(AVG(loan_amount), 0) AS avg_loan_amount,
    ROUND(AVG(credit_score), 0) AS avg_credit_score,
    ROUND(AVG(interest_rate), 2) AS avg_interest_rate,
    ROUND(AVG(dti_ratio), 3) AS avg_dti_ratio
FROM loans
GROUP BY default_flag;
 
-- Q10: How risky is a high-risk profile (poor credit and high DTI) compared with everyone else
WITH segments AS (
    SELECT
        default_flag,
        CASE
            WHEN credit_score < 580 AND dti_ratio > 0.5 THEN 'High-risk profile'
            ELSE 'All other borrowers'
        END AS segment
    FROM loans
)
SELECT
    segment,
    COUNT(*) AS loans,
    ROUND(100.0 * AVG(default_flag), 2) AS default_rate_pct
FROM segments
GROUP BY segment
ORDER BY default_rate_pct DESC;