#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
الميزات الذكية لنظام إدارة المخازن
"""

import sqlite3
from datetime import datetime, timedelta
import statistics
from collections import defaultdict

class SmartAnalytics:
    def __init__(self, db):
        self.db = db
    
    def predict_stock_needs(self, product_id, days_ahead=30):
        """توقع احتياجات المخزون"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # جلب بيانات المبيعات للشهرين الماضيين
            cursor.execute('''
                SELECT DATE(s.created_at), SUM(si.quantity)
                FROM sales s
                JOIN sale_items si ON s.id = si.sale_id
                WHERE si.product_id = ? 
                AND s.created_at >= date('now', '-60 days')
                GROUP BY DATE(s.created_at)
                ORDER BY DATE(s.created_at)
            ''', (product_id,))
            
            sales_data = cursor.fetchall()
            
            if len(sales_data) < 7:  # نحتاج على الأقل أسبوع من البيانات
                return None
            
            # حساب متوسط المبيعات اليومية
            daily_sales = [row[1] for row in sales_data]
            avg_daily_sales = statistics.mean(daily_sales)
            
            # حساب الانحراف المعياري
            std_dev = statistics.stdev(daily_sales) if len(daily_sales) > 1 else 0
            
            # التوقع للأيام القادمة
            predicted_demand = avg_daily_sales * days_ahead
            safety_stock = std_dev * (days_ahead ** 0.5)  # جذر تربيعي للأيام
            
            # جلب المخزون الحالي
            cursor.execute('SELECT current_stock FROM products WHERE id = ?', (product_id,))
            current_stock = cursor.fetchone()[0]
            
            recommended_order = max(0, predicted_demand + safety_stock - current_stock)
            
            return {
                'current_stock': current_stock,
                'avg_daily_sales': round(avg_daily_sales, 2),
                'predicted_demand': round(predicted_demand, 2),
                'safety_stock': round(safety_stock, 2),
                'recommended_order': round(recommended_order, 2),
                'days_until_stockout': round(current_stock / avg_daily_sales, 1) if avg_daily_sales > 0 else float('inf')
            }
            
        finally:
            conn.close()
    
    def get_seasonal_trends(self, product_id):
        """تحليل الاتجاهات الموسمية"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    strftime('%m', s.created_at) as month,
                    strftime('%w', s.created_at) as weekday,
                    strftime('%H', s.created_at) as hour,
                    SUM(si.quantity) as total_sold
                FROM sales s
                JOIN sale_items si ON s.id = si.sale_id
                WHERE si.product_id = ?
                AND s.created_at >= date('now', '-365 days')
                GROUP BY month, weekday, hour
            ''', (product_id,))
            
            data = cursor.fetchall()
            
            # تجميع البيانات
            monthly_sales = defaultdict(float)
            weekday_sales = defaultdict(float)
            hourly_sales = defaultdict(float)
            
            for row in data:
                month, weekday, hour, quantity = row
                monthly_sales[int(month)] += quantity
                weekday_sales[int(weekday)] += quantity
                hourly_sales[int(hour)] += quantity
            
            # أسماء الأشهر والأيام
            month_names = ['', 'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                          'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
            
            weekday_names = ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت']
            
            return {
                'monthly_trends': {month_names[month]: sales for month, sales in monthly_sales.items()},
                'weekday_trends': {weekday_names[day]: sales for day, sales in weekday_sales.items()},
                'hourly_trends': dict(hourly_sales),
                'peak_month': month_names[max(monthly_sales.keys(), key=monthly_sales.get)] if monthly_sales else None,
                'peak_weekday': weekday_names[max(weekday_sales.keys(), key=weekday_sales.get)] if weekday_sales else None,
                'peak_hour': max(hourly_sales.keys(), key=hourly_sales.get) if hourly_sales else None
            }
            
        finally:
            conn.close()
    
    def detect_slow_moving_products(self, days=90):
        """اكتشاف المنتجات بطيئة الحركة"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    p.id,
                    p.name,
                    p.current_stock,
                    p.purchase_price,
                    COALESCE(SUM(si.quantity), 0) as total_sold,
                    (p.current_stock * p.purchase_price) as tied_capital
                FROM products p
                LEFT JOIN sale_items si ON p.id = si.product_id
                LEFT JOIN sales s ON si.sale_id = s.id AND s.created_at >= date('now', '-{} days')
                WHERE p.current_stock > 0
                GROUP BY p.id, p.name, p.current_stock, p.purchase_price
                HAVING total_sold < 5  -- أقل من 5 قطع في الفترة المحددة
                ORDER BY tied_capital DESC
            '''.format(days))
            
            return cursor.fetchall()
            
        finally:
            conn.close()
    
    def suggest_pricing_optimization(self, product_id):
        """اقتراح تحسين الأسعار"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # جلب بيانات المنتج
            cursor.execute('''
                SELECT name, purchase_price, selling_price, current_stock
                FROM products WHERE id = ?
            ''', (product_id,))
            
            product = cursor.fetchone()
            if not product:
                return None
            
            name, purchase_price, current_price, stock = product
            
            # جلب بيانات المبيعات بأسعار مختلفة
            cursor.execute('''
                SELECT si.unit_price, SUM(si.quantity) as total_sold
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                WHERE si.product_id = ?
                AND s.created_at >= date('now', '-180 days')
                GROUP BY si.unit_price
                ORDER BY si.unit_price
            ''', (product_id,))
            
            price_performance = cursor.fetchall()
            
            if not price_performance:
                return None
            
            # تحليل مرونة الطلب
            suggestions = []
            current_margin = ((current_price - purchase_price) / purchase_price) * 100
            
            # اقتراحات بناءً على الأداء
            best_price = max(price_performance, key=lambda x: x[1])[0]  # السعر الأكثر مبيعاً
            
            if best_price != current_price:
                suggestions.append({
                    'type': 'price_optimization',
                    'current_price': current_price,
                    'suggested_price': best_price,
                    'reason': f'السعر {best_price} حقق أفضل مبيعات تاريخياً'
                })
            
            # اقتراح تخفيض للمخزون الراكد
            if stock > 50:  # مخزون كبير
                discounted_price = current_price * 0.9  # خصم 10%
                if discounted_price > purchase_price * 1.1:  # مع الحفاظ على هامش 10%
                    suggestions.append({
                        'type': 'clearance_discount',
                        'current_price': current_price,
                        'suggested_price': discounted_price,
                        'reason': 'تخفيض لتصريف المخزون الراكد'
                    })
            
            return {
                'product_name': name,
                'current_margin': round(current_margin, 1),
                'suggestions': suggestions,
                'price_history': price_performance
            }
            
        finally:
            conn.close()
    
    def generate_reorder_alerts(self):
        """إنشاء تنبيهات إعادة الطلب"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # المنتجات التي وصلت للحد الأدنى
            cursor.execute('''
                SELECT id, name, current_stock, min_stock
                FROM products
                WHERE current_stock <= min_stock
                AND current_stock >= 0
                ORDER BY (current_stock - min_stock)
            ''')
            
            low_stock_products = cursor.fetchall()
            
            alerts = []
            
            for product in low_stock_products:
                product_id, name, current_stock, min_stock = product
                
                # توقع احتياجات المخزون
                prediction = self.predict_stock_needs(product_id)
                
                alert = {
                    'product_id': product_id,
                    'product_name': name,
                    'current_stock': current_stock,
                    'min_stock': min_stock,
                    'urgency': 'critical' if current_stock == 0 else 'high' if current_stock < min_stock else 'medium'
                }
                
                if prediction:
                    alert.update({
                        'recommended_order': prediction['recommended_order'],
                        'days_until_stockout': prediction['days_until_stockout']
                    })
                
                alerts.append(alert)
            
            return alerts
            
        finally:
            conn.close()
    
    def analyze_customer_behavior(self, customer_id=None):
        """تحليل سلوك العملاء"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            if customer_id:
                # تحليل عميل محدد
                cursor.execute('''
                    SELECT 
                        COUNT(s.id) as total_purchases,
                        AVG(s.final_amount) as avg_purchase_amount,
                        SUM(s.final_amount) as total_spent,
                        MAX(DATE(s.created_at)) as last_purchase,
                        MIN(DATE(s.created_at)) as first_purchase
                    FROM sales s
                    WHERE s.customer_id = ?
                ''', (customer_id,))
                
                customer_stats = cursor.fetchone()
                
                # المنتجات المفضلة
                cursor.execute('''
                    SELECT p.name, SUM(si.quantity) as total_bought
                    FROM sale_items si
                    JOIN sales s ON si.sale_id = s.id
                    JOIN products p ON si.product_id = p.id
                    WHERE s.customer_id = ?
                    GROUP BY p.id, p.name
                    ORDER BY total_bought DESC
                    LIMIT 5
                ''', (customer_id,))
                
                favorite_products = cursor.fetchall()
                
                return {
                    'customer_id': customer_id,
                    'total_purchases': customer_stats[0],
                    'avg_purchase_amount': round(customer_stats[1] or 0, 2),
                    'total_spent': round(customer_stats[2] or 0, 2),
                    'last_purchase': customer_stats[3],
                    'first_purchase': customer_stats[4],
                    'favorite_products': favorite_products
                }
            
            else:
                # تحليل عام للعملاء
                cursor.execute('''
                    SELECT 
                        c.id,
                        c.name,
                        COUNT(s.id) as purchase_count,
                        SUM(s.final_amount) as total_spent,
                        MAX(DATE(s.created_at)) as last_purchase
                    FROM customers c
                    LEFT JOIN sales s ON c.id = s.customer_id
                    GROUP BY c.id, c.name
                    HAVING purchase_count > 0
                    ORDER BY total_spent DESC
                    LIMIT 20
                ''')
                
                return cursor.fetchall()
                
        finally:
            conn.close()

class AutomationEngine:
    def __init__(self, db):
        self.db = db
        self.analytics = SmartAnalytics(db)
    
    def auto_generate_purchase_orders(self):
        """إنشاء أوامر شراء تلقائية"""
        alerts = self.analytics.generate_reorder_alerts()
        
        purchase_suggestions = []
        
        for alert in alerts:
            if alert['urgency'] in ['critical', 'high']:
                suggestion = {
                    'product_id': alert['product_id'],
                    'product_name': alert['product_name'],
                    'current_stock': alert['current_stock'],
                    'suggested_quantity': alert.get('recommended_order', alert['min_stock'] * 2),
                    'urgency': alert['urgency'],
                    'reason': f"المخزون الحالي ({alert['current_stock']}) أقل من الحد الأدنى ({alert['min_stock']})"
                }
                
                purchase_suggestions.append(suggestion)
        
        return purchase_suggestions
    
    def optimize_inventory_levels(self):
        """تحسين مستويات المخزون"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT id FROM products WHERE current_stock > 0')
            product_ids = [row[0] for row in cursor.fetchall()]
            
            optimization_suggestions = []
            
            for product_id in product_ids:
                prediction = self.analytics.predict_stock_needs(product_id)
                
                if prediction:
                    current_stock = prediction['current_stock']
                    avg_daily_sales = prediction['avg_daily_sales']
                    
                    # اقتراح حد أدنى جديد
                    suggested_min_stock = max(1, int(avg_daily_sales * 7))  # أسبوع من المبيعات
                    
                    cursor.execute('SELECT min_stock FROM products WHERE id = ?', (product_id,))
                    current_min_stock = cursor.fetchone()[0]
                    
                    if abs(suggested_min_stock - current_min_stock) > 2:
                        optimization_suggestions.append({
                            'product_id': product_id,
                            'current_min_stock': current_min_stock,
                            'suggested_min_stock': suggested_min_stock,
                            'reason': f'بناءً على متوسط المبيعات اليومية ({avg_daily_sales:.1f})'
                        })
            
            return optimization_suggestions
            
        finally:
            conn.close()
    
    def detect_anomalies(self):
        """اكتشاف الشذوذ في البيانات"""
        anomalies = []
        
        # مبيعات غير عادية
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            # البحث عن مبيعات كبيرة غير عادية
            cursor.execute('''
                SELECT s.id, s.final_amount, s.created_at, c.name
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE s.final_amount > (
                    SELECT AVG(final_amount) * 3
                    FROM sales
                    WHERE created_at >= date('now', '-30 days')
                )
                AND s.created_at >= date('now', '-7 days')
            ''')
            
            unusual_sales = cursor.fetchall()
            
            for sale in unusual_sales:
                anomalies.append({
                    'type': 'unusual_sale',
                    'sale_id': sale[0],
                    'amount': sale[1],
                    'date': sale[2],
                    'customer': sale[3] or 'عميل عادي',
                    'description': f'مبيعات غير عادية بقيمة {sale[1]:.2f}'
                })
            
            # منتجات بدون مبيعات لفترة طويلة
            cursor.execute('''
                SELECT p.id, p.name, p.current_stock
                FROM products p
                WHERE p.id NOT IN (
                    SELECT DISTINCT si.product_id
                    FROM sale_items si
                    JOIN sales s ON si.sale_id = s.id
                    WHERE s.created_at >= date('now', '-90 days')
                )
                AND p.current_stock > 0
            ''')
            
            stagnant_products = cursor.fetchall()
            
            for product in stagnant_products:
                anomalies.append({
                    'type': 'stagnant_product',
                    'product_id': product[0],
                    'product_name': product[1],
                    'stock': product[2],
                    'description': f'منتج بدون مبيعات لأكثر من 90 يوم'
                })
            
            return anomalies
            
        finally:
            conn.close()