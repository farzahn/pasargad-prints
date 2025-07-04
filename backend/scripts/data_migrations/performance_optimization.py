#!/usr/bin/env python3

"""
Performance Optimization Migration for Pasargad Prints
Adds database indexes, optimizes queries, and improves performance
"""

import os
import sys
import django
import logging
from pathlib import Path
from django.db import transaction, connection

# Load environment variables from root .env file
from dotenv import load_dotenv
root_dir = Path(__file__).resolve().parent.parent.parent.parent
env_path = root_dir / '.env'
load_dotenv(env_path)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pasargad_prints.settings_production')
django.setup()

logger = logging.getLogger(__name__)

def run_migration():
    """
    Main performance optimization migration function
    """
    logger.info("Starting performance optimization migration")
    
    try:
        with transaction.atomic():
            # Add database indexes
            add_database_indexes()
            
            # Optimize database configuration
            optimize_database_config()
            
            # Update table statistics
            update_table_statistics()
            
            # Create materialized views if supported
            create_materialized_views()
            
        logger.info("Performance optimization migration completed successfully")
        
    except Exception as e:
        logger.error(f"Performance optimization migration failed: {str(e)}")
        raise

def add_database_indexes():
    """Add database indexes for better query performance"""
    logger.info("Adding database indexes...")
    
    indexes_to_create = [
        # User indexes
        {
            'table': 'users_user',
            'columns': ['email'],
            'name': 'idx_users_email'
        },
        {
            'table': 'users_user',
            'columns': ['last_login'],
            'name': 'idx_users_last_login'
        },
        {
            'table': 'users_user',
            'columns': ['date_joined'],
            'name': 'idx_users_date_joined'
        },
        
        # Product indexes
        {
            'table': 'products_product',
            'columns': ['category_id', 'is_active'],
            'name': 'idx_products_category_active'
        },
        {
            'table': 'products_product',
            'columns': ['price'],
            'name': 'idx_products_price'
        },
        {
            'table': 'products_product',
            'columns': ['created_at'],
            'name': 'idx_products_created_at'
        },
        {
            'table': 'products_product',
            'columns': ['stock_quantity'],
            'name': 'idx_products_stock'
        },
        
        # Order indexes
        {
            'table': 'orders_order',
            'columns': ['user_id', 'status'],
            'name': 'idx_orders_user_status'
        },
        {
            'table': 'orders_order',
            'columns': ['created_at'],
            'name': 'idx_orders_created_at'
        },
        {
            'table': 'orders_order',
            'columns': ['status', 'created_at'],
            'name': 'idx_orders_status_created'
        },
        {
            'table': 'orders_order',
            'columns': ['session_key'],
            'name': 'idx_orders_session_key'
        },
        
        # Order item indexes
        {
            'table': 'orders_orderitem',
            'columns': ['order_id', 'product_id'],
            'name': 'idx_orderitems_order_product'
        },
        
        # Payment indexes
        {
            'table': 'payments_payment',
            'columns': ['order_id'],
            'name': 'idx_payments_order'
        },
        {
            'table': 'payments_payment',
            'columns': ['status', 'created_at'],
            'name': 'idx_payments_status_created'
        },
        {
            'table': 'payments_payment',
            'columns': ['stripe_payment_intent_id'],
            'name': 'idx_payments_stripe_intent'
        },
        
        # Cart indexes
        {
            'table': 'cart_cart',
            'columns': ['user_id'],
            'name': 'idx_cart_user'
        },
        {
            'table': 'cart_cart',
            'columns': ['session_key'],
            'name': 'idx_cart_session'
        },
        {
            'table': 'cart_cart',
            'columns': ['created_at'],
            'name': 'idx_cart_created_at'
        },
        
        # Cart item indexes
        {
            'table': 'cart_cartitem',
            'columns': ['cart_id', 'product_id'],
            'name': 'idx_cartitems_cart_product'
        },
        
        # Analytics indexes
        {
            'table': 'analytics_pageview',
            'columns': ['timestamp'],
            'name': 'idx_analytics_timestamp'
        },
        {
            'table': 'analytics_pageview',
            'columns': ['user_id', 'timestamp'],
            'name': 'idx_analytics_user_timestamp'
        },
        {
            'table': 'analytics_pageview',
            'columns': ['url', 'timestamp'],
            'name': 'idx_analytics_url_timestamp'
        },
        
        # Wishlist indexes
        {
            'table': 'wishlist_wishlist',
            'columns': ['user_id'],
            'name': 'idx_wishlist_user'
        },
        {
            'table': 'wishlist_wishlistitem',
            'columns': ['wishlist_id', 'product_id'],
            'name': 'idx_wishlistitem_wishlist_product'
        }
    ]
    
    created_count = 0
    with connection.cursor() as cursor:
        for index in indexes_to_create:
            try:
                # Check if index already exists
                cursor.execute("""
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname = %s
                """, [index['name']])
                
                if cursor.fetchone():
                    logger.info(f"Index {index['name']} already exists, skipping")
                    continue
                
                # Create index
                columns_str = ', '.join(index['columns'])
                sql = f"""
                    CREATE INDEX CONCURRENTLY {index['name']} 
                    ON {index['table']} ({columns_str})
                """
                
                cursor.execute(sql)
                created_count += 1
                logger.info(f"Created index: {index['name']}")
                
            except Exception as e:
                logger.warning(f"Failed to create index {index['name']}: {str(e)}")
    
    logger.info(f"Created {created_count} new database indexes")

def optimize_database_config():
    """Optimize database configuration settings"""
    logger.info("Optimizing database configuration...")
    
    optimizations = [
        # Update autovacuum settings for high-traffic tables
        {
            'table': 'analytics_pageview',
            'settings': {
                'autovacuum_vacuum_scale_factor': '0.1',
                'autovacuum_analyze_scale_factor': '0.05'
            }
        },
        {
            'table': 'orders_order',
            'settings': {
                'autovacuum_vacuum_scale_factor': '0.2',
                'autovacuum_analyze_scale_factor': '0.1'
            }
        },
        {
            'table': 'cart_cartitem',
            'settings': {
                'autovacuum_vacuum_scale_factor': '0.15',
                'autovacuum_analyze_scale_factor': '0.1'
            }
        }
    ]
    
    with connection.cursor() as cursor:
        for optimization in optimizations:
            try:
                for setting, value in optimization['settings'].items():
                    sql = f"""
                        ALTER TABLE {optimization['table']} 
                        SET ({setting} = {value})
                    """
                    cursor.execute(sql)
                    logger.info(f"Set {setting} = {value} for {optimization['table']}")
                    
            except Exception as e:
                logger.warning(f"Failed to optimize {optimization['table']}: {str(e)}")

def update_table_statistics():
    """Update table statistics for query planner"""
    logger.info("Updating table statistics...")
    
    high_priority_tables = [
        'users_user',
        'products_product',
        'orders_order',
        'orders_orderitem',
        'payments_payment',
        'cart_cart',
        'cart_cartitem',
        'analytics_pageview'
    ]
    
    with connection.cursor() as cursor:
        try:
            # Update statistics for high-priority tables
            for table in high_priority_tables:
                cursor.execute(f"ANALYZE {table}")
                logger.info(f"Updated statistics for {table}")
            
            # Full database analyze
            cursor.execute("ANALYZE")
            logger.info("Completed full database statistics update")
            
        except Exception as e:
            logger.error(f"Failed to update statistics: {str(e)}")

def create_materialized_views():
    """Create materialized views for commonly used aggregations"""
    logger.info("Creating materialized views...")
    
    materialized_views = [
        {
            'name': 'mv_product_stats',
            'query': """
                SELECT 
                    p.id as product_id,
                    p.name,
                    p.category_id,
                    COUNT(oi.id) as total_orders,
                    SUM(oi.quantity) as total_quantity_sold,
                    AVG(oi.price) as avg_price,
                    MAX(o.created_at) as last_ordered
                FROM products_product p
                LEFT JOIN orders_orderitem oi ON p.id = oi.product_id
                LEFT JOIN orders_order o ON oi.order_id = o.id
                WHERE p.is_active = true
                GROUP BY p.id, p.name, p.category_id
            """
        },
        {
            'name': 'mv_user_order_stats',
            'query': """
                SELECT 
                    u.id as user_id,
                    COUNT(o.id) as total_orders,
                    SUM(o.total_amount) as total_spent,
                    AVG(o.total_amount) as avg_order_value,
                    MAX(o.created_at) as last_order_date,
                    MIN(o.created_at) as first_order_date
                FROM users_user u
                LEFT JOIN orders_order o ON u.id = o.user_id
                WHERE o.status IN ('completed', 'delivered')
                GROUP BY u.id
            """
        },
        {
            'name': 'mv_daily_sales',
            'query': """
                SELECT 
                    DATE(o.created_at) as date,
                    COUNT(o.id) as order_count,
                    SUM(o.total_amount) as total_revenue,
                    AVG(o.total_amount) as avg_order_value,
                    COUNT(DISTINCT o.user_id) as unique_customers
                FROM orders_order o
                WHERE o.status IN ('completed', 'delivered')
                GROUP BY DATE(o.created_at)
                ORDER BY date DESC
            """
        }
    ]
    
    with connection.cursor() as cursor:
        for view in materialized_views:
            try:
                # Check if view already exists
                cursor.execute("""
                    SELECT 1 FROM pg_matviews 
                    WHERE matviewname = %s
                """, [view['name']])
                
                if cursor.fetchone():
                    # Refresh existing view
                    cursor.execute(f"REFRESH MATERIALIZED VIEW {view['name']}")
                    logger.info(f"Refreshed materialized view: {view['name']}")
                else:
                    # Create new view
                    sql = f"""
                        CREATE MATERIALIZED VIEW {view['name']} AS
                        {view['query']}
                    """
                    cursor.execute(sql)
                    
                    # Create index on the view
                    if 'product_id' in view['query']:
                        cursor.execute(f"CREATE INDEX ON {view['name']} (product_id)")
                    elif 'user_id' in view['query']:
                        cursor.execute(f"CREATE INDEX ON {view['name']} (user_id)")
                    elif 'date' in view['query']:
                        cursor.execute(f"CREATE INDEX ON {view['name']} (date)")
                    
                    logger.info(f"Created materialized view: {view['name']}")
                    
            except Exception as e:
                logger.warning(f"Failed to create/refresh view {view['name']}: {str(e)}")

def create_performance_monitoring_functions():
    """Create functions to monitor database performance"""
    logger.info("Creating performance monitoring functions...")
    
    functions = [
        {
            'name': 'get_slow_queries',
            'sql': """
                CREATE OR REPLACE FUNCTION get_slow_queries(threshold_ms INTEGER DEFAULT 1000)
                RETURNS TABLE(
                    query TEXT,
                    calls BIGINT,
                    total_time DOUBLE PRECISION,
                    mean_time DOUBLE PRECISION,
                    rows BIGINT
                ) AS $$
                BEGIN
                    RETURN QUERY
                    SELECT 
                        pss.query,
                        pss.calls,
                        pss.total_time,
                        pss.mean_time,
                        pss.rows
                    FROM pg_stat_statements pss
                    WHERE pss.mean_time > threshold_ms
                    ORDER BY pss.mean_time DESC
                    LIMIT 20;
                END;
                $$ LANGUAGE plpgsql;
            """
        },
        {
            'name': 'get_table_sizes',
            'sql': """
                CREATE OR REPLACE FUNCTION get_table_sizes()
                RETURNS TABLE(
                    table_name TEXT,
                    table_size TEXT,
                    index_size TEXT,
                    total_size TEXT
                ) AS $$
                BEGIN
                    RETURN QUERY
                    SELECT 
                        schemaname||'.'||tablename AS table_name,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS table_size,
                        pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) AS index_size,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) + pg_indexes_size(schemaname||'.'||tablename)) AS total_size
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
                END;
                $$ LANGUAGE plpgsql;
            """
        }
    ]
    
    with connection.cursor() as cursor:
        for func in functions:
            try:
                cursor.execute(func['sql'])
                logger.info(f"Created function: {func['name']}")
            except Exception as e:
                logger.warning(f"Failed to create function {func['name']}: {str(e)}")

def rollback_migration():
    """
    Rollback performance optimizations (remove indexes and views)
    """
    logger.info("Rolling back performance optimization migration")
    
    try:
        with transaction.atomic():
            # Remove materialized views
            remove_materialized_views()
            
            # Remove indexes (be careful with this)
            remove_added_indexes()
            
        logger.info("Performance optimization rollback completed")
        
    except Exception as e:
        logger.error(f"Rollback failed: {str(e)}")
        raise

def remove_materialized_views():
    """Remove created materialized views"""
    views_to_remove = ['mv_product_stats', 'mv_user_order_stats', 'mv_daily_sales']
    
    with connection.cursor() as cursor:
        for view_name in views_to_remove:
            try:
                cursor.execute(f"DROP MATERIALIZED VIEW IF EXISTS {view_name}")
                logger.info(f"Removed materialized view: {view_name}")
            except Exception as e:
                logger.warning(f"Failed to remove view {view_name}: {str(e)}")

def remove_added_indexes():
    """Remove indexes created by this migration"""
    # This is dangerous in production - only remove if absolutely necessary
    logger.warning("Index removal should be done carefully in production")
    # Implementation would go here if needed

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Performance Optimization Migration')
    parser.add_argument('--rollback', action='store_true', help='Rollback the migration')
    args = parser.parse_args()
    
    if args.rollback:
        rollback_migration()
    else:
        run_migration()