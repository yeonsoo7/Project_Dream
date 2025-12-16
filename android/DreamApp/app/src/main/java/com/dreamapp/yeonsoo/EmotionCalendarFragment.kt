package com.dreamapp.yeonsoo

import android.os.Bundle
import android.view.View
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.GridLayoutManager
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import java.time.DayOfWeek
import java.time.YearMonth

class EmotionCalendarFragment : Fragment(R.layout.fragment_emotion_calendar) {

    private lateinit var calendarAdapter: CalendarDayAdapter
    private lateinit var dayDreamAdapter: DreamDetailAdapter

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        val rvCalendar = view.findViewById<RecyclerView>(R.id.rvCalendar)
        val rvDayDreams = view.findViewById<RecyclerView>(R.id.rvDayDreams)

        calendarAdapter = CalendarDayAdapter(emptyList()) { day ->
            // 날짜 칸 클릭 시 호출
            if (day.label != "empty") {
                showMockDreamsForDate(day.date)
            }
        }
        dayDreamAdapter = DreamDetailAdapter(emptyList())

        rvCalendar.adapter = calendarAdapter
        rvDayDreams.adapter = dayDreamAdapter

        rvCalendar.layoutManager = GridLayoutManager(requireContext(), 7)
        rvDayDreams.layoutManager = LinearLayoutManager(requireContext())

        // ▼▼▼ 11월 달력 데이터 만들기 ▼▼▼
        val year = 2025
        val month = 11
        val ym = YearMonth.of(year, month)
        val daysInMonth = ym.lengthOfMonth()

        // 자바 시간 기준: MONDAY=1 ... SUNDAY=7
        val firstDow = ym.atDay(1).dayOfWeek
        val firstIndex = when (firstDow) {
            DayOfWeek.MONDAY -> 1
            DayOfWeek.TUESDAY -> 2
            DayOfWeek.WEDNESDAY -> 3
            DayOfWeek.THURSDAY -> 4
            DayOfWeek.FRIDAY -> 5
            DayOfWeek.SATURDAY -> 6
            DayOfWeek.SUNDAY -> 0      // 일요일 시작 기준
        }

        val cells = mutableListOf<CalendarDayEmotion>()

        // 앞쪽 패딩(이전 달 빈 칸)
        repeat(firstIndex) {
            cells.add(
                CalendarDayEmotion(
                    date = "",
                    avg_positive = 0.0,
                    avg_negative = 0.0,
                    score = 0.0,
                    label = "empty",
                    dream_count = 0
                )
            )
        }

        // 11월 1~마지막 날
        val specialMap = mapOf(
            // 감정 색만 좀 다르게 주고 싶은 날짜들
            "%04d-%02d-%02d".format(year, month, 5)  to 0.2, // 빨강
            "%04d-%02d-%02d".format(year, month, 12) to 0.5, // 노랑
            "%04d-%02d-%02d".format(year, month, 20) to 0.8  // 초록
        )

        for (d in 1..daysInMonth) {
            val fullDate = "%04d-%02d-%02d".format(year, month, d)
            val score = specialMap[fullDate] ?: 0.5
            val label = when {
                score <= 0.33 -> "negative"
                score <= 0.66 -> "mixed"
                else -> "positive"
            }
            cells.add(
                CalendarDayEmotion(
                    date = fullDate,
                    avg_positive = score,
                    avg_negative = 1.0 - score,
                    score = score,
                    label = label,
                    dream_count = if (specialMap.containsKey(fullDate)) 1 else 0
                )
            )
        }

        // 마지막 줄 패딩(다음 달 빈 칸)
        val remainder = cells.size % 7
        if (remainder != 0) {
            repeat(7 - remainder) {
                cells.add(
                    CalendarDayEmotion(
                        date = "",
                        avg_positive = 0.0,
                        avg_negative = 0.0,
                        score = 0.0,
                        label = "empty",
                        dream_count = 0
                    )
                )
            }
        }

        // 그리드에 넣기
        calendarAdapter.submitList(cells)

        // 기본으로 11월 20일 꿈 보여주기 (초록색 칸)
        val defaultDate = "%04d-%02d-%02d".format(year, month, 20)
        showMockDreamsForDate(defaultDate)
    }

    private fun showMockDreamsForDate(date: String) {
        // 날짜별로 다른 목업 보여주기
        val dreams: List<DreamDetail> = when (date.takeLast(2)) {
            "05" -> listOf(
                DreamDetail(
                    id = 1,
                    date = date,
                    text = "시험을 망치는 꿈을 꿨어...",
                    emotion = "불안",
                    interpretation = "시험에 대한 압박감이 반영된 꿈일 수 있어요.",
                    images = emptyList(),
                    valence = mapOf("positive" to 0.2, "negative" to 0.8),
                    facets = emptyMap(),
                    nlg_notes = listOf("부정적인 정서와 불안이 강하게 느껴지는 꿈입니다.")
                )
            )
            "12" -> listOf(
                DreamDetail(
                    id = 2,
                    date = date,
                    text = "친구랑 크게 싸우다가 마지막엔 화해했어.",
                    emotion = "복잡",
                    interpretation = null,
                    images = emptyList(),
                    valence = mapOf("positive" to 0.5, "negative" to 0.5),
                    facets = emptyMap(),
                    nlg_notes = listOf("갈등과 회복이 함께 나타나는 복합적인 감정의 꿈입니다.")
                )
            )
            "20" -> listOf(
                DreamDetail(
                    id = 3,
                    date = date,
                    text = "바닷가에서 고래랑 같이 헤엄쳤다.",
                    emotion = "행복",
                    interpretation = "요즘 마음이 조금은 여유롭다는 신호일 수 있어요.",
                    images = emptyList(),
                    valence = mapOf("positive" to 0.8, "negative" to 0.2),
                    facets = emptyMap(),
                    nlg_notes = listOf("전반적으로 긍정적인 정서와 안정감이 느껴집니다.")
                )
            )
            else -> listOf(
                DreamDetail(
                    id = 4,
                    date = date,
                    text = "${date}의 꿈 기록 예시입니다.",
                    emotion = null,
                    interpretation = null,
                    images = emptyList(),
                    valence = mapOf("positive" to 0.5, "negative" to 0.5),
                    facets = emptyMap(),
                    nlg_notes = listOf("특별한 정서 편향이 없는 중립적인 꿈입니다.")
                )
            )
        }

        dayDreamAdapter.submitList(dreams)
    }
}
