#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام التحليلات والذكاء الاصطناعي المتقدم
تصميم: المهندس هشام المجمر - 773988932
"""

import sqlite3
import json
import math
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics
import random

class AIAnalyticsEngine:
    """محرك التحليلات والذكاء الاصطناعي"""
    
    def __init__(self, db_path):
        self.db_path = db_path
    
    def get_connection(self):
        """الحصول على اتصال قاعدة البيانات"""
        return sqlite3.connect(self.db_path)
    
    def analyze_sales_patterns(self, days=30):
        """تحليل أنماط المبيعات"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # بيانات المبيعات للفترة المحددة
            date_threshold = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute('''
                SELECT 
                    DATE(s.sale_date) as sale_date,
                    strftime('%w', s.sale_date) as day_of_week,
                    strftime('%H', s.sale_date) as hour,
                    COUNT(*) as transaction_count,
                    SUM(s.total) as total_sales,
                    AVG(s.total) as avg_transaction
                FROM sales s
                WHERE s.sale_date >= ?
                GROUP BY DATE(s.sale_date), strftime('%w', s.sale_date), strftime('%H', s.sale_date)
                ORDER BY s.sale_date
            ''', (date_threshold,))
            
            sales_data = cursor.fetchall()
            
            # تحليل الأنماط
            patterns = {
                'daily_trends': self._analyze_daily_trends(sales_data),
                'hourly_trends': self._analyze_hourly_trends(sales_data),
                'weekly_trends': self._analyze_weekly_trends(sales_data),
                'seasonal_patterns': self._detect_seasonal_patterns(sales_data)
            }
            
            return patterns
            
        except Exception as e:
            print(f"خطأ في تحليل أنماط المبيعات: {e}")
            return {}
        finally:
            conn.close()
    
    def _analyze_daily_trends(self, sales_data):
        """تحليل الاتجاهات اليومية"""
        daily_sales = defaultdict(list)
        
        for row in sales_data:
            date, day_of_week, hour, count, total, avg = row
            daily_sales[date].append(total or 0)
        
        # حساب المتوسطات اليومية
        daily_averages = {}
        for date, sales in daily_sales.items():
            daily_averages[date] = sum(sales)
        
        # تحديد الاتجاه العام
        dates = sorted(daily_averages.keys())
        values = [daily_averages[date] for date in dates]
        
        if len(values) >= 2:
            trend = "صاعد" if values[-1] > values[0] else "هابط"
            growth_rate = ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
        else:
            trend = "مستقر"
            growth_rate = 0
        
        return {
            'trend': trend,
            'growth_rate': round(growth_rate, 2),
            'best_day': max(daily_averages, key=daily_averages.get) if daily_averages else None,
            'worst_day': min(daily_averages, key=daily_averages.get) if daily_averages else None,
            'average_daily_sales': round(statistics.mean(values), 2) if values else 0
        }
    
    def _analyze_hourly_trends(self, sales_data):
        """تحليل الاتجاهات بالساعة"""
        hourly_sales = defaultdict(list)
        
        for row in sales_data:
            date, day_of_week, hour, count, total, avg = row
            hourly_sales[int(hour)].append(total or 0)
        
        # حساب المتوسطات بالساعة
        hourly_averages = {}
        for hour in range(24):
            if hour in hourly_sales:
                hourly_averages[hour] = statistics.mean(hourly_sales[hour])
            else:
                hourly_averages[hour] = 0
        
        # تحديد أفضل وأسوأ ساعات
        peak_hour = max(hourly_averages, key=hourly_averages.get)
        low_hour = min(hourly_averages, key=hourly_averages.get)
        
        return {
            'peak_hour': peak_hour,
            'low_hour': low_hour,
            'peak_sales': round(hourly_averages[peak_hour], 2),
            'low_sales': round(hourly_averages[low_hour], 2),
            'hourly_distribution': hourly_averages
        }
    
    def _analyze_weekly_trends(self, sales_data):
        """تحليل الاتجاهات الأسبوعية"""
        weekly_sales = defaultdict(list)
        day_names = ['الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت']
        
        for row in sales_data:
            date, day_of_week, hour, count, total, avg = row
            weekly_sales[int(day_of_week)].append(total or 0)
        
        # حساب المتوسطات الأسبوعية
        weekly_averages = {}
        for day in range(7):
            if day in weekly_sales:
                weekly_averages[day] = statistics.mean(weekly_sales[day])
            else:
                weekly_averages[day] = 0
        
        # تحديد أفضل وأسوأ أيام
        best_day = max(weekly_averages, key=weekly_averages.get)
        worst_day = min(weekly_averages, key=weekly_averages.get)
        
        return {
            'best_day': day_names[best_day],
            'worst_day': day_names[worst_day],
            'best_day_sales': round(weekly_averages[best_day], 2),
            'worst_day_sales': round(weekly_averages[worst_day], 2),
            'weekly_distribution': {day_names[i]: round(weekly_averages[i], 2) for i in range(7)}
        }
    
    def _detect_seasonal_patterns(self, sales_data):
        """كشف الأنماط الموسمية"""
        monthly_sales = defaultdict(list)
        
        for row in sales_data:
            date, day_of_week, hour, count, total, avg = row
            month = datetime.fromisoformat(date).month
            monthly_sales[month].append(total or 0)
        
        # حساب المتوسطات الشهرية
        monthly_averages = {}
        month_names = ['', 'يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                      'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
        
        for month, sales in monthly_sales.items():
            monthly_averages[month] = statistics.mean(sales)
        
        if monthly_averages:
            peak_month = max(monthly_averages, key=monthly_averages.get)
            low_month = min(monthly_averages, key=monthly_averages.get)
            
            return {
                'peak_month': month_names[peak_month],
                'low_month': month_names[low_month],
                'peak_sales': round(monthly_averages[peak_month], 2),
                'low_sales': round(monthly_averages[low_month], 2),
                'seasonal_variance': round(statistics.stdev(monthly_averages.values()), 2) if len(monthly_averages) > 1 else 0
            }
        
        return {}
    
    def predict_demand(self, product_id, days_ahead=7):
        """توقع الطلب على المنتج باستخدام خوارزميات متقدمة"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # جلب بيانات المبيعات التاريخية
            cursor.execute('''
                SELECT 
                    DATE(s.sale_date) as sale_date,
                    SUM(si.quantity) as daily_quantity
                FROM sales s
                JOIN sale_items si ON s.id = si.sale_id
                WHERE si.product_id = ? 
                AND s.sale_date >= date('now', '-60 days')
                GROUP BY DATE(s.sale_date)
                ORDER BY sale_date
            ''', (product_id,))
            
            sales_history = cursor.fetchall()
            
            if len(sales_history) < 7:
                return self._simple_demand_prediction(product_id, days_ahead)
            
            # استخراج البيانات
            dates = [row[0] for row in sales_history]
            quantities = [row[1] for row in sales_history]
            
            # تطبيق خوارزميات التوقع
            predictions = {
                'moving_average': self._moving_average_prediction(quantities, days_ahead),
                'exponential_smoothing': self._exponential_smoothing_prediction(quantities, days_ahead),
                'linear_regression': self._linear_regression_prediction(quantities, days_ahead),
                'seasonal_adjustment': self._seasonal_adjustment_prediction(quantities, days_ahead)
            }
            
            # حساب التوقع النهائي (متوسط مرجح)
            weights = {'moving_average': 0.2, 'exponential_smoothing': 0.3, 
                      'linear_regression': 0.3, 'seasonal_adjustment': 0.2}
            
            final_prediction = sum(predictions[method] * weights[method] 
                                 for method in predictions)
            
            # معلومات إضافية
            confidence_level = self._calculate_confidence_level(quantities)
            trend = self._detect_trend(quantities)
            
            return {
                'predicted_demand': max(0, round(final_prediction)),
                'confidence_level': confidence_level,
                'trend': trend,
                'individual_predictions': predictions,
                'historical_average': round(statistics.mean(quantities), 2),
                'volatility': round(statistics.stdev(quantities), 2) if len(quantities) > 1 else 0
            }
            
        except Exception as e:
            print(f"خطأ في توقع الطلب: {e}")
            return self._simple_demand_prediction(product_id, days_ahead)
        finally:
            conn.close()
    
    def _simple_demand_prediction(self, product_id, days_ahead):
        """توقع بسيط للطلب"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT AVG(si.quantity)
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                WHERE si.product_id = ? 
                AND s.sale_date >= date('now', '-30 days')
            ''', (product_id,))
            
            result = cursor.fetchone()
            avg_daily = result[0] if result and result[0] else 0
            
            return {
                'predicted_demand': max(0, round(avg_daily * days_ahead)),
                'confidence_level': 'منخفض',
                'trend': 'غير محدد',
                'method': 'بسيط'
            }
            
        except:
            return {'predicted_demand': 0, 'confidence_level': 'منخفض', 'trend': 'غير محدد'}
        finally:
            conn.close()
    
    def _moving_average_prediction(self, data, days_ahead, window=7):
        """توقع بالمتوسط المتحرك"""
        if len(data) < window:
            return statistics.mean(data) * days_ahead if data else 0
        
        recent_avg = statistics.mean(data[-window:])
        return recent_avg * days_ahead
    
    def _exponential_smoothing_prediction(self, data, days_ahead, alpha=0.3):
        """توقع بالتنعيم الأسي"""
        if not data:
            return 0
        
        smoothed = data[0]
        for value in data[1:]:
            smoothed = alpha * value + (1 - alpha) * smoothed
        
        return smoothed * days_ahead
    
    def _linear_regression_prediction(self, data, days_ahead):
        """توقع بالانحدار الخطي البسيط"""
        if len(data) < 2:
            return statistics.mean(data) * days_ahead if data else 0
        
        n = len(data)
        x = list(range(n))
        y = data
        
        # حساب معاملات الانحدار
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return y_mean * days_ahead
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # التوقع للأيام القادمة
        future_x = n + days_ahead - 1
        prediction = slope * future_x + intercept
        
        return max(0, prediction)
    
    def _seasonal_adjustment_prediction(self, data, days_ahead):
        """توقع مع التعديل الموسمي"""
        if len(data) < 14:  # نحتاج أسبوعين على الأقل
            return statistics.mean(data) * days_ahead if data else 0
        
        # حساب المتوسط الأسبوعي
        weekly_pattern = []
        for i in range(7):
            day_values = [data[j] for j in range(i, len(data), 7)]
            weekly_pattern.append(statistics.mean(day_values) if day_values else 0)
        
        # التوقع بناءً على النمط الأسبوعي
        total_prediction = 0
        for day in range(days_ahead):
            day_of_week = day % 7
            total_prediction += weekly_pattern[day_of_week]
        
        return total_prediction
    
    def _calculate_confidence_level(self, data):
        """حساب مستوى الثقة في التوقع"""
        if len(data) < 2:
            return 'منخفض'
        
        # حساب معامل التباين
        mean_val = statistics.mean(data)
        if mean_val == 0:
            return 'منخفض'
        
        cv = statistics.stdev(data) / mean_val
        
        if cv < 0.2:
            return 'عالي'
        elif cv < 0.5:
            return 'متوسط'
        else:
            return 'منخفض'
    
    def _detect_trend(self, data):
        """كشف الاتجاه في البيانات"""
        if len(data) < 3:
            return 'غير محدد'
        
        # حساب الاتجاه باستخدام الانحدار البسيط
        n = len(data)
        x = list(range(n))
        
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(data)
        
        numerator = sum((x[i] - x_mean) * (data[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 'مستقر'
        
        slope = numerator / denominator
        
        if slope > 0.1:
            return 'صاعد'
        elif slope < -0.1:
            return 'هابط'
        else:
            return 'مستقر'
    
    def analyze_customer_behavior(self, customer_id=None):
        """تحليل سلوك العملاء"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if customer_id:
                # تحليل عميل محدد
                return self._analyze_individual_customer(cursor, customer_id)
            else:
                # تحليل عام للعملاء
                return self._analyze_customer_segments(cursor)
                
        except Exception as e:
            print(f"خطأ في تحليل سلوك العملاء: {e}")
            return {}
        finally:
            conn.close()
    
    def _analyze_individual_customer(self, cursor, customer_id):
        """تحليل عميل فردي"""
        # بيانات العميل الأساسية
        cursor.execute('''
            SELECT c.name, c.phone, c.email,
                   COUNT(s.id) as total_orders,
                   SUM(s.total) as total_spent,
                   AVG(s.total) as avg_order_value,
                   MAX(s.sale_date) as last_purchase,
                   MIN(s.sale_date) as first_purchase
            FROM customers c
            LEFT JOIN sales s ON c.id = s.customer_id
            WHERE c.id = ?
            GROUP BY c.id
        ''', (customer_id,))
        
        customer_data = cursor.fetchone()
        
        if not customer_data:
            return {}
        
        # تحليل تفضيلات المنتجات
        cursor.execute('''
            SELECT p.name, c.name as category, SUM(si.quantity) as total_qty,
                   SUM(si.total) as total_spent
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            JOIN products p ON si.product_id = p.id
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE s.customer_id = ?
            GROUP BY p.id
            ORDER BY total_qty DESC
            LIMIT 10
        ''', (customer_id,))
        
        favorite_products = cursor.fetchall()
        
        # تحليل أنماط الشراء
        cursor.execute('''
            SELECT strftime('%w', s.sale_date) as day_of_week,
                   strftime('%H', s.sale_date) as hour,
                   COUNT(*) as frequency
            FROM sales s
            WHERE s.customer_id = ?
            GROUP BY strftime('%w', s.sale_date), strftime('%H', s.sale_date)
            ORDER BY frequency DESC
        ''', (customer_id,))
        
        purchase_patterns = cursor.fetchall()
        
        # حساب قيمة العميل
        name, phone, email, total_orders, total_spent, avg_order, last_purchase, first_purchase = customer_data
        
        # تصنيف العميل
        if total_spent > 10000:
            customer_tier = 'VIP'
        elif total_spent > 5000:
            customer_tier = 'ذهبي'
        elif total_spent > 1000:
            customer_tier = 'فضي'
        else:
            customer_tier = 'عادي'
        
        # حساب معدل تكرار الشراء
        if first_purchase and last_purchase:
            days_between = (datetime.fromisoformat(last_purchase) - 
                          datetime.fromisoformat(first_purchase)).days
            purchase_frequency = total_orders / max(days_between, 1) if days_between > 0 else 0
        else:
            purchase_frequency = 0
        
        return {
            'customer_info': {
                'name': name,
                'phone': phone,
                'email': email,
                'tier': customer_tier
            },
            'purchase_summary': {
                'total_orders': total_orders or 0,
                'total_spent': round(total_spent or 0, 2),
                'avg_order_value': round(avg_order or 0, 2),
                'purchase_frequency': round(purchase_frequency, 3),
                'last_purchase': last_purchase,
                'first_purchase': first_purchase
            },
            'favorite_products': favorite_products,
            'purchase_patterns': purchase_patterns
        }
    
    def _analyze_customer_segments(self, cursor):
        """تحليل شرائح العملاء"""
        # إحصائيات عامة
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT c.id) as total_customers,
                COUNT(DISTINCT s.id) as total_orders,
                SUM(s.total) as total_revenue,
                AVG(s.total) as avg_order_value
            FROM customers c
            LEFT JOIN sales s ON c.id = s.customer_id
        ''')
        
        general_stats = cursor.fetchone()
        
        # تصنيف العملاء حسب القيمة
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN total_spent > 10000 THEN 'VIP'
                    WHEN total_spent > 5000 THEN 'ذهبي'
                    WHEN total_spent > 1000 THEN 'فضي'
                    ELSE 'عادي'
                END as tier,
                COUNT(*) as customer_count,
                AVG(total_spent) as avg_spent
            FROM (
                SELECT c.id, COALESCE(SUM(s.total), 0) as total_spent
                FROM customers c
                LEFT JOIN sales s ON c.id = s.customer_id
                GROUP BY c.id
            )
            GROUP BY tier
        ''')
        
        customer_tiers = cursor.fetchall()
        
        return {
            'general_stats': {
                'total_customers': general_stats[0] or 0,
                'total_orders': general_stats[1] or 0,
                'total_revenue': round(general_stats[2] or 0, 2),
                'avg_order_value': round(general_stats[3] or 0, 2)
            },
            'customer_tiers': customer_tiers
        }
    
    def generate_business_insights(self):
        """توليد رؤى تجارية ذكية"""
        insights = []
        
        try:
            # تحليل المنتجات بطيئة الحركة
            slow_moving = self._identify_slow_moving_products()
            if slow_moving:
                insights.append({
                    'type': 'تحذير',
                    'title': 'منتجات بطيئة الحركة',
                    'message': f'يوجد {len(slow_moving)} منتج بطيء الحركة يحتاج لاهتمام',
                    'action': 'اقتراح خصومات أو عروض ترويجية',
                    'priority': 'عالي'
                })
            
            # تحليل المخزون المنخفض
            low_stock = self._identify_low_stock_products()
            if low_stock:
                insights.append({
                    'type': 'تنبيه',
                    'title': 'مخزون منخفض',
                    'message': f'{len(low_stock)} منتج يحتاج لإعادة تموين',
                    'action': 'إنشاء أوامر شراء',
                    'priority': 'متوسط'
                })
            
            # تحليل الاتجاهات
            trends = self._analyze_sales_trends()
            if trends.get('growth_rate', 0) < -10:
                insights.append({
                    'type': 'تحذير',
                    'title': 'انخفاض في المبيعات',
                    'message': f'انخفاض بنسبة {abs(trends["growth_rate"]):.1f}% في المبيعات',
                    'action': 'مراجعة استراتيجية التسويق',
                    'priority': 'عالي'
                })
            elif trends.get('growth_rate', 0) > 20:
                insights.append({
                    'type': 'إيجابي',
                    'title': 'نمو في المبيعات',
                    'message': f'نمو بنسبة {trends["growth_rate"]:.1f}% في المبيعات',
                    'action': 'زيادة المخزون للمنتجات الرائجة',
                    'priority': 'متوسط'
                })
            
            # تحليل الربحية
            profitability = self._analyze_profitability()
            if profitability.get('low_margin_products'):
                insights.append({
                    'type': 'معلومة',
                    'title': 'منتجات بهامش ربح منخفض',
                    'message': f'{len(profitability["low_margin_products"])} منتج بهامش ربح أقل من 20%',
                    'action': 'مراجعة الأسعار أو التكاليف',
                    'priority': 'منخفض'
                })
            
            return insights
            
        except Exception as e:
            print(f"خطأ في توليد الرؤى التجارية: {e}")
            return []
    
    def _identify_slow_moving_products(self):
        """تحديد المنتجات بطيئة الحركة"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT p.id, p.name, p.stock,
                       COALESCE(SUM(si.quantity), 0) as total_sold
                FROM products p
                LEFT JOIN sale_items si ON p.id = si.product_id
                LEFT JOIN sales s ON si.sale_id = s.id
                WHERE s.sale_date >= date('now', '-30 days') OR s.sale_date IS NULL
                GROUP BY p.id
                HAVING total_sold < 5 AND p.stock > 10
                ORDER BY total_sold ASC
            ''')
            
            return cursor.fetchall()
            
        except:
            return []
        finally:
            conn.close()
    
    def _identify_low_stock_products(self):
        """تحديد المنتجات ذات المخزون المنخفض"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, name, stock, min_stock
                FROM products
                WHERE stock <= min_stock
                ORDER BY (stock - min_stock) ASC
            ''')
            
            return cursor.fetchall()
            
        except:
            return []
        finally:
            conn.close()
    
    def _analyze_sales_trends(self):
        """تحليل اتجاهات المبيعات"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    DATE(sale_date) as sale_date,
                    SUM(total) as daily_total
                FROM sales
                WHERE sale_date >= date('now', '-30 days')
                GROUP BY DATE(sale_date)
                ORDER BY sale_date
            ''')
            
            daily_sales = cursor.fetchall()
            
            if len(daily_sales) >= 2:
                first_week = sum(row[1] for row in daily_sales[:7])
                last_week = sum(row[1] for row in daily_sales[-7:])
                
                growth_rate = ((last_week - first_week) / first_week * 100) if first_week > 0 else 0
                
                return {'growth_rate': growth_rate}
            
            return {}
            
        except:
            return {}
        finally:
            conn.close()
    
    def _analyze_profitability(self):
        """تحليل الربحية"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # منتجات بهامش ربح منخفض (تحتاج لبيانات التكلفة)
            cursor.execute('''
                SELECT p.id, p.name, p.price
                FROM products p
                WHERE p.price < 50  -- افتراض أن المنتجات الرخيصة لها هامش ربح منخفض
                ORDER BY p.price ASC
                LIMIT 10
            ''')
            
            low_margin_products = cursor.fetchall()
            
            return {'low_margin_products': low_margin_products}
            
        except:
            return {}
        finally:
            conn.close()

class SmartRecommendationSystem:
    """نظام التوصيات الذكي المتقدم"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.analytics = AIAnalyticsEngine(db_path)
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def get_personalized_recommendations(self, customer_id, limit=10):
        """توصيات شخصية متقدمة للعميل"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # تحليل سلوك العميل
            customer_analysis = self.analytics.analyze_customer_behavior(customer_id)
            
            recommendations = []
            
            # توصيات بناءً على المشتريات السابقة
            past_purchases = self._get_customer_purchase_history(cursor, customer_id)
            category_preferences = self._analyze_category_preferences(past_purchases)
            
            # توصيات من الفئات المفضلة
            for category_id, preference_score in category_preferences.items():
                category_products = self._get_category_products(cursor, category_id, limit=3)
                for product in category_products:
                    if not self._customer_bought_product(cursor, customer_id, product[0]):
                        recommendations.append({
                            'product_id': product[0],
                            'product_name': product[1],
                            'price': product[2],
                            'reason': f'من فئة مفضلة ({product[3]})',
                            'confidence': preference_score,
                            'type': 'category_preference'
                        })
            
            # توصيات بناءً على العملاء المشابهين
            similar_customers = self._find_similar_customers(cursor, customer_id)
            for similar_customer in similar_customers:
                similar_products = self._get_customer_unique_products(cursor, similar_customer[0], customer_id)
                for product in similar_products[:2]:
                    recommendations.append({
                        'product_id': product[0],
                        'product_name': product[1],
                        'price': product[2],
                        'reason': 'عملاء مشابهون اشتروه',
                        'confidence': 0.7,
                        'type': 'collaborative_filtering'
                    })
            
            # توصيات المنتجات الرائجة
            trending = self._get_trending_products(cursor, limit=5)
            for product in trending:
                if not self._customer_bought_product(cursor, customer_id, product[0]):
                    recommendations.append({
                        'product_id': product[0],
                        'product_name': product[1],
                        'price': product[2],
                        'reason': f'رائج (مباع {product[4]} مرة)',
                        'confidence': 0.6,
                        'type': 'trending'
                    })
            
            # ترتيب التوصيات حسب الثقة
            recommendations.sort(key=lambda x: x['confidence'], reverse=True)
            
            return recommendations[:limit]
            
        except Exception as e:
            print(f"خطأ في التوصيات الشخصية: {e}")
            return []
        finally:
            conn.close()
    
    def _get_customer_purchase_history(self, cursor, customer_id):
        """جلب تاريخ مشتريات العميل"""
        cursor.execute('''
            SELECT p.id, p.category_id, si.quantity, si.total
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            JOIN products p ON si.product_id = p.id
            WHERE s.customer_id = ?
        ''', (customer_id,))
        
        return cursor.fetchall()
    
    def _analyze_category_preferences(self, purchases):
        """تحليل تفضيلات الفئات"""
        category_scores = defaultdict(float)
        
        for product_id, category_id, quantity, total in purchases:
            if category_id:
                # نقاط بناءً على الكمية والقيمة
                score = (quantity * 0.3) + (total * 0.7)
                category_scores[category_id] += score
        
        # تطبيع النقاط
        max_score = max(category_scores.values()) if category_scores else 1
        normalized_scores = {cat: score/max_score for cat, score in category_scores.items()}
        
        return dict(sorted(normalized_scores.items(), key=lambda x: x[1], reverse=True))
    
    def _get_category_products(self, cursor, category_id, limit=5):
        """جلب منتجات من فئة معينة"""
        cursor.execute('''
            SELECT p.id, p.name, p.price, c.name as category_name
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE p.category_id = ? AND p.stock > 0
            ORDER BY p.stock DESC
            LIMIT ?
        ''', (category_id, limit))
        
        return cursor.fetchall()
    
    def _customer_bought_product(self, cursor, customer_id, product_id):
        """التحقق من شراء العميل للمنتج سابقاً"""
        cursor.execute('''
            SELECT 1
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            WHERE s.customer_id = ? AND si.product_id = ?
            LIMIT 1
        ''', (customer_id, product_id))
        
        return cursor.fetchone() is not None
    
    def _find_similar_customers(self, cursor, customer_id, limit=5):
        """العثور على عملاء مشابهين"""
        # خوارزمية بسيطة للعثور على العملاء المشابهين
        cursor.execute('''
            SELECT DISTINCT s2.customer_id, COUNT(*) as common_products
            FROM sale_items si1
            JOIN sales s1 ON si1.sale_id = s1.id
            JOIN sale_items si2 ON si1.product_id = si2.product_id
            JOIN sales s2 ON si2.sale_id = s2.id
            WHERE s1.customer_id = ? AND s2.customer_id != ?
            GROUP BY s2.customer_id
            ORDER BY common_products DESC
            LIMIT ?
        ''', (customer_id, customer_id, limit))
        
        return cursor.fetchall()
    
    def _get_customer_unique_products(self, cursor, similar_customer_id, original_customer_id):
        """جلب منتجات فريدة اشتراها عميل مشابه"""
        cursor.execute('''
            SELECT DISTINCT p.id, p.name, p.price
            FROM sale_items si
            JOIN sales s ON si.sale_id = s.id
            JOIN products p ON si.product_id = p.id
            WHERE s.customer_id = ? 
            AND p.id NOT IN (
                SELECT DISTINCT si2.product_id
                FROM sale_items si2
                JOIN sales s2 ON si2.sale_id = s2.id
                WHERE s2.customer_id = ?
            )
            AND p.stock > 0
            LIMIT 3
        ''', (similar_customer_id, original_customer_id))
        
        return cursor.fetchall()
    
    def _get_trending_products(self, cursor, limit=10):
        """جلب المنتجات الرائجة"""
        cursor.execute('''
            SELECT p.id, p.name, p.price, p.stock, SUM(si.quantity) as total_sold
            FROM products p
            JOIN sale_items si ON p.id = si.product_id
            JOIN sales s ON si.sale_id = s.id
            WHERE s.sale_date >= date('now', '-7 days') AND p.stock > 0
            GROUP BY p.id
            ORDER BY total_sold DESC
            LIMIT ?
        ''', (limit,))
        
        return cursor.fetchall()