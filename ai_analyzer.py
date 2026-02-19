"""
AI Analyzer for Hotel Management Bot
Uses OpenAI API for intelligent analysis and reporting
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Check if OpenAI is available
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI library not installed. AI features will be disabled.")


def get_openai_key() -> Optional[str]:
    """
    Retrieve OpenAI API key from encrypted storage
    Falls back to environment variable for backward compatibility
    
    Returns:
        API key string or None
    
    Security: API key is never logged or exposed
    """
    try:
        from security_manager import SecurityManager
        
        # Get database config from environment
        db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'name': os.getenv('DB_NAME', 'hotel_manage'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres')
        }
        
        security = SecurityManager(db_config, ensure_table=False)
        api_key = security.get_secret('openai_api_key')
        security.close()
        
        if api_key:
            return api_key
    except Exception as e:
        # Silent fail - will try environment variable fallback
        pass
    
    # Fallback to environment variable
    return os.getenv('OPENAI_API_KEY', '')


def is_ai_enabled() -> bool:
    """Check if AI/OpenAI is properly configured"""
    if not OPENAI_AVAILABLE:
        return False
    api_key = get_openai_key()
    return bool(api_key and len(api_key) > 10)


class DailyBriefGenerator:
    """Generates AI-powered daily briefings and reports"""
    
    def __init__(self):
        """Initialize the generator with OpenAI client"""
        self.client = None
        if OPENAI_AVAILABLE and is_ai_enabled():
            api_key = get_openai_key()
            if api_key:
                self.client = AsyncOpenAI(api_key=api_key)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    async def generate_daily_brief(self, db, hotel_id: int = 1, lang: str = 'en') -> Optional[str]:
        """
        Generate a comprehensive daily briefing
        
        Args:
            db: Database manager instance
            hotel_id: Hotel ID
            lang: Language code
            
        Returns:
            Generated brief text or None if failed
        """
        if not self.client:
            return None
        
        try:
            # Gather data for analysis
            data = await self._gather_daily_data(db, hotel_id)
            
            lang_instruction = "Respond in Serbian." if lang == 'sr' else "Respond in English."
            
            prompt = f"""You are a hotel operations analyst. Generate a concise daily briefing based on this data:

{json.dumps(data, indent=2, default=str)}

{lang_instruction}

Include:
1. 📊 Key metrics summary (tasks completed, pending, overdue)
2. 🏆 Top performers today
3. ⚠️ Issues requiring attention
4. 💡 Recommendations

Keep it brief and actionable. Use emojis for visual clarity."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating daily brief: {e}")
            return None
    
    async def generate_anomaly_report(self, db, hotel_id: int = 1, lang: str = 'en') -> Optional[str]:
        """
        Generate anomaly detection report
        
        Args:
            db: Database manager instance
            hotel_id: Hotel ID
            lang: Language code
            
        Returns:
            Generated report text or None if failed
        """
        if not self.client:
            return None
        
        try:
            data = await self._gather_anomaly_data(db, hotel_id)
            
            lang_instruction = "Respond in Serbian." if lang == 'sr' else "Respond in English."
            
            prompt = f"""You are a hotel operations analyst specializing in anomaly detection. Analyze this data for unusual patterns:

{json.dumps(data, indent=2, default=str)}

{lang_instruction}

Identify:
1. 🔴 Critical anomalies (immediate attention needed)
2. 🟡 Warning signs (potential issues)
3. 🟢 Positive deviations (above-average performance)
4. 📈 Trends to watch

Be specific about what's unusual and why. Provide actionable insights."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating anomaly report: {e}")
            return None
    
    async def generate_department_report(self, db, department: str, hotel_id: int = 1, lang: str = 'en') -> Optional[str]:
        """
        Generate department-specific performance report
        
        Args:
            db: Database manager instance
            department: Department name
            hotel_id: Hotel ID
            lang: Language code
            
        Returns:
            Generated report text or None if failed
        """
        if not self.client:
            return None
        
        try:
            data = await self._gather_department_data(db, department, hotel_id)
            
            lang_instruction = "Respond in Serbian." if lang == 'sr' else "Respond in English."
            
            prompt = f"""You are a hotel department analyst. Generate a performance report for the {department} department:

{json.dumps(data, indent=2, default=str)}

{lang_instruction}

Include:
1. 📊 Department overview
2. 👥 Staff performance summary
3. ✅ Completed tasks analysis
4. ⏰ Pending/overdue tasks
5. 💡 Improvement recommendations

Be concise and focus on actionable insights."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating department report: {e}")
            return None
    
    async def generate_performance_ranking(self, db, hotel_id: int = 1, lang: str = 'en') -> Optional[str]:
        """
        Generate employee performance ranking
        
        Args:
            db: Database manager instance
            hotel_id: Hotel ID
            lang: Language code
            
        Returns:
            Generated ranking text or None if failed
        """
        if not self.client:
            return None
        
        try:
            data = await self._gather_performance_data(db, hotel_id)
            
            lang_instruction = "Respond in Serbian." if lang == 'sr' else "Respond in English."
            
            prompt = f"""You are a hotel HR analyst. Generate a fair performance ranking based on this data:

{json.dumps(data, indent=2, default=str)}

{lang_instruction}

Create:
1. 🏆 Top performers (with specific achievements)
2. 📊 Performance metrics breakdown
3. 📈 Improvement trends
4. 💪 Recognition recommendations

Be objective and focus on measurable achievements."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating performance ranking: {e}")
            return None
    
    async def generate_department_comparison(self, db, hotel_id: int = 1, lang: str = 'en') -> Optional[str]:
        """
        Generate department comparison report
        
        Args:
            db: Database manager instance
            hotel_id: Hotel ID
            lang: Language code
            
        Returns:
            Generated comparison text or None if failed
        """
        if not self.client:
            return None
        
        try:
            data = await self._gather_comparison_data(db, hotel_id)
            
            lang_instruction = "Respond in Serbian." if lang == 'sr' else "Respond in English."
            
            prompt = f"""You are a hotel operations analyst. Compare department performance:

{json.dumps(data, indent=2, default=str)}

{lang_instruction}

Provide:
1. 📊 Department rankings by efficiency
2. ⚖️ Workload distribution analysis
3. 🔄 Cross-department collaboration insights
4. 💡 Resource optimization suggestions

Use data to support your analysis."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating department comparison: {e}")
            return None
    
    async def _gather_daily_data(self, db, hotel_id: int) -> Dict[str, Any]:
        """Gather data for daily brief"""
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        data = {
            'date': today,
            'tasks': {},
            'employees': {},
            'departments': []
        }
        
        try:
            # Get task statistics
            db.cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_perform = 1 THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN is_perform = 0 AND due_date < %s THEN 1 ELSE 0 END) as overdue
                FROM tbl_tasks WHERE Date >= %s
            """, (today, yesterday))
            task_stats = db.cursor.fetchone()
            if task_stats:
                data['tasks'] = dict(task_stats)
            
            # Get department list
            db.cursor.execute("SELECT DISTINCT department FROM tbl_employeer WHERE department IS NOT NULL")
            departments = db.cursor.fetchall()
            data['departments'] = [d['department'] for d in departments]
            
            # Get top performers (most tasks completed today)
            db.cursor.execute("""
                SELECT assignee_name, COUNT(*) as completed_count
                FROM tbl_tasks 
                WHERE is_perform = 1 AND DATE(task_completed_at) = %s
                GROUP BY assignee_name
                ORDER BY completed_count DESC
                LIMIT 5
            """, (today,))
            top_performers = db.cursor.fetchall()
            data['top_performers'] = [dict(p) for p in top_performers]
            
        except Exception as e:
            print(f"Error gathering daily data: {e}")
        
        return data
    
    async def _gather_anomaly_data(self, db, hotel_id: int) -> Dict[str, Any]:
        """Gather data for anomaly detection"""
        today = datetime.now().strftime('%Y-%m-%d')
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        data = {
            'period': f"{week_ago} to {today}",
            'daily_task_counts': [],
            'overdue_tasks': [],
            'unusual_patterns': []
        }
        
        try:
            # Get daily task completion counts for the past week
            db.cursor.execute("""
                SELECT DATE(task_completed_at) as date, COUNT(*) as count
                FROM tbl_tasks 
                WHERE task_completed_at >= %s
                GROUP BY DATE(task_completed_at)
                ORDER BY date
            """, (week_ago,))
            daily_counts = db.cursor.fetchall()
            data['daily_task_counts'] = [dict(d) for d in daily_counts]
            
            # Get overdue tasks
            db.cursor.execute("""
                SELECT id, description, assignee_name, due_date, department
                FROM tbl_tasks 
                WHERE is_perform = 0 AND due_date < %s
                ORDER BY due_date
                LIMIT 10
            """, (today,))
            overdue = db.cursor.fetchall()
            data['overdue_tasks'] = [dict(o) for o in overdue]
            
        except Exception as e:
            print(f"Error gathering anomaly data: {e}")
        
        return data
    
    async def _gather_department_data(self, db, department: str, hotel_id: int) -> Dict[str, Any]:
        """Gather department-specific data"""
        today = datetime.now().strftime('%Y-%m-%d')
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        data = {
            'department': department,
            'period': f"{week_ago} to {today}",
            'employees': [],
            'tasks': {}
        }
        
        try:
            # Get department employees
            db.cursor.execute("""
                SELECT employee_id, name, work_role FROM tbl_employeer WHERE department = %s
            """, (department,))
            employees = db.cursor.fetchall()
            data['employees'] = [dict(e) for e in employees]
            
            # Get department task statistics
            db.cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_perform = 1 THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN is_perform = 0 THEN 1 ELSE 0 END) as pending
                FROM tbl_tasks 
                WHERE department = %s AND Date >= %s
            """, (department, week_ago))
            task_stats = db.cursor.fetchone()
            if task_stats:
                data['tasks'] = dict(task_stats)
            
        except Exception as e:
            print(f"Error gathering department data: {e}")
        
        return data
    
    async def _gather_performance_data(self, db, hotel_id: int) -> Dict[str, Any]:
        """Gather employee performance data"""
        today = datetime.now().strftime('%Y-%m-%d')
        month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        data = {
            'period': f"{month_ago} to {today}",
            'employee_stats': []
        }
        
        try:
            # Get employee performance statistics
            db.cursor.execute("""
                SELECT 
                    e.name,
                    e.department,
                    COUNT(t.id) as total_tasks,
                    SUM(CASE WHEN t.is_perform = 1 THEN 1 ELSE 0 END) as completed_tasks
                FROM tbl_employeer e
                LEFT JOIN tbl_tasks t ON e.name = t.assignee_name AND t.Date >= %s
                WHERE e.department != 'Management'
                GROUP BY e.employee_id, e.name, e.department
                ORDER BY completed_tasks DESC
            """, (month_ago,))
            stats = db.cursor.fetchall()
            data['employee_stats'] = [dict(s) for s in stats]
            
        except Exception as e:
            print(f"Error gathering performance data: {e}")
        
        return data
    
    async def _gather_comparison_data(self, db, hotel_id: int) -> Dict[str, Any]:
        """Gather department comparison data"""
        today = datetime.now().strftime('%Y-%m-%d')
        month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        data = {
            'period': f"{month_ago} to {today}",
            'departments': []
        }
        
        try:
            # Get department statistics
            db.cursor.execute("""
                SELECT 
                    department,
                    COUNT(*) as total_tasks,
                    SUM(CASE WHEN is_perform = 1 THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN is_perform = 0 AND due_date < %s THEN 1 ELSE 0 END) as overdue
                FROM tbl_tasks 
                WHERE Date >= %s AND department IS NOT NULL
                GROUP BY department
                ORDER BY department
            """, (today, month_ago))
            dept_stats = db.cursor.fetchall()
            data['departments'] = [dict(d) for d in dept_stats]
            
            # Get employee count per department
            db.cursor.execute("""
                SELECT department, COUNT(*) as employee_count
                FROM tbl_employeer
                WHERE department IS NOT NULL
                GROUP BY department
            """)
            emp_counts = db.cursor.fetchall()
            emp_count_map = {e['department']: e['employee_count'] for e in emp_counts}
            
            for dept in data['departments']:
                dept['employee_count'] = emp_count_map.get(dept['department'], 0)
            
        except Exception as e:
            print(f"Error gathering comparison data: {e}")
        
        return data
