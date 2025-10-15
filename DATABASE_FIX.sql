-- Quick fix: Create x_partner_distance column if other modules reference it
-- Run this in your PostgreSQL database if you get "column does not exist" errors

-- Add the column to res_partner table
ALTER TABLE res_partner 
ADD COLUMN IF NOT EXISTS x_partner_distance NUMERIC(10,2) DEFAULT 0.0;

-- Add comment for documentation
COMMENT ON COLUMN res_partner.x_partner_distance IS 'Distance from origin (miles) - Legacy field for compatibility';

-- Optional: Set all existing values to 0
UPDATE res_partner SET x_partner_distance = 0.0 WHERE x_partner_distance IS NULL;
