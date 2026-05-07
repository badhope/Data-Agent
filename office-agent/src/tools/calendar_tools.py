"""
Office Agent Tools - Calendar Module
日程管理工具集
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from langchain_core.tools import tool
from langchain_core.pydantic_v1 import BaseModel, Field


# ==================== Tool Input Schemas ====================

class CheckCalendarInput(BaseModel):
    """查看日历输入参数"""
    date: str = Field(description="日期 (格式: YYYY-MM-DD)")
    start_time: str = Field(default="09:00", description="开始时间 (格式: HH:MM)")
    end_time: str = Field(default="18:00", description="结束时间 (格式: HH:MM)")


class ScheduleMeetingInput(BaseModel):
    """安排会议输入参数"""
    title: str = Field(description="会议标题")
    date: str = Field(description="日期 (格式: YYYY-MM-DD)")
    time: str = Field(description="时间 (格式: HH:MM)")
    duration_minutes: int = Field(default=60, description="会议时长（分钟）")
    participants: List[str] = Field(description="参会人员邮箱列表")
    location: Optional[str] = Field(default=None, description="会议地点")
    description: Optional[str] = Field(default=None, description="会议描述")


class UpdateMeetingInput(BaseModel):
    """更新会议输入参数"""
    meeting_id: str = Field(description="会议ID")
    title: Optional[str] = Field(default=None, description="新标题")
    date: Optional[str] = Field(default=None, description="新日期")
    time: Optional[str] = Field(default=None, description="新时间")
    duration_minutes: Optional[int] = Field(default=None, description="新时长")
    location: Optional[str] = Field(default=None, description="新地点")


class FindAvailableTimeInput(BaseModel):
    """查找空闲时间输入参数"""
    date: str = Field(description="日期 (格式: YYYY-MM-DD)")
    duration_minutes: int = Field(description="需要时长（分钟）")
    participants: List[str] = Field(description="参会人员列表")


class CancelMeetingInput(BaseModel):
    """取消会议输入参数"""
    meeting_id: str = Field(description="会议ID")
    reason: Optional[str] = Field(default=None, description="取消原因")


# ==================== Mock Calendar Data Store ====================

class MockCalendarStore:
    """模拟日历数据存储（实际项目中应连接真实日历服务）"""
    
    def __init__(self):
        self.meetings = [
            {
                "id": "meet_001",
                "title": "产品评审会议",
                "date": "2025-01-15",
                "time": "10:00",
                "duration": 60,
                "participants": ["zhangsan@company.com", "lisi@company.com"],
                "location": "3号会议室",
                "description": "Q1产品规划评审",
                "status": "confirmed",
                "organizer": "assistant@company.com"
            },
            {
                "id": "meet_002",
                "title": "团队周会",
                "date": "2025-01-15",
                "time": "14:00",
                "duration": 45,
                "participants": ["team@company.com"],
                "location": "线上会议",
                "description": "每周例会",
                "status": "confirmed",
                "organizer": "assistant@company.com"
            },
            {
                "id": "meet_003",
                "title": "一对一谈话",
                "date": "2025-01-16",
                "time": "09:00",
                "duration": 30,
                "participants": ["wangwu@company.com"],
                "location": "经理办公室",
                "description": "绩效反馈",
                "status": "confirmed",
                "organizer": "assistant@company.com"
            }
        ]
        self.next_id = 4
    
    def get_meetings(self, date: str) -> List[Dict]:
        return [m for m in self.meetings if m["date"] == date]
    
    def get_meeting(self, meeting_id: str) -> Optional[Dict]:
        for m in self.meetings:
            if m["id"] == meeting_id:
                return m
        return None
    
    def create_meeting(self, data: Dict) -> Dict:
        meeting = {
            "id": f"meet_{self.next_id:03d}",
            "status": "confirmed",
            "organizer": "assistant@company.com",
            **data
        }
        self.meetings.append(meeting)
        self.next_id += 1
        return meeting
    
    def update_meeting(self, meeting_id: str, updates: Dict) -> Optional[Dict]:
        for m in self.meetings:
            if m["id"] == meeting_id:
                m.update(updates)
                return m
        return None
    
    def delete_meeting(self, meeting_id: str) -> bool:
        for i, m in enumerate(self.meetings):
            if m["id"] == meeting_id:
                self.meetings.pop(i)
                return True
        return False
    
    def check_availability(self, date: str, time: str, duration: int, 
                          exclude_id: Optional[str] = None) -> bool:
        """检查时间是否可用"""
        start_minutes = self._time_to_minutes(time)
        end_minutes = start_minutes + duration
        
        for m in self.meetings:
            if m["date"] != date or m["id"] == exclude_id:
                continue
            if m["status"] == "cancelled":
                continue
            
            m_start = self._time_to_minutes(m["time"])
            m_end = m_start + m["duration"]
            
            # 检查时间冲突
            if not (end_minutes <= m_start or start_minutes >= m_end):
                return False
        return True
    
    def find_available_slots(self, date: str, duration: int, 
                            work_start: str = "09:00",
                            work_end: str = "18:00") -> List[Dict]:
        """查找可用时间段"""
        available = []
        start_minutes = self._time_to_minutes(work_start)
        end_minutes = self._time_to_minutes(work_end)
        
        # 获取当天的会议
        day_meetings = sorted(
            [m for m in self.meetings if m["date"] == date and m["status"] != "cancelled"],
            key=lambda x: self._time_to_minutes(x["time"])
        )
        
        current = start_minutes
        for m in day_meetings:
            m_start = self._time_to_minutes(m["time"])
            m_end = m_start + m["duration"]
            
            # 检查开始到会议开始之间是否有足够时间
            if current + duration <= m_start:
                available.append({
                    "start": self._minutes_to_time(current),
                    "end": self._minutes_to_time(m_start)
                })
            
            current = max(current, m_end)
        
        # 检查最后一个会议后到下班时间
        if current + duration <= end_minutes:
            available.append({
                "start": self._minutes_to_time(current),
                "end": self._minutes_to_time(end_minutes)
            })
        
        return available
    
    @staticmethod
    def _time_to_minutes(time: str) -> int:
        h, m = map(int, time.split(":"))
        return h * 60 + m
    
    @staticmethod
    def _minutes_to_time(minutes: int) -> str:
        h = minutes // 60
        m = minutes % 60
        return f"{h:02d}:{m:02d}"


# 全局日历存储实例
_calendar_store = MockCalendarStore()


# ==================== Calendar Tools ====================

@tool(args_schema=CheckCalendarInput, return_direct=False)
def check_calendar(
    date: str,
    start_time: str = "09:00",
    end_time: str = "18:00"
) -> str:
    """
    查看指定日期的日历安排。
    
    当用户想了解某一天的日程安排时使用此工具。
    
    Args:
        date: 日期，格式 YYYY-MM-DD
        start_time: 查询开始时间，默认 09:00
        end_time: 查询结束时间，默认 18:00
    
    Returns:
        日程安排详情
    """
    try:
        meetings = _calendar_store.get_meetings(date)
        
        if not meetings:
            return f"""📅 {date} 日程

当前没有安排的会议，您可以自由安排时间。"""
        
        # 按时间排序
        meetings = sorted(meetings, key=lambda x: x["time"])
        
        output = f"📅 {date} 日程\n"
        output += "=" * 40 + "\n\n"
        
        for m in meetings:
            start = m["time"]
            end_h, end_m = map(int, start.split(":"))
            end_h += m["duration"] // 60
            end_m += m["duration"] % 60
            if end_m >= 60:
                end_h += 1
                end_m -= 60
            end = f"{end_h:02d}:{end_m:02d}"
            
            output += f"""🕐 {start} - {end} ({m['duration']}分钟)
   📌 {m['title']}
   📍 {m['location']}
   👥 {', '.join(m['participants'])}
   
"""
        
        return output.strip()
        
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


@tool(args_schema=ScheduleMeetingInput, return_direct=True)
def schedule_meeting(
    title: str,
    date: str,
    time: str,
    duration_minutes: int,
    participants: List[str],
    location: Optional[str] = None,
    description: Optional[str] = None
) -> str:
    """
    安排新的会议。
    
    当用户需要创建会议、预约时间、发起讨论时使用此工具。
    
    Args:
        title: 会议标题
        date: 会议日期，格式 YYYY-MM-DD
        time: 会议时间，格式 HH:MM
        duration_minutes: 会议时长（分钟）
        participants: 参会人员邮箱列表
        location: 会议地点（可选，默认线上会议）
        description: 会议描述（可选）
    
    Returns:
        创建结果
    """
    try:
        # 检查时间是否可用
        if not _calendar_store.check_availability(date, time, duration_minutes):
            # 获取冲突的会议
            existing = _calendar_store.get_meetings(date)
            conflicts = []
            for m in existing:
                m_start = _calendar_store._time_to_minutes(m["time"])
                m_end = m_start + m["duration"]
                req_start = _calendar_store._time_to_minutes(time)
                req_end = req_start + duration_minutes
                if not (req_end <= m_start or req_start >= m_end):
                    conflicts.append(m)
            
            if conflicts:
                conflict = conflicts[0]
                return f"""⚠️ 时间冲突！

与现有会议冲突：
📌 {conflict['title']}
🕐 {conflict['time']} - ({conflict['duration']}分钟)

请选择其他时间。"""
        
        # 创建会议
        meeting = _calendar_store.create_meeting({
            "title": title,
            "date": date,
            "time": time,
            "duration": duration_minutes,
            "participants": participants,
            "location": location or "线上会议",
            "description": description or ""
        })
        
        end_h, end_m = map(int, time.split(":"))
        end_h += duration_minutes // 60
        end_m += duration_minutes % 60
        if end_m >= 60:
            end_h += 1
            end_m -= 60
        end_time = f"{end_h:02d}:{end_m:02d}"
        
        result = f"""✅ 会议已创建！

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 标题: {title}
📅 日期: {date}
🕐 时间: {time} - {end_time} ({duration_minutes}分钟)
👥 参会人: {', '.join(participants)}
📍 地点: {location or '线上会议'}
"""
        if description:
            result += f"📝 描述: {description}\n"
        
        result += f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🆔 会议ID: {meeting['id']}
"""
        
        return result
        
    except Exception as e:
        return f"❌ 创建会议失败: {str(e)}"


@tool(args_schema=CancelMeetingInput, return_direct=True)
def cancel_meeting(meeting_id: str, reason: Optional[str] = None) -> str:
    """
    取消会议。
    
    当用户需要取消已安排的会议时使用此工具。
    
    Args:
        meeting_id: 会议ID
        reason: 取消原因（可选）
    
    Returns:
        取消结果
    """
    try:
        meeting = _calendar_store.get_meeting(meeting_id)
        
        if not meeting:
            return f"❌ 未找到会议: {meeting_id}"
        
        _calendar_store.update_meeting(meeting_id, {"status": "cancelled"})
        
        result = f"""✅ 会议已取消

📌 {meeting['title']}
📅 {meeting['date']} {meeting['time']}
"""
        if reason:
            result += f"\n📝 取消原因: {reason}"
        
        return result
        
    except Exception as e:
        return f"❌ 取消会议失败: {str(e)}"


@tool(args_schema=FindAvailableTimeInput, return_direct=False)
def find_available_time(
    date: str,
    duration_minutes: int,
    participants: List[str]
) -> str:
    """
    查找所有参会人都空闲的时间段。
    
    当用户需要安排会议但不确定何时有空时使用此工具。
    
    Args:
        date: 日期，格式 YYYY-MM-DD
        duration_minutes: 需要的时间长度（分钟）
        participants: 参会人员列表
    
    Returns:
        可用时间段列表
    """
    try:
        available = _calendar_store.find_available_slots(date, duration_minutes)
        
        if not available:
            return f"""😔 {date} 全天繁忙

在 {duration_minutes} 分钟的时间段内没有找到可用时间。
建议：
1. 尝试其他日期
2. 缩短会议时长
3. 只邀请必要人员"""
        
        output = f"""📅 {date} 可用时间段

查找条件：时长 ≥ {duration_minutes} 分钟
参会人: {', '.join(participants)}

"""
        
        for i, slot in enumerate(available, 1):
            start_h, start_m = map(int, slot["start"].split(":"))
            end_h, end_m = map(int, slot["end"].split(":"))
            slot_duration = (end_h * 60 + end_m) - (start_h * 60 + start_m)
            
            output += f"{i}. 🕐 {slot['start']} - {slot['end']}"
            if slot_duration > duration_minutes:
                output += f" (可用 {slot_duration} 分钟)"
            output += "\n"
        
        return output.strip()
        
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


@tool(return_direct=False)
def list_upcoming_meetings(days: int = 7) -> str:
    """
    列出近期即将到来的会议。
    
    当用户想了解接下来几天的会议安排时使用此工具。
    
    Args:
        days: 查看多少天内的会议，默认7天
    
    Returns:
        近期会议列表
    """
    try:
        today = datetime.now()
        upcoming = []
        
        for i in range(days):
            date = (today + timedelta(days=i)).strftime("%Y-%m-%d")
            meetings = _calendar_store.get_meetings(date)
            for m in meetings:
                if m["status"] != "cancelled":
                    upcoming.append(m)
        
        if not upcoming:
            return f"📅 未来 {days} 天内没有安排的会议。"
        
        # 按日期和时间排序
        upcoming = sorted(upcoming, key=lambda x: (x["date"], x["time"]))
        
        output = f"📅 近期会议预告（未来 {days} 天）\n"
        output += "=" * 40 + "\n\n"
        
        current_date = None
        for m in upcoming:
            if m["date"] != current_date:
                current_date = m["date"]
                weekday = datetime.strptime(current_date, "%Y-%m-%d").strftime("%A")
                output += f"📆 {current_date} ({weekday})\n"
            
            output += f"   🕐 {m['time']} - {m['title']}\n"
        
        return output.strip()
        
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"


# ==================== Tool Exports ====================

CALENDAR_TOOLS = [
    check_calendar,
    schedule_meeting,
    cancel_meeting,
    find_available_time,
    list_upcoming_meetings
]

__all__ = [
    "check_calendar",
    "schedule_meeting",
    "cancel_meeting",
    "find_available_time",
    "list_upcoming_meetings",
    "CALENDAR_TOOLS"
]
