"""
Analytics engine for engagement, performance, and recommendations.
Tracks post metrics, generates insights, and suggests improvements.
"""
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.logger import get_logger

logger = get_logger(__name__)

class AnalyticsEngine:
    """Analyze engagement and performance, generate insights"""
    def __init__(self, supabase):
        self.supabase = supabase
        self.metrics_file = "analytics_metrics.json"

    def fetch_post_metrics(self, days: int = 30) -> pd.DataFrame:
        """Fetch post metrics from Supabase for the last N days"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        posts = self.supabase.table("posting_history").select(
            "id,created_at,likes,comments,reach,success,caption,template,image_path"
        ).gte("created_at", cutoff).execute().data
        if not posts:
            logger.warning("No post metrics found.")
            return pd.DataFrame()
        return pd.DataFrame(posts)

    def compute_engagement_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute aggregate engagement statistics"""
        if df.empty:
            return {"message": "No data"}
        stats = {
            "total_posts": len(df),
            "avg_likes": df["likes"].mean() if "likes" in df else 0,
            "avg_comments": df["comments"].mean() if "comments" in df else 0,
            "avg_reach": df["reach"].mean() if "reach" in df else 0,
            "success_rate": df["success"].mean() * 100 if "success" in df else 0,
        }
        return stats

    def top_performing_posts(self, df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
        """Return top N posts by engagement (likes + comments + reach)"""
        if df.empty:
            return df
        df["engagement"] = (
            df.get("likes", 0) + df.get("comments", 0) + df.get("reach", 0)
        )
        return df.sort_values("engagement", ascending=False).head(n)

    def template_performance(self, df: pd.DataFrame) -> pd.DataFrame:
        """Analyze performance by template type"""
        if df.empty or "template" not in df:
            return pd.DataFrame()
        return (
            df.groupby("template")[["likes", "comments", "reach"]]
            .mean()
            .sort_values("reach", ascending=False)
        )

    def generate_insights(self, df: pd.DataFrame) -> List[str]:
        """Generate actionable insights and recommendations"""
        insights = []
        if df.empty:
            return ["No data available for insights."]
        # Example: Best posting time
        if "created_at" in df:
            df["hour"] = pd.to_datetime(df["created_at"]).dt.hour
            best_hour = (
                df.groupby("hour")["likes"].mean().idxmax()
                if not df["likes"].isnull().all() else None
            )
            if best_hour is not None:
                insights.append(f"Best posting hour: {best_hour}:00")
        # Example: Best template
        if "template" in df:
            best_template = (
                df.groupby("template")["reach"].mean().idxmax()
                if not df["reach"].isnull().all() else None
            )
            if best_template:
                insights.append(f"Top-performing template: {best_template}")
        # Example: Success rate
        if "success" in df:
            success_rate = df["success"].mean() * 100
            if success_rate < 90:
                insights.append(f"Success rate is low ({success_rate:.1f}%). Investigate failures.")
        return insights

    def save_metrics(self, stats: Dict[str, Any]):
        """Save analytics metrics to file"""
        import json
        try:
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file, "r") as f:
                    metrics = json.load(f)
            else:
                metrics = []
            metrics.append({"timestamp": datetime.now().isoformat(), **stats})
            metrics = metrics[-1000:]
            with open(self.metrics_file, "w") as f:
                json.dump(metrics, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save analytics metrics: {e}")

    def run_full_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Run full analytics pipeline and return summary"""
        df = self.fetch_post_metrics(days=days)
        stats = self.compute_engagement_stats(df)
        top_posts = self.top_performing_posts(df)
        template_stats = self.template_performance(df)
        insights = self.generate_insights(df)
        summary = {
            "stats": stats,
            "top_posts": top_posts.to_dict(orient="records") if not top_posts.empty else [],
            "template_stats": template_stats.to_dict() if not template_stats.empty else {},
            "insights": insights,
        }
        self.save_metrics(stats)
        return summary

if __name__ == "__main__":
    from app.config import SUPABASE_URL, SUPABASE_KEY
    from supabase import create_client
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    engine = AnalyticsEngine(supabase)
    summary = engine.run_full_analytics(days=30)
    print("\nANALYTICS SUMMARY:")
    print(summary)
