from datetime import datetime
from collections import defaultdict
import sqlite3

class DataBase():
    def __init__(self, data_path):
        self.db_path = data_path

    def load_data(self, date_str):
        """
        用于查找指定日期的数据
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT CommonId, Name FROM Ar_CommonGroup")
        common_map = dict(cursor.fetchall())
        cursor.execute("""
            SELECT CommonGroupId, StartLocalTime, EndLocalTime
            FROM Ar_Activity
            WHERE CommonGroupId IS NOT NULL AND StartLocalTime LIKE ? AND EndLocalTime IS NOT NULL
        """, (f"{date_str}%",))
        rows = cursor.fetchall()
        conn.close()

        segments = []
        usage = defaultdict(float)

        for gid, start, end in rows:
            title = common_map.get(gid, "(unknown window)")
            t1 = datetime.fromisoformat(start)
            t2 = datetime.fromisoformat(end)
            if t2 > t1:
                segments.append((title, int(t1.timestamp() * 1000), int(t2.timestamp() * 1000)))
                usage[title] += (t2 - t1).total_seconds() / 3600
        return segments, usage
    
    def load_lock_data(self, date_str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # 精选 Ar_Group 中名称为 'Away' 和 'Session lock' 的 GroupId
        cursor.execute("SELECT GroupId, Name FROM Ar_Group WHERE Name IN ('Away', 'Session lock')")
        special_gid_map = dict(cursor.fetchall())

        # 用这些 GroupId 精确查 Ar_Activity
        if special_gid_map:
            placeholder = ",".join(["?"] * len(special_gid_map))
            cursor.execute(f"""
                SELECT GroupId, StartLocalTime, EndLocalTime
                FROM Ar_Activity
                WHERE GroupId IN ({placeholder}) AND StartLocalTime LIKE ? AND EndLocalTime IS NOT NULL
            """, list(special_gid_map.keys()) + [f"{date_str}%"])

            special_rows = cursor.fetchall()
            segments = []

            for gid, start, end in special_rows:
                name = special_gid_map.get(gid, "(special)")
                try:
                    t1 = datetime.fromisoformat(start)
                    t2 = datetime.fromisoformat(end)
                    if t2 > t1:
                        segments.append((name, int(t1.timestamp() * 1000), int(t2.timestamp() * 1000)))
                except Exception:
                    continue
        return segments
    
    def load_data_range(self, start_date_str, end_date_str):
        """
        用于查找指定日期范围内的数据
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT CommonId, Name FROM Ar_CommonGroup")
        common_map = dict(cursor.fetchall())
        cursor.execute("""
            SELECT CommonGroupId, StartLocalTime, EndLocalTime
            FROM Ar_Activity
            WHERE CommonGroupId IS NOT NULL
            AND EndLocalTime IS NOT NULL
            AND StartLocalTime BETWEEN ? AND ?
        """, (f"{start_date_str} 00:00:00", f"{end_date_str} 23:59:59"))
        rows = cursor.fetchall()
        conn.close()

        usage = defaultdict(float)

        for gid, start, end in rows:
            title = common_map.get(gid, "(unknown window)")
            t1 = datetime.fromisoformat(start)
            t2 = datetime.fromisoformat(end)
            if t2 > t1:
                usage[title] += (t2 - t1).total_seconds() / 3600
        return usage

    def get_available_dates(self):
        """
        有数据的日期列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT substr(StartLocalTime, 1, 10) AS date
            FROM Ar_Activity
            WHERE CommonGroupId IS NOT NULL AND EndLocalTime IS NOT NULL
        """)
        rows = cursor.fetchall()
        conn.close()
        return {row[0] for row in rows}