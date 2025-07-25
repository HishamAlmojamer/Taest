#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أدوات الطباعة والتصدير
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
import csv
import json

class PrintManager:
    def __init__(self, parent_window):
        self.parent = parent_window
    
    def print_invoice(self, invoice_data, invoice_type="sale"):
        """طباعة الفاتورة"""
        try:
            # إنشاء نافذة معاينة الطباعة
            preview_window = tk.Toplevel(self.parent)
            preview_window.title(f"معاينة الطباعة - فاتورة {invoice_type}")
            preview_window.geometry("800x600")
            preview_window.grab_set()
            
            # إنشاء محتوى الفاتورة
            content = self.generate_invoice_content(invoice_data, invoice_type)
            
            # عرض المحتوى
            text_widget = tk.Text(preview_window, wrap=tk.WORD, font=("Courier New", 10))
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_widget.insert(tk.END, content)
            text_widget.config(state=tk.DISABLED)
            
            # أزرار الطباعة
            buttons_frame = ttk.Frame(preview_window)
            buttons_frame.pack(fill=tk.X, padx=10, pady=10)
            
            ttk.Button(buttons_frame, text="طباعة", 
                      command=lambda: self.send_to_printer(content)).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(buttons_frame, text="حفظ كـ PDF", 
                      command=lambda: self.save_as_pdf(content, invoice_type)).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(buttons_frame, text="إغلاق", 
                      command=preview_window.destroy).pack(side=tk.RIGHT)
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في إنشاء معاينة الطباعة: {str(e)}")
    
    def generate_invoice_content(self, invoice_data, invoice_type):
        """إنشاء محتوى الفاتورة"""
        content = []
        content.append("=" * 60)
        content.append("                    نظام إدارة المخازن")
        content.append("=" * 60)
        content.append("")
        
        # نوع الفاتورة
        if invoice_type == "sale":
            content.append("                      فاتورة بيع")
        else:
            content.append("                     فاتورة شراء")
        
        content.append("")
        content.append(f"رقم الفاتورة: {invoice_data.get('id', 'غير محدد')}")
        content.append(f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        if invoice_type == "sale":
            content.append(f"العميل: {invoice_data.get('customer', 'عميل عادي')}")
        else:
            content.append(f"المورد: {invoice_data.get('supplier', 'غير محدد')}")
        
        content.append("")
        content.append("-" * 60)
        content.append(f"{'المنتج':<25} {'الكمية':<8} {'السعر':<10} {'الإجمالي':<10}")
        content.append("-" * 60)
        
        # عناصر الفاتورة
        for item in invoice_data.get('items', []):
            content.append(f"{item['name']:<25} {item['quantity']:<8} {item['price']:<10.2f} {item['total']:<10.2f}")
        
        content.append("-" * 60)
        content.append(f"{'المجموع الفرعي:':<45} {invoice_data.get('subtotal', 0):<10.2f}")
        content.append(f"{'الخصم:':<45} {invoice_data.get('discount', 0):<10.2f}")
        content.append(f"{'الإجمالي النهائي:':<45} {invoice_data.get('total', 0):<10.2f}")
        content.append("=" * 60)
        content.append("")
        content.append("                    شكراً لتعاملكم معنا")
        content.append("")
        
        return "\n".join(content)
    
    def send_to_printer(self, content):
        """إرسال للطابعة"""
        try:
            # حفظ مؤقت للطباعة
            temp_file = "temp_print.txt"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # طباعة الملف (Windows)
            os.system(f'notepad /p {temp_file}')
            
            # حذف الملف المؤقت
            try:
                os.remove(temp_file)
            except:
                pass
                
            messagebox.showinfo("نجح", "تم إرسال الفاتورة للطابعة")
            
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في الطباعة: {str(e)}")
    
    def save_as_pdf(self, content, invoice_type):
        """حفظ كـ PDF"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title=f"حفظ فاتورة {invoice_type}"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("نجح", f"تم حفظ الفاتورة في: {filename}")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في حفظ الفاتورة: {str(e)}")
    
    def export_to_excel(self, data, filename_prefix="report"):
        """تصدير البيانات إلى Excel"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="تصدير البيانات",
                initialvalue=f"{filename_prefix}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
            )
            
            if filename:
                with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                    if data:
                        writer = csv.writer(csvfile)
                        # كتابة العناوين
                        if isinstance(data[0], dict):
                            writer.writerow(data[0].keys())
                            for row in data:
                                writer.writerow(row.values())
                        else:
                            for row in data:
                                writer.writerow(row)
                
                messagebox.showinfo("نجح", f"تم تصدير البيانات إلى: {filename}")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في تصدير البيانات: {str(e)}")
    
    def backup_database(self, db_path):
        """نسخ احتياطي لقاعدة البيانات"""
        try:
            backup_filename = filedialog.asksaveasfilename(
                defaultextension=".db",
                filetypes=[("Database files", "*.db"), ("All files", "*.*")],
                title="حفظ نسخة احتياطية",
                initialvalue=f"backup_{datetime.now().strftime('%Y%m%d_%H%M')}.db"
            )
            
            if backup_filename:
                import shutil
                shutil.copy2(db_path, backup_filename)
                messagebox.showinfo("نجح", f"تم إنشاء نسخة احتياطية: {backup_filename}")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"فشل في إنشاء النسخة الاحتياطية: {str(e)}")

class ReportGenerator:
    def __init__(self, db):
        self.db = db
    
    def generate_detailed_sales_report(self, from_date, to_date):
        """تقرير مبيعات مفصل"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    s.id as invoice_id,
                    DATE(s.created_at) as date,
                    COALESCE(c.name, 'عميل عادي') as customer,
                    p.name as product,
                    si.quantity,
                    si.unit_price,
                    si.total_price,
                    s.payment_method,
                    u.full_name as cashier
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                LEFT JOIN sale_items si ON s.id = si.sale_id
                LEFT JOIN products p ON si.product_id = p.id
                LEFT JOIN users u ON s.created_by = u.id
                WHERE DATE(s.created_at) BETWEEN ? AND ?
                ORDER BY s.created_at DESC, s.id
            ''', (from_date, to_date))
            
            return cursor.fetchall()
            
        finally:
            conn.close()
    
    def generate_inventory_valuation_report(self):
        """تقرير تقييم المخزون"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    p.name,
                    p.current_stock,
                    p.purchase_price,
                    p.selling_price,
                    (p.current_stock * p.purchase_price) as cost_value,
                    (p.current_stock * p.selling_price) as selling_value,
                    ((p.current_stock * p.selling_price) - (p.current_stock * p.purchase_price)) as potential_profit
                FROM products p
                WHERE p.current_stock > 0
                ORDER BY cost_value DESC
            ''')
            
            return cursor.fetchall()
            
        finally:
            conn.close()
    
    def generate_top_products_report(self, from_date, to_date, limit=10):
        """تقرير أفضل المنتجات مبيعاً"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    p.name,
                    SUM(si.quantity) as total_sold,
                    SUM(si.total_price) as total_revenue,
                    AVG(si.unit_price) as avg_price,
                    COUNT(DISTINCT s.id) as num_transactions
                FROM products p
                JOIN sale_items si ON p.id = si.product_id
                JOIN sales s ON si.sale_id = s.id
                WHERE DATE(s.created_at) BETWEEN ? AND ?
                GROUP BY p.id, p.name
                ORDER BY total_sold DESC
                LIMIT ?
            ''', (from_date, to_date, limit))
            
            return cursor.fetchall()
            
        finally:
            conn.close()
    
    def generate_customer_analysis_report(self, from_date, to_date):
        """تقرير تحليل العملاء"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT 
                    COALESCE(c.name, 'عميل عادي') as customer,
                    COUNT(s.id) as num_purchases,
                    SUM(s.final_amount) as total_spent,
                    AVG(s.final_amount) as avg_purchase,
                    MAX(DATE(s.created_at)) as last_purchase
                FROM sales s
                LEFT JOIN customers c ON s.customer_id = c.id
                WHERE DATE(s.created_at) BETWEEN ? AND ?
                GROUP BY s.customer_id, c.name
                ORDER BY total_spent DESC
            ''', (from_date, to_date))
            
            return cursor.fetchall()
            
        finally:
            conn.close()