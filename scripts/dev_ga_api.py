from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)
from google.oauth2 import service_account
import os

# 서비스 계정 인증
credentials = service_account.Credentials.from_service_account_file(
    "path/to/your/service-account-key.json"
)

# GA4 클라이언트 초기화
client = BetaAnalyticsDataClient(credentials=credentials)


def get_analytics_data(property_id, start_date="30daysAgo", end_date="today"):
    """GA4에서 기본 분석 데이터 수집"""

    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name="pagePath"),
            Dimension(name="pageTitle"),
        ],
        metrics=[
            Metric(name="screenPageViews"),
            Metric(name="averageSessionDuration"),
            Metric(name="bounceRate"),
        ],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
    )

    response = client.run_report(request=request)

    # 데이터 처리
    results = []
    for row in response.rows:
        page_path = row.dimension_values[0].value
        page_title = row.dimension_values[1].value
        page_views = row.metric_values[0].value
        avg_duration = row.metric_values[1].value
        bounce_rate = row.metric_values[2].value

        results.append(
            {
                "page_path": page_path,
                "page_title": page_title,
                "page_views": int(page_views),
                "avg_duration": float(avg_duration),
                "bounce_rate": float(bounce_rate),
            }
        )

    return results


# 사용 예시
if __name__ == "__main__":
    PROPERTY_ID = "YOUR_GA4_PROPERTY_ID"  # GA4 속성 ID
    data = get_analytics_data(PROPERTY_ID)
    print(f"수집된 페이지 수: {len(data)}")
