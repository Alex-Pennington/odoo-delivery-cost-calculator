# -*- coding: utf-8 -*-
"""
Migration Script: Recalculate Partner Distances with Haversine Formula

This script updates all existing partner distance calculations from the old
inaccurate flat-Earth approximation to the new accurate Haversine formula.

Usage:
------
1. Via Odoo Shell:
   docker exec -it <odoo_container> odoo shell -d <database>
   Then paste this script

2. Via Python Script:
   Place in odoo/addons/delivery_cost_calculator/migrations/
   Odoo will run it automatically on module upgrade

3. Via Developer Console (if enabled):
   Copy and paste into Odoo's developer console

What it does:
-------------
- Finds all partners with existing distance calculations
- Recalculates distance using new Haversine formula
- Logs progress and any errors
- Updates x_partner_distance field
- Skips partners without valid GPS coordinates

"""

import logging
_logger = logging.getLogger(__name__)

def migrate_partner_distances(env):
    """
    Recalculate all partner distances using accurate Haversine formula.
    
    Args:
        env: Odoo environment object
    """
    Partner = env['res.partner']
    
    # Find all partners with existing distance calculations
    partners = Partner.search([('x_partner_distance', '>', 0)])
    
    total_count = len(partners)
    success_count = 0
    skip_count = 0
    error_count = 0
    
    _logger.info(f"Starting migration: {total_count} partners to recalculate")
    
    for i, partner in enumerate(partners, 1):
        try:
            # Check if partner has GPS coordinates
            if not partner.partner_latitude or not partner.partner_longitude:
                _logger.debug(
                    f"[{i}/{total_count}] Skipping {partner.name} (ID: {partner.id}): "
                    "No GPS coordinates"
                )
                skip_count += 1
                continue
            
            # Store old distance for comparison
            old_distance = partner.x_partner_distance
            
            # Recalculate using new Haversine formula
            new_distance = partner.calculate_distance_from_origin()
            
            # Calculate difference
            diff = abs(new_distance - old_distance)
            diff_pct = (diff / old_distance * 100) if old_distance > 0 else 0
            
            _logger.info(
                f"[{i}/{total_count}] Updated {partner.name} (ID: {partner.id}): "
                f"{old_distance:.2f} mi → {new_distance:.2f} mi "
                f"(Δ {diff:.2f} mi, {diff_pct:.1f}%)"
            )
            
            success_count += 1
            
            # Commit every 50 partners to avoid long transactions
            if i % 50 == 0:
                env.cr.commit()
                _logger.info(f"Progress: {i}/{total_count} processed, committed")
                
        except Exception as e:
            _logger.error(
                f"[{i}/{total_count}] Error recalculating {partner.name} (ID: {partner.id}): {str(e)}"
            )
            error_count += 1
            continue
    
    # Final commit
    env.cr.commit()
    
    # Summary
    _logger.info(
        f"Migration complete!\n"
        f"  Total: {total_count}\n"
        f"  Success: {success_count}\n"
        f"  Skipped: {skip_count}\n"
        f"  Errors: {error_count}"
    )
    
    return {
        'total': total_count,
        'success': success_count,
        'skipped': skip_count,
        'errors': error_count
    }


def clear_all_distances(env):
    """
    Clear all partner distances to force recalculation on next order.
    
    This is a simpler alternative to recalculating - distances will be
    recalculated automatically when customers place their next order.
    
    Args:
        env: Odoo environment object
    """
    Partner = env['res.partner']
    
    partners = Partner.search([('x_partner_distance', '>', 0)])
    count = len(partners)
    
    _logger.info(f"Clearing distances for {count} partners")
    
    partners.write({'x_partner_distance': 0.0})
    env.cr.commit()
    
    _logger.info(f"Successfully cleared {count} partner distances")
    
    return count


# ============================================================================
# Run Migration
# ============================================================================

if __name__ == '__main__':
    # If running directly in Odoo shell, 'env' is already available
    # Uncomment the method you want to use:
    
    # Option 1: Recalculate all distances immediately
    result = migrate_partner_distances(env)
    print(f"Migration complete: {result}")
    
    # Option 2: Just clear distances (will recalculate on next order)
    # count = clear_all_distances(env)
    # print(f"Cleared {count} partner distances")


# ============================================================================
# SQL Alternative (Direct Database Update)
# ============================================================================
"""
If you prefer to use SQL directly:

-- Clear all distances (simplest option)
UPDATE res_partner SET x_partner_distance = NULL WHERE x_partner_distance > 0;

-- Or clear to zero
UPDATE res_partner SET x_partner_distance = 0 WHERE x_partner_distance > 0;

-- Check how many will be affected
SELECT COUNT(*) FROM res_partner WHERE x_partner_distance > 0;

-- Backup before clearing (optional)
CREATE TABLE res_partner_distance_backup AS 
SELECT id, name, x_partner_distance 
FROM res_partner 
WHERE x_partner_distance > 0;
"""
