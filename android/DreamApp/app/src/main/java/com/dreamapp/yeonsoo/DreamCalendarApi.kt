package com.dreamapp.yeonsoo

import retrofit2.http.GET
import retrofit2.http.Query

interface DreamCalendarApi {

    @GET("dreams/calendar")
    suspend fun getCalendar(
        @Query("user_id") userId: String,
        @Query("month") month: String  // "2025-11"
    ): List<CalendarDayEmotion>

    @GET("dreams/by-date")
    suspend fun getDreamsByDate(
        @Query("user_id") userId: String,
        @Query("date") date: String    // "2025-11-18"
    ): List<DreamDetail>
}
