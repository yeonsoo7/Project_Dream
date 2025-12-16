package com.dreamapp.yeonsoo

data class CalendarDayEmotion(
    val date: String,          // "YYYY-MM-DD"
    val avg_positive: Double,
    val avg_negative: Double,
    val score: Double,         // 0~1, 색 결정용 (0=빨강, 1=초록)
    val label: String,         // "positive" / "negative" / "mixed" / "neutral"
    val dream_count: Int
)
