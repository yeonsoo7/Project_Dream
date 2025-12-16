package com.dreamapp.yeonsoo

import android.graphics.Color
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView

class CalendarDayAdapter(
    private var items: List<CalendarDayEmotion>,
    private val onClick: (CalendarDayEmotion) -> Unit
) : RecyclerView.Adapter<CalendarDayAdapter.DayViewHolder>() {

    class DayViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        val viewColor: View = itemView.findViewById(R.id.viewColor)
        val tvDate: TextView = itemView.findViewById(R.id.tvDate)
        val tvLabel: TextView = itemView.findViewById(R.id.tvLabel)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): DayViewHolder {
        val v = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_calendar_day, parent, false)
        return DayViewHolder(v)
    }

    override fun onBindViewHolder(holder: DayViewHolder, position: Int) {
        val item = items[position]

        // label 이 "empty" 이면 달력 패딩 칸
        if (item.label == "empty") {
            holder.tvDate.text = ""
            holder.viewColor.setBackgroundColor(Color.TRANSPARENT)
            holder.itemView.setOnClickListener(null)
            return
        }

        // "2025-11-03" -> "3"
        val dayNumber = item.date.takeLast(2).toIntOrNull() ?: (position + 1)
        holder.tvDate.text = dayNumber.toString()

        // 꿈 데이터 없는 날
        if (item.dream_count == 0) {
            // → 기본 배경색(연보라/분홍)과 맞추기
            holder.viewColor.setBackgroundColor(Color.parseColor("#F9F1F6"))
            holder.itemView.setOnClickListener {
                onClick(item)
            }
            return
        }

        // 색상: score 로 빨강~노랑~초록
        val color = when {
            item.score <= 0.33 -> Color.parseColor("#EF5350") // 부정
            item.score <= 0.66 -> Color.parseColor("#FFCA28") // 중간
            else -> Color.parseColor("#66BB6A")               // 긍정
        }
        holder.viewColor.setBackgroundColor(color)

        holder.itemView.setOnClickListener {
            onClick(item)
        }
    }

    override fun getItemCount(): Int = items.size

    fun submitList(newItems: List<CalendarDayEmotion>) {
        items = newItems
        notifyDataSetChanged()
    }
}
