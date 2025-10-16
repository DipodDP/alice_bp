## Blood Pressure Monitoring Integration

This bot includes integration with a Django API for blood pressure measurements. The bot uses a dialog-based interface where users can:

- Click "Получить отчет" (Get Report) button to access pressure measurements
- Select time intervals: "За неделю" (Last week), "За прошлую неделю" (Previous week), or "За месяц" (Last month)
- View detailed statistics including average pressure and pulse
- Browse through individual measurements with dates and times

### Dialog Flow

1. **Main Menu**: Users see a "Получить отчет" button
2. **Interval Selection**: Users choose the time period for the report
3. **Results Display**: Shows statistics and individual measurements for the selected period

### Django API Configuration

To use the blood pressure functionality, configure the Django API connection in your `.env` file:

```env
# Django API Configuration
DJANGO_API_BASE_URL=http://localhost:8000
DJANGO_API_TOKEN=your_api_token_here
```

The bot expects the Django API to have the following endpoint structure:
- `GET /measurements/` - Returns blood pressure measurements
- Query parameters: `user_id`, `created_at__gte`, `created_at__lte`, `ordering`
